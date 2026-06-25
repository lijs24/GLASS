# Memory Model

GLASS must not load all input frames into CPU RAM or GPU VRAM by default.
Metadata stages read only headers. Pixel stages use an explicit memory plan:
full-frame resident, batched resident, slab, or tile. A resident mode is allowed
only when the planner proves the active stage fits inside the configured RAM and
VRAM budgets with reserve space; otherwise the stage must fall back to bounded
slab or tile iteration.

`FitsImageReader` performs raw memmapped FITS tile reads and applies
`BSCALE`/`BZERO` per tile for scaled integer FITS. This avoids the Astropy
scaled-image `memmap=False` fallback in the light calibration, warp, local
normalization, and integration paths. Master bias, dark, and flat construction
also uses tile streaming in the high-level pipeline. Within each tile, master
stacking uses a fixed-size float64 accumulator instead of a 3D tile stack, so
host memory does not scale with calibration-frame count. Large
median-normalized flats use a temporary float32 `memmap` scratch file and an
in-place partition to compute an exact median without keeping the full image in
process memory, including small flat images where a full-frame read would be
convenient but unnecessary.

The standalone `glass.gpu.master_frames` helpers use the same bounded input
pattern: FITS tile reads plus per-tile accumulators. When the native CUDA module
is available they reuse the CUDA weighted-accumulation kernel; otherwise they
fall back to a CPU tile accumulator instead of a full-frame stack.

Integration uses tile streaming. For `rejection=none`, weighted mean
integration uses fixed-size sum, weight-sum, and coverage accumulators instead
of a per-tile 3D frame stack. Rejection modes still build a tile stack because
sigma and winsorized rejection need the per-pixel frame distribution.

Quality measurement reads calibrated frames in tiles. It computes exact median
backgrounds through a temporary `memmap` scratch file, computes mean/std in the
same tile pass, and performs star detection in a second tile pass with a 1-pixel
halo around each tile.

Registration uses tile reads to build a bounded preview image before running the
CPU phase-correlation baseline. The preview scale, shape, tile size, and tile
count are recorded in `registration_results.json`. Even `preview_scale=1`
previews are filled by tile reads instead of a full-frame load.

The memory model has four levels:

- Source files: immutable FITS/XISF input images.
- Device hot set: calibrated, registered, or integration-ready frame batches
  that are most valuable for the next GPU stage. Raw input buffers are reused
  and released after the next intermediate level is produced.
- RAM warm cache: bounded host cache for master frames, resident-batch spill,
  and prefetch queues when VRAM is not large enough. RAM is preferred over disk
  for reusable intermediates as long as it stays below a configured high-water
  mark and does not trigger OS paging.
- Host staging: small full-frame, slab, or tile buffers, preferably
  memory-mapped or streaming reads.
- Run cache: checkpointable intermediate artifacts under the run directory, used
  after VRAM/RAM cache options are exhausted or when resume durability is more
  important than speed.

For a large-memory GPU, the preferred light path is staged residency:

- Upload one raw light into a reusable device input buffer.
- Calibrate it into a device-resident calibrated layer, then release/reuse the
  raw input buffer immediately.
- Transform calibrated frames into an aligned layer, then release calibrated
  frames unless the memory plan explicitly keeps them for retry or diagnostics.
- Apply local normalization into an LN layer when LN is materialized as images;
  then release the aligned layer. If LN is represented as parameters, keep only
  those parameters and apply them while feeding integration.
- Feed the current highest-value layer into integration and retain only
  accumulators, weight/coverage/rejection maps, and final outputs.

The logical data chain is therefore:

`raw input -> calibrated -> aligned -> local-normalized -> integrated output`

Resident CUDA runs now write `resident_memory_lifecycle.json` as the runtime
evidence surface for this chain. The artifact is derived from run-local GLASS
artifacts and records, per output group, the estimated raw host/device staging
surface, master calibration surfaces, calibrated resident stack,
registration/warp workspace, local-normalization surface, and integration
output workspace. Each row declares its residence type and release point. This
is intentionally an estimated lifecycle contract rather than a live CUDA
allocator trace: it proves the declared stage handoff and provides a stable
target for future allocator telemetry, but it must not be read as exact peak
VRAM measurement.

As of S2-Gate 674, this lifecycle is a mainline postcondition. Resident default
runs are not green unless `phase2-mainline-audit` and
`resident-regression-gate` can see a passing lifecycle artifact with transient
raw staging, resident calibrated frames, no registered disk cache, and valid
calibrated-stack/peak byte estimates. Small smoke runs may derive shape from
output FITS headers and frame counts from `frame_accounting.json`, but they
still use the same contract.

As of S2-Gate 681, `--ram-budget-gb` participates in resident native-completion
raw staging. When no explicit raw-ring frame count is supplied, GLASS may use
up to 25% of the RAM budget for pinned host raw FITS completion buffers,
capped by light-frame count and never below the runtime preset's safe base.
This is a RAM warm-cache policy for the read/H2D/calibration boundary only; it
does not change the device-resident calibrated stack or promote full raw-frame
preload as a default. The resolved budget source, cap, planned frames, and
effective native queue buffer count are recorded in resident artifacts.

At steady state the planner should keep only the active source layer, the target
layer being produced, and stage scratch buffers. Brief two-layer residency is
allowed because every transition needs a source and a destination. Additional
layers are allowed only when the budget calculation shows they fit with reserve
and when keeping them avoids a more expensive recomputation.

For the M38 H benchmark dataset, one `9600 x 6422` float32 frame is about
235 MiB. Two hundred calibrated frames are about 45.9 GiB. Three full-frame
master calibration frames plus one reusable raw-light buffer add about
0.9 GiB, and output/weight maps add less than 0.5 GiB. This fits comfortably on
a 96 GiB GPU for a calibration-plus-mean-integration benchmark. Keeping both a
calibrated stack and a separate registered stack would require about 91.8 GiB
before temporary buffers, so the planner should either transform in place,
stream registration into integration, or switch to a batched mode.

The cache hierarchy is:

1. VRAM hot set: fastest, used for the current stage and next-stage handoff.
2. RAM warm cache: preferred spill and prefetch target; never allowed to push
   the system into virtual-memory paging.
3. Disk run cache: durable checkpoint and diagnostic artifacts.

The tile scheduler exposes rectangular tiles with stable bounds. Later gates
extend it with halos for convolution, star detection, warp interpolation, and
local normalization windows.

Every heavy stage should declare:

- input artifacts;
- output artifacts;
- tile shape;
- RAM budget;
- VRAM budget;
- checksum or freshness rule;
- resume behavior.

Failure rules:

- write `run_state.json` before returning failure;
- preserve completed artifacts;
- never modify the input directory;
- never silently skip failed frames;
- record crop boxes, masks, and coverage if geometry changes.
