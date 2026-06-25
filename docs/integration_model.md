# Integration Model

Integration is designed as a tile-streaming accumulator. Initial CPU baseline
supports mean integration and sigma clipping on small synthetic stacks.

## Gate 11 Baseline

Gate 11 integrates registered or local-normalized frames tile by tile. It never
loads all registered lights into memory at once. For each filter group, the
engine opens the contributing FITS files with memmap, reads one tile from each
frame, integrates that small stack, and writes output tiles directly to FITS
maps.

Outputs per filter:

- master light
- weight map
- coverage map
- variance map
- low rejection map
- high rejection map

## Weighting

Supported modes:

- `none`: every valid frame contributes weight 1.
- `simple_snr`: uses the per-frame quality SNR when available, falling back to
  the frame quality weight and then to 1.
- `combined`: uses the S2-Gate 6 quality score, combining median star SNR,
  star count, FWHM penalty, eccentricity penalty, background-noise penalty, and
  saturation penalty. Tile-mode weights are normalized by their median positive
  value so the integrated master is invariant to global score scale and the
  weight map stays readable.
- `variance_aware`: uses a first-pass inverse-variance proxy from
  `noise_sigma` or `background_rms` in `frame_quality.json`, falling back to the
  frame quality weight when no noise estimate is available. Positive weights
  are median-normalized like the other non-unit modes.

In resident CUDA mode, `simple_snr` is derived from per-frame device-side
mean/std after calibration/registration and before integration. Frames excluded
or failed during registration keep weight 0.
Resident CUDA does not yet implement `combined`; it is rejected explicitly until
resident PSF-quality metrics are available.

The selected per-frame weights are recorded in `integration_results.json`.

## Rejection

Supported modes:

- `none`: weighted mean over valid coverage pixels.
- `sigma_clip`: excludes pixels outside median +/- sigma thresholds.
- `minmax`: rejects the lowest and highest valid sample per pixel when enough
  samples remain.
- `percentile`: rejects samples outside percentile bounds encoded by
  `low_sigma` and `high_sigma`.
- `mad`: uses median absolute deviation as a robust scale estimate.
- `median_sigma`: alias-style median/MAD robust sigma path.
- `winsorized_sigma`: estimates a more stable mean/std by clamping extreme
  samples for the statistics pass, then rejects original samples outside the
  derived sigma thresholds before weighted averaging.

The rejection maps count low and high outliers per output pixel.

The current CPU tile path uses median/std thresholds for rejection. The current
resident CUDA path has two high-VRAM winsorized implementations:

- `sigma_clip`: two-pass mean/std thresholds over finite, positive-weight
  resident samples.
- `winsorized_sigma` `fast_approx`: first-pass mean/std thresholds,
  winsorized mean/std re-estimation, then final rejection of original samples
  outside those thresholds.
- `winsorized_sigma` `hardened_cpu_parity`: resident CUDA median/IQR
  winsorized sigma path matching the GLASS CPU baseline for supported groups.

The resident default is `--resident-winsorized-mode auto`. Auto selects
`hardened_cpu_parity` for resident stack-dispatch groups when diagnostic
maps (`audit` or `science`) are written, the native hardened method is present,
and the group has at most 512 frames. It falls back to `fast_approx` for
`minimal` output-map runs, unsupported dispatch, missing native methods, and
larger groups. For large resident auto groups above 64 frames, GLASS applies a
coverage-preserving default `rejection_max_fraction=0.015` unless the plan or
CLI explicitly supplies a rejection guard. Explicit `hardened_cpu_parity`
remains available up to the same native prototype limit of 512 frames. The
selected mode, requested mode, rejection-guard source, resolution reason, and
runtime contract are written into integration artifacts. The fast approximation
remains available as an explicit escape hatch and is still labeled non-parity.

