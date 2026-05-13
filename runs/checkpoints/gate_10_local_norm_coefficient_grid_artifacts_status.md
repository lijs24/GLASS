# Gate 10 Local Norm Coefficient Grid Artifacts Status

## Gate

Gate 10 diagnostic/artifact checkpoint.

This checkpoint strengthens the tile-mode Local Normalization stage by making per-tile coefficients auditable and resumable. It does not claim full WBPP-like interpolated/windowed LN completion.

## Completed Content

- `local_norm_results.json` now records per-frame coefficient grid metadata:
  - `coefficient_grid_path`;
  - `model`;
  - `grid_rows`;
  - `grid_cols`.
- Each normalized frame writes a sidecar coefficient-grid JSON file:
  - per-tile scales;
  - per-tile offsets;
  - per-tile valid-pixel counts;
  - per-tile statuses.
- Added pipeline fixture assertions for coefficient-grid artifact shape and existence.
- Updated `docs/local_normalization_model.md` artifact documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\local_norm.py tests\test_pipeline_fixture.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_run_local_normalization tests\test_cpu_local_norm.py tests\test_gpu_local_norm_vs_cpu.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Targeted LN tests: `11 passed in 0.74s`.
- Full test suite: `167 passed in 7.82s`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- Coefficients are piecewise per tile, not smoothly interpolated.
- Tile-mode CPU uses median/std; tile-mode CUDA uses mean/std primitive when available.
- The resident high-VRAM path still uses global mean/std LN rather than this tile-grid artifact model.
- Full windowed local background modeling and robust masks remain future work.

## Next Step

- Wire tile-grid coefficient generation and CUDA grid apply into the resident path, or add interpolated coefficient application for smoother LN.

## Clean-room Compliance

- Compliant. The change records GPWBPP-owned LN coefficients and uses general local statistics math.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
