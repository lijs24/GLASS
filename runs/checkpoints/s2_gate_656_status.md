# S2-Gate 656 Status: Registration Source-DQ Input Audit

## Gate

- Gate: S2-Gate 656
- Theme: per-frame source-DQ catalog-input audit in resident registration
  artifacts
- Status: passed

## Completed Content

- Added registration-time source-DQ input audit serialization to resident CUDA
  outputs.
- `registration_results.json` now includes:
  - top-level `source_dq_registration_input_summary`;
  - per-row `source_dq_registration_input` for each resident registration
    result.
- Extended `resident_registration_runtime_contract.json` so positive
  source-DQ runs must prove:
  - registration rows carry per-frame source-DQ input evidence;
  - registration source-DQ input totals match
    `resident_source_dq_execution.json`;
  - catalog-required source-DQ invalid samples remain visible before
    registration catalog construction.
- Updated focused runtime-contract fixtures and resident mainline fixtures to
  include the new registration input audit when they model positive source-DQ.
- Extended the CUDA synthetic source-DQ triangle test to assert the generated
  registration row and contract checks.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\engine\resident_registration_runtime_contract.py tests\test_resident_registration_runtime_contract.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_registration_runtime_contract.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_source_dq_feeds_registration_runtime_contract
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq_contract.py tests/test_resident_source_dq.py tests/test_pipeline_contract.py tests/test_resident_registration_runtime_contract.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py::test_resident_mainline_framework_source_dq_positive_threshold_passes tests/test_resident_mainline_framework.py::test_resident_mainline_framework_source_dq_scope_relaxes_default_route tests/test_resident_registration_runtime_contract.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_source_dq_feeds_registration_runtime_contract
```

Real 200-light validation:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --out C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\default_strict
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\default_strict --out C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\gate656_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\gate656_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe resident-regression-gate --candidate-run C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\default_strict --baseline-run C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\default_strict --out C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\gate656_regression_vs_gate655.json --markdown C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\gate656_regression_vs_gate655.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe doctor
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff focused checks: passed.
- Focused runtime/CLI source-DQ tests: `9 passed`.
- Wider DQ/source-DQ focused suite: `75 passed`.
- Focused mainline-fixture regression after fixture update: `11 passed`.
- Full pytest: `1379 passed in 60.99s`.

## Real 200-Light Results

- Run:
  `C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\default_strict`
- `resident_registration_runtime_contract.json`: passed.
- `resident_mainline_framework.json`: passed.
- `phase2-mainline-audit --fail-on-not-green`: passed.
- `resident-regression-gate` versus Gate655 default strict: passed.
- Regression elapsed ratio: `1.009718840829939`.
- GLASS elapsed time: `11.83883819996845 s`.
- Input lights: `200`.
- Active/masked frames: `193 / 7`.
- Registration rows: `200`.
- Warped non-reference frames: `192`.
- Native warp chunks: `24` chunks of `8` frames.
- Native warp fallback frames: `0`.
- Native warp total time: `0.4884192 s`.
- Resident component timings:
  - `resident_light_read_upload_calibrate=3.3925699000246823 s`;
  - `resident_registration_warp=0.26639369945041835 s`;
  - `resident_local_normalization=0.3590581000316888 s`;
  - `resident_integration=3.301900500082411 s`;
  - `resident_output_write=0.2690196998883039 s`.
- Source-DQ registration input evidence on this real M38 run:
  - `source_dq_positive=false`;
  - `registration_source_dq_input_available=false`;
  - `registration_source_dq_input_row_count=200`;
  - `registration_source_dq_input_invalid_samples=0`.
- Synthetic positive source-DQ CUDA evidence:
  `test_cli_resident_cuda_triangle_source_dq_feeds_registration_runtime_contract`
  applied one sidecar source-DQ invalid sample, observed it on the moving
  registration row, and passed the new runtime-contract checks.

## CUDA Availability

- CUDA wrapper importable: true.
- Native extension loaded: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Windows package recommendation: `cuda13`; fallback order `cuda13`,
  `cuda12`, `cuda11`, `cpu`.

## Known Limits

- The real M38 200-light benchmark has no nonzero source-DQ sidecars, so the
  real run validates zero-input registration audit closure and default-path
  non-regression. Positive source-DQ row-level behavior is proven by the
  focused synthetic CUDA strict-positive run.
- This gate changes artifact auditability and runtime validation only. It does
  not change calibration, star detection, registration fitting, warp
  interpolation, local normalization, rejection, integration pixel math, CUDA
  kernels, or frame admission.
- Future DQ/mask gates still need broader real-data coverage with nonzero
  source-DQ masks or bad-pixel maps.

## Next Step

- Continue with substantive Phase 2 work: either add a real nonzero DQ/mask
  dataset path, or return to measured resident hot-path work in
  calibration/integration.

## Clean-Room Compliance

- This gate used only GLASS-owned source-DQ rows, resident registration rows,
  runtime-contract artifacts, tests, and user-owned benchmark outputs.
- No proprietary or external implementation source was read, copied,
  summarized, or reworked.
- Original image directories were treated as read-only.