S2-Gate 600 adds a rejection coverage guard to the CPU baseline and resident
CUDA hardened winsorized path. `rejection_min_samples` and
`rejection_max_fraction` are part of the `IntegrationPolicy` and can be
overridden from the CLI with `--integration-rejection-min-samples` and
`--integration-rejection-max-fraction`. For each output pixel, a proposed
low/high rejection mask is applied only if the remaining valid sample count
stays at or above `rejection_min_samples` and the rejected fraction is at or
below `rejection_max_fraction`. Otherwise the pixel keeps the valid samples for
the final mean and records no low/high rejection at that pixel. This keeps
robust rejection from eroding scientifically important coverage on high-frame
resident stacks while preserving parity between CPU and CUDA hardened behavior.

S2-Gate 601 reduces resident hardened winsorized transfer and host memory
pressure by allowing native count maps to be returned as `uint16`. The master
and weight maps remain `float32`; coverage, low-rejection, and high-rejection
maps are integer sample counts and are written to FITS as signed 16-bit count
maps for 200-frame groups. The Python wrapper records
`count_map_dtype_requested` and actual `count_map_dtype` in the native timing
payload. The float32 count-map path remains available for direct API callers
and compatibility.

S2-Gate 619 adds the same output download policy to the native hardened
winsorized stack path that ordinary sigma and fused-matrix resident integration
already use. `download_mode=full` returns master, weight, coverage, and
rejection maps for audit/science output. `download_mode=master_only` returns
only the master and skips device allocation plus host download for omitted maps.
This is an output-transfer/workspace optimization only; the winsorized
percentile, guard, rejection, and accumulation formulas are unchanged.

S2-Gate 602 extends the resident DQ/count-map native consumer so it accepts
`float32`, `int16`, and `uint16` count maps without forcing compact maps back
to float32. Resident artifacts record `dq_map_count_input_dtypes`; in the
200-light hardened path this proves coverage, low-rejection, and
high-rejection maps remain `uint16` through DQ generation while geometric warp
coverage remains `float32`.

S2-Gate 603 promotes the default resident `auto` path for supported 200-frame
groups from `fast_approx` to `hardened_cpu_parity`. The same real 200-light
M38 benchmark now reaches the CPU-baseline parity winsorized implementation
without explicit `--resident-winsorized-mode` or
`--integration-rejection-max-fraction` flags. Artifacts record the implicit
base guard (`0.5`) and the effective resident auto large-stack guard (`0.015`)
so default scientific behavior remains auditable.

S2-Gate 606 adds a correctness-first fallback for resident hardened
`winsorized_sigma` groups above the native 256-frame CUDA prototype limit.
When `auto` or explicit `hardened_cpu_parity` resolves to a group too large
for the native resident kernel, GLASS records
`hardened_execution_route=cpu_stack_engine_segmented_resident_download` and
runs the CPUStackEngine median/IQR winsorized implementation on tiles
downloaded from the resident calibrated stack. This preserves CPU-baseline
parity for larger audit/science groups while leaving the high-throughput
segmented CUDA reduction as future work. The existing 200-light route remains
the native CUDA resident hardened implementation and is protected by hash
regression tests.

S2-Gate 607 improves that over-limit fallback surface by adding a native
resident batch tile download API. `ResidentCalibratedStack.download_frames_tile`
returns one `(N, tile_h, tile_w)` stack tile for a requested frame-index set, so
the segmented CPUStackEngine replay makes one resident/native call per tile
instead of one call per frame per tile when the native method is available.
Artifacts record batch availability, native availability, call counts, and
download method counts. This does not change the math or promote the fallback
to a final CUDA segmented reduction; it reduces orchestration overhead and
creates the replacement point for a future all-device segmented reducer.

S2-Gate 623 aligns that segmented CPUStackEngine replay with resident native
frame-mask semantics. Before any tile download, the fallback now filters the
resident frame list to finite positive integration weights. Zero-weight,
nonpositive, or non-finite weighted frames are not downloaded and do not enter
the CPUStackEngine rejection/combine request. Timing, DQ provenance, and metrics
record the original resident frame count, active replay frame count, skipped
inactive count, and StackEngine request frame count. A 520-frame synthetic probe
with 20 zero-weight frames verified that the fallback downloaded only the 500
active frame indices and matched the active-only CPUStackEngine result for all
output maps.

