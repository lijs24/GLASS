# S2-Gate 571 Status: Opt-In CUDA Catalog Reference Scout

## Gate

S2-Gate 571 adds an explicit CUDA catalog backend to the resident reference
scout, validates it against the 200-light benchmark, and prevents unsafe CUDA
promotion after the real-data health check fails.

## Completed

- Added `--resident-reference-scout-backend auto|cpu|cuda` to `glass run` and
  `glass audit`.
- Added CUDA-backed scout scoring through existing
  `glass_cuda.star_grid_top_nms_candidates_f32`.
- Added per-frame scout artifact fields:
  - `catalog_backend`
  - `catalog_diagnostics`
  - `catalog_backend_requested`
  - `catalog_backend_resolution`
- Kept `auto` on the safe CPU scout path until a future CUDA reference-health
  gate passes on real data.
- Explicit `--resident-reference-scout-backend cuda` remains available for
  diagnostics and future hardening.
- Updated `docs/registration_model.md`.
- Updated `docs/algorithm_sources.md`.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_reference_scout.py src\glass\cli.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_resident_run_auto_reference_scout_feeds_reference_admission tests/test_cli_smoke.py::test_resident_reference_scout_prefers_dominant_orientation tests/test_cli_smoke.py::test_resident_reference_scout_cuda_catalog_backend_records_diagnostics tests/test_cli_smoke.py::test_resident_reference_scout_auto_keeps_cpu_until_cuda_reference_health_gate tests/test_cli_smoke.py::test_resident_reference_scout_explicit_cuda_backend_reports_unavailable`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py tests/test_fits_io.py`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\explicit_cuda_catalog_scout --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --resident-reference-scout-backend cuda`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\default_safe_auto_scout --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\default_safe_auto_scout_repeat --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe doctor`

## Test Results

- Focused scout tests: `5 passed in 0.84 s`.
- CLI/FITS related suites: `77 passed in 6.89 s`.
- Full pytest: `1229 passed in 53.15 s`.
- Syntax check: passed.

## Real 200-Light Validation

### Safe Default Auto Scout

- Run root:
  `C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\default_safe_auto_scout`
- Repeat run root:
  `C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\default_safe_auto_scout_repeat`
- Catalog backend requested/effective: `auto -> cpu`.
- Backend resolution reason:
  `cuda_reference_scout_requires_explicit_backend_until_real_reference_health_passes`
- CUDA status recorded by scout: `available`.
- Selected reference: `F000225`,
  `C:\gpwbpp_runs\final_m38_h_200\input\Light\LIGHT_H_0165.fits`.
- Orientation key: `east / 92.0`.
- Accepted/reference/rejected frames: `192 / 1 / 7`.
- Rejected frame ids:
  `F000160,F000213,F000214,F000215,F000216,F000217,F000218`.
- Pipeline contract: passed.
- Run timing total: `7.9146436000592075 s`.
- Repeat timing total: `7.809409200039227 s`.
- WBPP black-box elapsed reference: `1092.541 s`.
- Repeat speedup versus WBPP: `139.90059580877283x`.
- Safe default master SHA256:
  `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`.
- Gate570 master SHA256:
  `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`.
- Safe default vs Gate570 master difference: `RMS=0`, `p99_abs=0`,
  `max_abs=0`, shape `(6422, 9600)`.

### Explicit CUDA Scout Negative Probe

- Run root:
  `C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\explicit_cuda_catalog_scout`
- Catalog backend requested/effective during the probe: `cuda -> cuda`.
- Selected reference: `F000215`,
  `C:\gpwbpp_runs\final_m38_h_200\input\Light\LIGHT_H_0155.fits`.
- CUDA catalog diagnostics for selected row:
  - model: `cuda_grid_top_nms_candidates_f32`
  - `stored_count=16`
  - `detected_count=41`
  - `catalog_sort_mode=shared_bitonic_power2`
  - `catalog_topk_mode=strict_flux_precheck_per_cell_lock`
- Registration quality summary: only `5` ok frames plus `1` reference, with
  `194` rejected frames.
- Interpretation: raw sampled CUDA catalog peak scoring is not sufficient as a
  default reference policy. The gate therefore keeps CUDA scout opt-in and
  records the required next step as a reference-health gate over resident
  registration evidence or calibrated GPU catalogs.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- Safe default:
  `C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\default_safe_auto_scout`
- Safe default repeat:
  `C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\default_safe_auto_scout_repeat`
- CUDA negative probe:
  `C:\glass_runs\phase2_s2_gate571_cuda_reference_scout\explicit_cuda_catalog_scout`
- Safe default `resident_reference_scout.json`.
- CUDA probe `resident_reference_scout.json`.
- Safe default and repeat `pipeline_contract.json`.
- Safe default and repeat integration `resident_master_H.fits`.

## Known Limitations

- CUDA scout remains opt-in because the first real probe selected a poor
  reference and caused a severe registration-quality regression.
- The safe default still performs CPU raw-light crop reads before resident
  execution.
- The current pipeline contract did not fail the bad CUDA probe despite 194
  rejected frames. A follow-up gate should harden the resident reference-health
  or registration-quality admission surface so such probes fail before being
  considered science-acceptable.

## Next Step

Implement a resident reference-health admission gate that rejects or downranks
candidate references causing excessive registration rejection, then retry CUDA
catalog reference selection with calibrated/resident GPU evidence.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA primitives, GLASS FITS reads, GLASS
tests, and user-owned 200-light artifacts only. It does not inspect external
proprietary source code, copy external algorithms, or modify input image
directories.
