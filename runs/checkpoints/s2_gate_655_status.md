# S2-Gate 655 Status: Source-DQ To Registration Runtime Bridge

## Gate

- Gate: S2-Gate 655
- Theme: source-DQ / mask pipeline bridge into resident registration runtime
  contract
- Status: passed

## Completed Content

- Extended `resident_registration_runtime_contract.json` with source-DQ
  execution evidence from `resident_source_dq_execution.json`.
- Added contract checks for:
  - source-DQ execution passing when the artifact exists;
  - invalid source-DQ samples being applied when declared;
  - catalog-required non-inline source-DQ samples being visible before resident
    registration catalog construction.
- Added summary fields for source-DQ existence, positive invalid samples,
  applied samples, pre-registration catalog-visible samples,
  post-registration deferred samples, and required samples not visible to
  registration.
- Added unit tests for passing positive source-DQ visibility and failing
  post-registration-only visibility.
- Added a CUDA CLI synthetic test that binds one sidecar source-DQ mask, runs
  resident `similarity_cuda_triangle`, and proves the source-DQ sample is
  pre-registration catalog visible in the runtime contract.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_registration_runtime_contract.py tests\test_resident_registration_runtime_contract.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_registration_runtime_contract.py tests/test_resident_source_dq_contract.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_source_dq_feeds_registration_runtime_contract
```

Real 200-light validation:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --out C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\default_strict
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\default_strict --out C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\gate655_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\gate655_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe resident-regression-gate --candidate-run C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\default_strict --baseline-run C:\glass_runs\phase2_s2_gate654_registration_runtime_contract\runs_20260625_205406\default_strict_final --out C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\gate655_regression_vs_gate654.json --markdown C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\gate655_regression_vs_gate654.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe doctor
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff focused checks: passed.
- Focused resident registration/source-DQ tests: `11 passed`.
- Full pytest: `1378 passed in 61.98s`.

## Real 200-Light Results

- Run:
  `C:\glass_runs\phase2_s2_gate655_source_dq_registration_bridge\runs_20260625_210540\default_strict`
- `resident_registration_runtime_contract.json`: passed.
- `resident_mainline_framework.json`: passed.
- `phase2-mainline-audit --fail-on-not-green`: passed.
- `resident-regression-gate` versus Gate654 default strict: passed.
- Regression elapsed ratio: `1.0138660524354346`.
- GLASS elapsed time: `11.724885900155641 s`.
- Input lights: `200`.
- Active/masked frames: `193 / 7`.
- Registration rows: `200`.
- Warped non-reference frames: `192`.
- Native warp chunks: `24` chunks of `8` frames.
- Native warp fallback frames: `0`.
- Native warp total time: `0.4884724 s`.
- Resident component timings:
  - `resident_light_read_upload_calibrate=3.4670131999300793 s`;
  - `resident_registration_warp=0.2659309997688979 s`;
  - `resident_local_normalization=0.3552255000686273 s`;
  - `resident_integration=3.2340052999788895 s`;
  - `resident_output_write=0.26684659998863935 s`.
- Source-DQ bridge evidence on this real M38 run:
  - `source_dq_exists=true`;
  - `source_dq_positive=false`;
  - `source_dq_input_invalid_samples_before_rejection=0`;
  - `source_dq_required_invalid_samples_not_visible_to_registration_catalog=0`.
- Synthetic positive source-DQ CUDA evidence:
  `test_cli_resident_cuda_triangle_source_dq_feeds_registration_runtime_contract`
  applied one sidecar source-DQ invalid sample and proved it was
  pre-registration catalog visible.

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
  real run validates default-path non-regression and zero-source-DQ closure.
  Positive source-DQ registration visibility is proven by the focused synthetic
  CUDA strict-positive run.
- This gate changes runtime validation and failure behavior only. It does not
  change calibration, star detection, registration fitting, warp interpolation,
  local normalization, rejection, integration pixel math, or frame admission.
- Future DQ/mask gates still need broader real-data coverage with actual
  nonzero source-DQ masks or bad-pixel maps.

## Next Step

- Return to image-path work under the new guardrail: either broaden the
  executable DQ/mask pipeline beyond sidecar visibility, or target the measured
  resident hot path in calibration/integration and registration/warp.

## Clean-Room Compliance

- This gate used only GLASS-owned source-DQ, resident registration, frame-mask,
  and runtime-contract artifacts, GLASS tests, and user-owned benchmark
  outputs.
- No proprietary or external implementation source was read, copied,
  summarized, or reworked.
- Original image directories were treated as read-only.