S2-Gate 624 promotes a subset of those over-limit cases back to native CUDA.
The native hardened winsorized launcher now admits by finite positive-weight
sample count: total frame groups above 512 may still use the exact CUDA path
when the final positive-weight count is between 1 and 512. Unit-positive
over-limit groups automatically use the active-index kernel for this admission
case, and non-unit groups scan the resident stack while retaining the same
positive-weight bound. The Python resident pipeline applies this as a late
promotion after registration, frame-mask, and weighting decisions are final.
Groups with more than 512 positive-weight frames still use the segmented
CPUStackEngine fallback.

S2-Gate 625 adds an opt-in native CUDA correctness prototype for groups with
more than 512 positive-weight samples. When
`GLASS_CUDA_RADIX_SELECT_WINSORIZED=1` is set, the resident hardened kernel can
select q25/median/q75 through a bitwise sortable-float radix scan instead of a
bounded thread-local sample array. The winsorized formula, rejection guard, and
final weighted mean remain the same as the GLASS CPU baseline, and artifacts
record `percentile_strategy=radix_select_order_statistics_scan`. This path is
not the default yet because it rereads the resident frame axis many times per
output pixel; it exists to validate a true over-512 device-side reduction before
later cooperative or segmented performance work.

S2-Gate 626 makes the CPU winsorized baseline deterministic for mixed-valid
tiles as well as all-valid tiles. DQ-masked or non-finite samples are filtered
before per-pixel sorting; q25/median/q75 use the same `(count - 1) * fraction`
float32 interpolation as the CUDA selectors; fallback and winsorized standard
deviation use frame-axis-valid double accumulation followed by float32 state.
The NaN-containing radix-select stress probe now matches CPU exactly for
master, weight, coverage, and low/high rejection maps without adding any
threshold tolerance.

S2-Gate 627 adds a reusable over-limit benchmark surface for that opt-in
radix-select path. `glass resident-winsorized-overlimit-benchmark` creates a
deterministic synthetic group above the 512-frame bounded kernel limit, times
the tiled CPUStackEngine `winsorized_sigma` baseline, temporarily enables
`GLASS_CUDA_RADIX_SELECT_WINSORIZED=1`, and records CUDA upload/integration
time plus five-map parity statistics. The benchmark does not change default
resident admission. Its first 545-frame validation matched CPUStackEngine
exactly for master, weight, coverage, and rejection maps and measured
`2.035x` CUDA integration speedup excluding upload on a 32 x 32 synthetic
case.

S2-Gate 608 raises the native exact hardened CUDA capacity from 256 to 512
frames. The native kernel now stores and sorts up to 512 valid samples per
pixel before applying the same median/IQR winsorized formula, so 260-frame
groups run through `native_cuda_resident_stack` instead of the segmented host
fallback. A 260-light synthetic validation produced zero pixel differences
against the Gate607 CPUStackEngine fallback while reducing hardened integration
time from `0.009082899894565344 s` to `0.00396340002771467 s`. Groups above
512 frames still use the segmented CPUStackEngine fallback until a scalable
device-side segmented/selection reducer is implemented.

S2-Gate 609 keeps that 512-frame capacity but avoids forcing smaller default
groups through the larger local-array kernel. The native launcher now selects a
`small_256` hardened kernel for frame counts at or below 256 and a `large_512`
kernel for frame counts from 257 through 512. The formula, rejection guard, and
output maps are unchanged; timing payloads record
`native_kernel_frame_capacity` and `native_kernel_capacity_selector`. The real
200-light default route uses `small_256` and preserved SHA256-identical outputs
against Gate608 while reducing native hardened integration from
`3.8001173000084236 s` to `3.7481071000220254 s`. The 260-light synthetic
validation uses `large_512` and stayed SHA256-identical to Gate608.

S2-Gate 610 adds optional native timing decomposition for the hardened resident
integration wrapper. When the native extension supports the `profile` argument,
`hardened_winsorized_timing_s.native_profile` records allocation, weight upload,
kernel+sync, D2H download, free time, downloaded array count, and downloaded
bytes. The real 200-light profiled run preserved SHA256-identical outputs
against Gate609 and measured `kernel_sync_s=3.6350664`,
`download_s=0.1124195`, and `downloaded_bytes=863116800` inside a
`3.752243599970825 s` hardened integration. This makes the next integration
optimization target explicit: the median/IQR hardened kernel itself dominates;
output-map download is not the main bottleneck on the current audit-map route.

