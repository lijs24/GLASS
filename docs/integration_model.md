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
resident CUDA path uses a separate high-VRAM engineering baseline:

- `sigma_clip`: two-pass mean/std thresholds over finite, positive-weight
  resident samples.
- `winsorized_sigma`: first-pass mean/std thresholds, winsorized mean/std
  re-estimation, then final rejection of original samples outside those
  thresholds.

This resident `winsorized_sigma` mode is deliberately labeled as an
approximation. It is useful for speed and diagnostic map development, but it is
not yet a verified reproduction of PixInsight/ImageIntegration-style robust
Winsorized Sigma Clipping. A future gate should implement robust per-pixel
location/scale estimation, finite-sample behavior, and iteration/cutoff details
behind the same public mode name.

## CUDA Scope

CUDA currently provides `integrate_accumulate_mean_tile_f32`, resident weighted
mean integration, resident mean/std sigma clipping, and resident mean/std
winsorized clipping. The tile-streaming CPU path remains the scientific baseline
for correctness, while the resident path is the high-VRAM performance path for
the M38 comparison dataset.

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
rejection mode, sigma thresholds, per-frame weights, variance-map enablement,
and all output map paths.
