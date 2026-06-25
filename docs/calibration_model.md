# Calibration Model

This document records the independent calibration semantics used by GLASS.

Master bias is built through the Phase 2 StackEngine. The default master-frame
policy uses `winsorized_sigma` rejection with conservative sigma limits; tests
also cover explicit min/max rejection to verify that extreme samples are removed
before combining. The legacy streaming mean accumulator remains as a diagnostic
fallback.

Master dark records its exposure and whether it includes bias. If a master dark
is made directly from raw dark frames, `master_dark_includes_bias=true`. If the
dark frames are bias-subtracted before stacking, `master_dark_includes_bias=false`.
This flag changes the light calibration formula and is always exposed in plan,
state, and report artifacts.

Master flat is calibrated by subtracting either bias or flat-dark data, then
normalizing each source flat by its own median or mean before StackEngine
combination. A `flat_floor` avoids division by zero and is applied to the final
normalized master flat.

As of S2-Gate 670, CPU/tile master calibration uses a streaming StackEngine
sink for bias, dark, and per-flat normalized flat masters. Each output tile is
presented to `CPUStackEngine` through tile-local image sources, written
immediately to the master FITS, and then discarded. Master artifacts record
`execution_path=stack_engine_master_streaming_tile_sink`,
`full_output_arrays_materialized=false`, per-tile contract counts, and a
`stack_engine_master_streaming_result_contract`. This keeps the same
calibration formulas while removing full-frame `StackEngineResult`
materialization from the master-frame pipeline.

As of S2-Gate 671, the same CPU/tile master calibration path writes an explicit
master DQ FITS artifact for each master bias, dark, and flat. Master records in
`calibration_artifacts.json` include `dq_mask_path` and `dq_summary`, and the
summary is mirrored in StackEngine DQ provenance. The DQ mask marks no-data
pixels and pixels touched by low/high rejection according to GLASS DQ flag
semantics; this makes master-frame DQ inspectable instead of JSON-only.

Both tile-mode and resident-mode `glass run` honor `--flat-floor`, and the
effective value is written into `calibration_artifacts.json` or
`resident_artifacts.json`. This is scientifically important for real flat
fields with dust shadows or clipped pixels because too small a floor can create
extreme calibrated values that break downstream star matching.

Resident CUDA calibration now follows the planner's per-light matching groups.
Before each light is calibrated, the resident runner loads or builds the
matching bias/dark/flat master set from `LightPlan.matching_*_group`, uploads
that set to the resident stack, and records the set in `resident_artifacts.json`.
This avoids the earlier aggregate-same-shape shortcut and keeps resident output
comparable with tile-mode calibration.

Light calibration:

```text
scaled_dark = master_dark * light_exposure_s / dark_exposure_s
```

When `master_dark_includes_bias=true`:

```text
calibrated = (light - scaled_dark) / normalized_flat
```

When `master_dark_includes_bias=false`:

```text
calibrated = (light - master_bias - scaled_dark) / normalized_flat
```

Dark scaling is controlled by policy and can be disabled. Pedestal is applied
after flat division.

## Additional Phase 2 Calibration Controls

Overscan/trim first pass:

- `overscan_enabled`
- `overscan_columns`
- `overscan_rows`
- `trim_overscan`

The CPU baseline subtracts the median of the configured overscan samples and can
trim the overscan rows/columns. Pipeline-wide tile integration of this transform
is a later hardening step.

Cosmetic correction first pass:

- `cosmetic_correction_enabled`
- `cosmetic_hot_sigma`
- `cosmetic_cold_sigma`
- `saturation_level`

When enabled, calibrated-light tiles are scanned for hot and cold outliers using
a robust median/MAD scale estimate. Corrected pixels are replaced by the local
tile median and marked in the DQ mask as `HOT_PIXEL`, `COLD_PIXEL`, and
`COSMETIC_CORRECTED`. Pixels at or above `saturation_level` are marked
`SATURATED`.

All calibrated light artifacts now record `dq_mask_path`, `dq_summary`, and
`cosmetic_correction` metadata.
