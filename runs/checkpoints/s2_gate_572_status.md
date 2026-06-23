# S2-Gate 572 Status: Resident Registration Health Admission

## Gate

S2-Gate 572 - resident registration health gate for the default CUDA triangle
registration path.

## Completed Content

- Added `src/glass/engine/resident_registration_health.py`.
- Added `resident_registration_health.json` as a post-resident CUDA admission
  artifact.
- Added CLI options:
  - `--resident-registration-health-gate {auto,off,warn,fail}`
  - `--resident-registration-health-min-accepted-fraction`
  - `--resident-registration-health-min-accepted-frames`
- Default `auto` resolves to `fail` for `similarity_cuda_triangle`, where
  GLASS currently records complete per-frame resident quality decisions.
- Default thresholds are accepted fraction `0.75` and accepted frame count `2`.
- `registration=off`, `similarity_cuda_catalog`, and `external_matrix` remain
  non-blocking by default until their resident quality artifacts expose the same
  complete decision contract.
- Updated registration model and algorithm-source documentation.

## Commands Run

```powershell
.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_registration_health.py src\glass\cli.py tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_registration_health_passes_healthy_quality tests/test_cli_smoke.py::test_resident_registration_health_blocks_catastrophic_rejection tests/test_cli_smoke.py::test_cli_resident_run_blocks_catastrophic_registration_health tests/test_cli_smoke.py::test_cli_resident_run_auto_reference_scout_feeds_reference_admission
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate572_registration_health\explicit_cuda_catalog_should_fail --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --resident-reference-scout-backend cuda
.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate572_registration_health\default_safe_auto_should_pass --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache
.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_aligns_shifted_pair tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_rejects_low_quality_matrix tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack tests/test_cli_smoke.py::test_cli_resident_run_blocks_catastrophic_registration_health
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\glass.exe doctor
```

## Test Result

- Focused health/CLI tests: `4 passed in 0.55s`.
- CLI smoke: `63 passed in 6.12s`.
- Regression subset after contract narrowing: `6 passed in 1.60s`.
- Full pytest final result: `1232 passed in 50.76s`.
- An intermediate full pytest run failed because the first implementation
  applied default health gating to `registration=off`,
  `similarity_cuda_catalog`, and `external_matrix`; the gate was corrected to
  default-fail only the current complete triangle quality path.

## Real 200-Light Validation

Bad explicit CUDA reference-scout probe:

- Run: `C:\glass_runs\phase2_s2_gate572_registration_health\explicit_cuda_catalog_should_fail`
- Result: failed at `resident_registration_health`.
- Accepted frames: `6 / 200` (`0.03`).
- Rejected frames: `194 / 200` (`0.97`).
- Internal elapsed: `4.675011499901302 s`.
- This is the desired result: a catastrophic reference/registration outcome is
  no longer reported as a successful pipeline run.

Safe default reference-scout path:

- Run: `C:\glass_runs\phase2_s2_gate572_registration_health\default_safe_auto_should_pass`
- Result: passed through integration.
- Accepted frames: `193 / 200` (`0.965`).
- Rejected frames: `7 / 200` (`0.035`).
- Internal elapsed: `7.3801251001423225 s`.
- WBPP reference time used for continuity: `1092.541 s`.
- Speedup versus WBPP timing: `148.03827647568343x`.
- Master SHA256:
  `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`.
- The SHA256 matches the Gate570/Gate571 safe default master.

## CUDA

- CUDA available: yes.
- Native CUDA extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- The gate is post-run in this checkpoint, so bad experimental references still
  spend compute before being rejected.
- `similarity_cuda_catalog` and `external_matrix` are not default-failed until
  their resident quality artifacts provide a complete per-frame decision
  contract.
- The next engineering step should move reference-health earlier, using
  calibrated-frame or GPU-resident evidence before full integration.

## Next Step

S2-Gate 573 should build an early reference-health scout/admission loop for the
resident default path so bad CUDA catalog references are rejected before full
calibration/warp/integration work begins. It should remain tied to the real
200-light benchmark and preserve the safe default master hash.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned artifacts, GLASS CLI state, and user-run
real benchmark outputs only. It does not inspect or derive from external
implementation source and does not modify input image directories.
