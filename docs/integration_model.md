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
- low rejection map
- high rejection map

## Weighting

Supported modes:

- `none`: every valid frame contributes weight 1.
- `simple_snr`: uses the per-frame quality SNR when available, falling back to
  the frame quality weight and then to 1.

The selected per-frame weights are recorded in `integration_results.json`.

## Rejection

Supported modes:

- `none`: weighted mean over valid coverage pixels.
- `sigma_clip`: excludes pixels outside median +/- sigma thresholds.
- `winsorized_sigma`: counts low/high outliers and clamps them to the sigma
  thresholds before weighted averaging.

The rejection maps count low and high outliers per output pixel.

## CUDA Scope

CUDA currently provides `integrate_accumulate_mean_tile_f32`, a weighted mean
accumulator used for non-rejection integration. Rejection modes remain CPU
baseline in Gate 11 because they need robust per-pixel stack statistics first.
This leaves a clear CPU reference for future CUDA reduction kernels.

## Artifact

`integration_results.json` records source stage, combine mode, weighting,
rejection mode, sigma thresholds, per-frame weights, and all output map paths.
