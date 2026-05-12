# Local Normalization Model

Local normalization runs after registration and warp. It never changes the image
dimensions. If a future stage crops output, the crop box must be recorded in the
local normalization artifact before integration can consume the result.

## Gate 10 Baseline

Gate 10 implements a conservative tile baseline:

1. Select the registration reference frame as the local-normalization reference.
2. Iterate over registered FITS files tile by tile.
3. Build a valid-pixel mask from the source and reference coverage maps.
4. Estimate per-tile source/reference median and standard deviation.
5. Apply `normalized = source * scale + offset` for valid pixels only.
6. Write `local_norm_results.json` and optional `local_norm_cache/*.fits`.

The scale and offset are:

```text
scale = reference_std / source_std
offset = reference_median - source_median * scale
```

If either standard deviation is too small, Gate 10 falls back to offset-only
matching:

```text
scale = 1
offset = reference_median - source_median
```

If a tile has no valid pixels, it is passed through and a warning is recorded.

## Policy

The processing plan stores:

- `enabled`
- `reference_mode`
- `tile_radius`
- `background_mask_policy`
- `outlier_policy`

The CLI can override the plan with `--local-normalization on|off|auto`. `auto`
uses the plan policy. Disabled mode writes a diagnostic passthrough artifact, so
resume and later gates can still determine what happened.

## CUDA Scope

CUDA is currently used for the pixel-wise apply kernel once CPU control logic has
estimated per-tile coefficients. Statistics remain on the CPU in Gate 10. This
keeps the implementation auditable and gives a CPU baseline for later GPU
reductions.

## Artifact

`local_norm_results.json` records:

- enabled state
- reference frame and reference path
- tile size/radius and policies
- crop box, currently `null`
- per-frame normalized path, coverage path, backend, tile count
- mean scale, mean offset, valid-pixel count, status, and warnings
