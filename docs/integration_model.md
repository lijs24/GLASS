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

## CUDA Scope

CUDA currently provides `integrate_accumulate_mean_tile_f32`, resident weighted
mean integration, resident mean/std sigma clipping, resident mean/std
winsorized clipping, and a bounded native resident median/IQR hardened
winsorized path with 256-frame and 512-frame native kernel variants. The
tile-streaming CPU path remains the portable scientific baseline, while the
resident path is the high-VRAM performance path for the 200-light comparison
dataset. Groups above the 512-frame native hardened limit may use the segmented
CPUStackEngine resident-tile fallback, now preferably through the batch
tile-download surface, until the dedicated CUDA segmented reduction is
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