S2-Gate 611 replaces the per-pixel full insertion sort used only for native
hardened percentiles with device-side quickselect order statistics. The CUDA
kernel still computes exact linear-interpolated median, q25, and q75 for the
bounded 256/512-frame resident groups, but it no longer relies on the local
sample array being sorted for later statistics. After the percentile pass,
winsorized mean/std are computed by rereading resident samples in input frame
axis order, matching the GLASS CPU baseline's `np.clip(data, ...).mean(axis=0)`
semantics. Timing profiles record
`percentile_strategy=quickselect_order_statistics` and
`winsorized_accumulation_order=frame_axis_input_order`. The real 200-light
default run reduced hardened native integration to `3.4022495999233797 s`
with `kernel_sync_s=3.2809923`, while passing pipeline and resident result
contracts. Compared with the Gate610 sorted-local-array profile, output
changes were limited to 41 of 61,651,200 master pixels
(`6.650316619952247e-07`, RMS `0.0006160635903431593`) and similarly sparse
integer count-map boundary changes. The 260-light synthetic validation stayed
bit-identical to Gate609.

S2-Gate 620 keeps the Gate611 formula and frame-axis accumulation order but
changes the native percentile scheduler from separate full-range q25/median/q75
quickselect calls to an ascending unique-rank quartile selector. Duplicate ranks
from small frame counts and integer percentile positions are selected once, and
each later quickselect starts after the previously selected order statistic.
Profiles record
`percentile_strategy=ascending_unique_quartile_quickselect_order_statistics`.

S2-Gate 621 adds a guarded unit/zero-weight active-index probe for the native
resident hardened winsorized kernel. When
`GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX=1` is set and all positive finite weights
are exactly `1.0`, the wrapper uploads the active frame indices and the kernel
can traverse only those frames. The path preserves the same median/IQR
winsorized formula and frame-axis accumulation semantics, but the real 200-light
benchmark showed it slower than the Gate620 default on the current GPU. It is
therefore disabled by default. Default profiles now record
`unit_positive_weights_detected`, `unit_positive_weights_fast_path`,
`unit_positive_active_frame_count`, and `sample_reuse_strategy`; normal runs
keep `unit_positive_weights_fast_path=false` unless the experiment is explicitly
enabled.

S2-Gate 622 adds a second guarded unit/zero-weight probe,
`GLASS_CUDA_UNIT_WEIGHT_LOCAL_REUSE=1`, that stores an additional frame-order
local sample copy per output pixel and reuses it for the winsorized
mean/variance, rejection-count, and final-mean passes. The route preserves the
same median/IQR formula and frame-axis accumulation order, and real 200-light
regression passed correctness contracts, but it was slower than the default:
native `kernel_sync_s` increased from `3.1234866` to `3.7804679`. This records a
negative design result: duplicating per-thread sample arrays increases local
memory pressure enough to outweigh fewer global stack rereads on the current
200-light RTX PRO 6000 benchmark. The route remains opt-in only, and future
hardened reducer work should avoid larger per-thread local arrays.

S2-Gate 629 adds a third guarded unit/zero-weight probe,
`GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN=1`. When all positive finite integration
weights are exactly `1.0`, the wrapper uploads a one-byte-per-frame positive
weight mask and the hardened kernel keeps the original frame-axis scan order
while skipping inactive frames through that mask. Unlike the active-index probe,
this keeps frame numbering and accumulation order identical to the generic
weighted scan; unlike local reuse, it does not add another per-thread sample
array. The route preserves the same median/IQR winsorized formula, count-map
semantics, and DQ inputs. On the real 200-light Gate629 A/B run, the path
recorded `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`,
`unit_positive_weight_mask_bytes=200`, and `unit_positive_weight_frame_count=193`.
It passed resident determinism and contract checks against Gate628 default
output with zero artifact or numerical drift, reduced total run timing from
`11.385932999895886 s` to `10.765879800193943 s`, and reduced the resident
hardened integration substage from `3.386920899967663 s` to
`3.3294103000080213 s`. Because the integration-only gain is modest and a
single real run still contains I/O and warp timing variation, this path remains
explicitly opt-in pending repeated-run promotion evidence.

