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

CUDA can now be used for a per-tile mean/std statistics primitive, a global
pixel-wise apply kernel, and a piecewise grid apply kernel. The standalone
primitive computes source/reference finite-pixel mean and standard deviation for
a tile, derives:

```text
scale = reference_std / source_std
offset = reference_mean - source_mean * scale
```

and applies it with `local_norm_estimate_apply_mean_std_f32`. A valid mask can be
provided by marking invalid pixels as `NaN` before the CUDA statistics pass; mask
outside pixels are restored to the source value after apply. The CPU median/std
baseline remains available and is still used when CUDA is unavailable.

The grid model estimates a coefficient table on the CPU baseline with
`estimate_grid_normalization_mean_std`, then applies that coefficient table with
`local_norm_apply_grid_f32` on the CUDA backend. This first grid implementation is
piecewise constant per tile. It validates the data model, edge tiles, and GPU
coefficient application before adding smoother windowed/interpolated LN.

The resident CUDA stack exposes the same grid application primitive as
`ResidentCalibratedStack.apply_grid_normalization_frame`. It applies an existing
scale/offset coefficient table directly to a resident frame in VRAM, which keeps
the calibrated/registered hot set resident and avoids a CPU round trip during the
apply step. Coefficient estimation for resident tile/window LN is still a later
step.

This CUDA mean/std primitive is intentionally simpler than the full future
WBPP-like local model. It is a tested GPU building block for tile/window LN, not
a claim of PixInsight-identical Local Normalization.

The high-VRAM resident CUDA path also exposes an explicit
`resident_global_mean_std` mode. In this mode calibrated/registered frames stay
in VRAM, the backend computes one finite-pixel mean/std pair per frame on the
device, and each non-reference frame is normalized with:

```text
normalized = source * (reference_std / source_std)
           + reference_mean - source_mean * (reference_std / source_std)
```

If either standard deviation is too small, resident mode falls back to a global
offset-only correction. This mode is a useful high-throughput diagnostic
capability, but it is not the full tile/window local normalization model.

## Artifact

`local_norm_results.json` records:

- enabled state
- reference frame and reference path
- tile size/radius and policies
- crop box, currently `null`
- per-frame normalized path, coverage path, backend, tile count
- mean scale, mean offset, valid-pixel count, status, and warnings
- per-frame coefficient grid path, grid dimensions, per-tile scale/offset arrays,
  per-tile valid-pixel counts, and per-tile statuses
