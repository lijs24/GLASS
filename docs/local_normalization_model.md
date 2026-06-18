# Local Normalization Model

Local normalization runs after registration and warp. It never changes the image
dimensions. If a future stage crops output, the crop box must be recorded in the
local normalization artifact before integration can consume the result.

## S2-Gate 8 Continuous Baseline

S2-Gate 8 replaces the original piecewise tile apply path with a continuous
coefficient-field baseline:

1. Select the registration reference frame as the local-normalization reference.
2. Iterate over registered FITS files tile by tile.
3. Build a valid-pixel mask from the source and reference coverage maps.
4. Estimate per-tile source/reference mean and standard deviation.
5. Repair empty coefficient tiles from the nearest valid tile.
6. Interpolate the scale and offset grids with bilinear interpolation over tile
   centers.
7. Apply `O(x,y) = a(x,y)S(x,y) + b(x,y)` for valid pixels only.
8. Write `local_norm_results.json`, normalized FITS, DQ FITS, coefficient JSON,
   and diagnostic coefficient/residual maps when the image is within the
   configured diagnostic size limit.

The scale and offset are:

```text
scale = reference_std / source_std
offset = reference_mean - source_mean * scale
```

If either standard deviation is too small, the model falls back to offset-only
matching:

```text
scale = 1
offset = reference_mean - source_mean
```

If a tile has no valid pixels, it is passed through and a warning is recorded.
Its coefficient cell is filled from the nearest valid cell before interpolation.
If no valid coefficient exists for a frame, the scale grid defaults to `1` and
the offset grid defaults to `0`.

The current interpolation model is recorded as:

```text
model = continuous_grid_mean_std_v1
coefficient_field_model = bilinear_tile_center_v1
```

The model never crops. Artifacts record `crop_box = null`; if a future LN stage
introduces cropping, that crop box becomes a required integration input.

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

The tile-mode S2-Gate 8 path now estimates the coefficient grid, repairs empty
cells, and applies a bilinear continuous field on the CPU baseline. When CUDA is
available, the pipeline can use CUDA pair-statistics primitives for coefficient
estimation, then applies the continuous field through the audited CPU tile path.
A fully resident CUDA continuous-field apply kernel remains a later optimization
target.

The resident CUDA stack exposes the same grid application primitive as
`ResidentCalibratedStack.apply_grid_normalization_frame`, plus resident
`frame_pair_grid_stats` for per-tile paired source/reference mean/std estimates.
The CLI path `--memory-mode resident --local-normalization on
--resident-local-normalization-mode grid_mean_std` computes tile coefficients on
the GPU, copies only the small coefficient table to host for audit JSON, and
applies the coefficients directly to frames that are already in VRAM.

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
- coefficient field model and interpolation name
- raw and repaired coefficient grids
- full-resolution scale/offset field paths when written
- residual map path and residual summary when written
- empty coefficient tile repair count
- crop box, currently `null`

Full-resolution diagnostic maps are intentionally bounded because one
9600-by-6422 float32 map is about 235 MiB. The environment variable
`GLASS_LN_FULL_FIELD_MAP_MAX_PIXELS` controls the threshold; the default writes
full maps for small validation runs and records `omitted_due_to_size` for larger
runs while retaining coefficient grids and summaries.

## S2-Gate 313 Contract Audit

S2-Gate 313 adds a dedicated `glass local-norm-contract` audit. The command is
metadata-only: it reads `local_norm_results.json` plus per-frame coefficient
JSON artifacts and checks paths, schema, model names, crop-box recording, DQ
summary presence, coefficient grid dimensions, residual summaries, and optional
full-field diagnostic map paths. It does not read image pixels.

For enabled local normalization, the contract requires:

- top-level `model = continuous_grid_mean_std_v1`
- top-level and per-frame `coefficient_field_model = bilinear_tile_center_v1`
- per-frame `interpolation = bilinear_tile_center`
- per-frame coefficient JSON with raw/repaired scale and offset grids
- per-frame valid-pixel/status grids matching `grid_rows` and `grid_cols`
- recorded residual summaries
- explicit `crop_box`, currently `null`

For disabled local normalization, the contract requires an explicit
`disabled_passthrough` artifact so downstream integration and report stages can
distinguish "LN deliberately off" from "LN silently skipped".

## S2-Gate 314 Guardrail Handoff

S2-Gate 314 makes the S2-Gate 313 contract consumable by run-level guardrails.
`glass pipeline-contract` accepts `--local-norm-contract-json` and, when
supplied, adds the run-level check
`local_normalization_continuous_contract_audit`. This check requires the
attached artifact to be a passing `local_norm_contract`, match the run's
enabled state and coefficient-field model, match the pipeline LN row count, and
report zero failed LN outputs.

`glass guardrails` now generates `local_norm_contract.json` and
`local_norm_contract.md` automatically when the audited run contains
`local_norm_results.json`. The generated audit is passed into the pipeline
contract and recorded in `guardrails_summary.json` plus
`acceptance_contract_bundle.json`. Runs that intentionally stop before local
normalization remain compatible: if `local_norm_results.json` is absent, the LN
contract is marked not required rather than failed.

This handoff does not change local-normalization math or read additional FITS
pixels. It only promotes existing LN metadata into the acceptance contract path
so continuous coefficient-field regressions cannot disappear between a manual
LN audit and final guardrail evidence.