S2-Gate 630 repeat-tested that promotion question on the real 200-light
benchmark with three default/mask-scan pairs. Mask-scan won total elapsed time
in all three pairs, but it lost the actual hardened integration and kernel-sync
measurements in all three pairs: `hardened_total_mean_ratio=1.0079091197710124`
and `native_kernel_sync_mean_ratio=1.0063806007728684`. The total-time win was
therefore attributed to surrounding I/O/runtime variance, not to a stable
reducer improvement. Gate630 keeps mask-scan opt-in and hardens the environment
flag parser: `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN` now enables the path only for
explicit true values (`1`, `true`, `yes`, or `on`). Values such as `auto` are
recorded as `unit_positive_weight_mask_reason=ignored_unrecognized_env_value`
and use the default `global_reread_weighted_samples` strategy.

S2-Gate 668 promotes the same frame-mask scan as the default native admission
for unit-positive 0/1 resident weights after a current-HEAD real 200-light A/B
and a post-change default validation both passed resident regression gates with
zero output drift. This is not a claim that Gate630's rejected kernel-speed
hypothesis became true; rather, the branch is now admitted because it is
low-risk, auditable, uses only one byte per input frame, avoids repeated
per-pixel float-weight checks in the dominant default case, and preserved or
slightly improved current total/runtime measurements. When the environment
variable is unset, matching groups record
`unit_positive_weight_mask_reason=default_unit_positive_weight_mask_scan`,
`unit_positive_weight_mask_policy_source=default_unit_positive_weight_mask_scan`,
and `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`.
Explicit false values still restore `global_reread_weighted_samples`, explicit
true values record `environment_enabled`, and unrecognized values such as
`auto` remain disabled.

S2-Gate 669 changes the portable CPU/tile integration sink from full-result
serialization to streaming output. The stage still calls `CPUStackEngine` for
the combine/rejection math, but it now wraps each global output tile in
tile-local `ImageSource` views, runs StackEngine on that tile, writes FITS map
tiles immediately, and aggregates DQ provenance across all tiles. Integration
artifacts record `execution_path=stack_engine_streaming_tile_sink`,
`full_output_arrays_materialized=false`, per-tile contract counts, and a
`stack_engine_streaming_result_contract` that is compatible with the older
`stack_engine_result_contract`. This gate does not change resident CUDA math or
the high-VRAM 200-light default path; it closes the CPU/tile StackEngine
memory-model gap and keeps disabled optional maps such as variance from being
treated as missing requested outputs.

## CUDA Scope

CUDA currently provides `integrate_accumulate_mean_tile_f32`, resident weighted
mean integration, resident mean/std sigma clipping, resident mean/std
winsorized clipping, and a bounded native resident median/IQR hardened
winsorized path with 256-frame and 512-frame native kernel variants using
quickselect percentiles plus input-frame-order winsorized statistics. The
tile-streaming CPU path remains the portable scientific baseline, while the
resident path is the high-VRAM performance path for the 200-light comparison
dataset. Groups above 512 total frames can remain native only when their final
positive-weight sample count is at most 512; larger active groups use the
segmented CPUStackEngine resident-tile fallback, now preferably through the
batch tile-download surface, until the dedicated CUDA segmented reduction is
implemented.

## Variance Map

S2-Gate 9 makes the tile-mode variance map a formal integration artifact. The
StackEngine computes a weighted population variance for `mean` and
`weighted_mean` combines:

```text
variance = sum(w_i * (x_i - master)^2) / sum(w_i)
```

Invalid, rejected, or zero-weight samples do not contribute. Median and sum
combines continue to report an unweighted finite-sample variance diagnostic.
The CUDA streaming fast path for rejection-free tile integration writes the
same population-variance map by accumulating `sum(w*x^2)` alongside `sum(w*x)`.

## Artifact

`integration_results.json` records source stage, combine mode, weighting,
rejection mode, sigma thresholds, rejection coverage guard, per-frame weights,
variance-map enablement, and all output map paths.
