# S2-Gate 565 Status: Resident Rejection Default Promotion

## Gate

S2-Gate 565 promotes resident CUDA integration rejection from an unrejected
default to a science default: `auto -> winsorized_sigma` for full resident CUDA
integration.

## Completed

- Added `DEFAULT_RESIDENT_INTEGRATION_REJECTION=auto`.
- Added `DEFAULT_RESIDENT_INTEGRATION_REJECTION_EFFECTIVE=winsorized_sigma`.
- Added `_resolve_resident_integration_rejection_default`.
- `glass run` and `glass audit` now resolve resident rejection defaults before
  command capture, memory admission, and execution.
- Full resident CUDA integration resolves unspecified rejection to
  `winsorized_sigma`.
- Explicit `--integration-rejection none` remains the unrejected diagnostic
  escape hatch.
- Non-resident/tile execution keeps `integration_rejection=auto`.
- `run_timing.json` now records `resident_integration_rejection_resolution`.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\cli.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_run_resident_rejection_defaults_to_winsorized_sigma tests\test_cli_smoke.py::test_run_resident_rejection_explicit_none_is_preserved tests\test_cli_smoke.py::test_run_resident_rejection_auto_keeps_tile_path_auto tests\test_cli_smoke.py::test_run_resident_registration_defaults_to_similarity_triangle tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate565_default_resident_rejection\runs_20260623_183202\default_rejection --local-normalization on --resident-local-normalization-mode grid_mean_std --resident-local-normalization-tile-size 256 --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Syntax check: passed.
- Focused default-resolution and resident smoke tests: `6 passed in 0.76 s`.
- Full pytest: `1210 passed in 45.24 s`.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate565_default_resident_rejection\runs_20260623_183202\default_rejection`
- Summary:
  `runs/checkpoints/s2_gate_565_default_resident_rejection_summary.json`
- Shell elapsed: `7.443477799999999 s`.
- Run timing total: `7.086396700004116 s`.
- The run intentionally omitted `--backend`, `--memory-mode`, `--until-stage`,
  `--resident-registration`, and `--integration-rejection`.
- Execution default resolution: backend `auto -> cuda`, memory mode
  `resident -> resident`.
- Resident registration resolution: `auto -> similarity_cuda_triangle`.
- Resident integration rejection resolution: `auto -> winsorized_sigma`.
- Pipeline contract: passed.
- Registration-quality decisions: `200`.
- Decision statuses: `192 accepted / 1 reference / 7 rejected`.
- Active/rejected frames: `193 / 7`.
- Output master, weight map, coverage map, low/high rejection maps, and DQ map
  have SHA256 hashes identical to S2-Gate 564.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `runs/checkpoints/s2_gate_565_real_run_path.json`
- `runs/checkpoints/s2_gate_565_default_resident_rejection_summary.json`
- Real run `run_timing.json` with
  `resident_integration_rejection_resolution`.
- Real run `resident_registration_quality.json`.
- Real run `pipeline_contract.json`.
- Real run integration master/maps under `integration/`.

## Known Limitations

- This gate changes only the resident CUDA default rejection dispatch. It does
  not alter the winsorized algorithm or promote the hardened CPU-parity
  winsorized prototype.
- The current resident default remains `fast_approx` winsorized semantics; the
  artifact records `known_non_parity_pending_cuda_update` as before.
- Explicit `--integration-rejection none` still allows unrejected resident
  diagnostic runs.

## Next Step

Continue reducing real-run manual science parameters: promote local
normalization defaults, then reference/registration parameter defaults, and
finally run a low-argument 200-light A/B against the Phase 1/WBPP comparison
baseline.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned default policy, tests, and user-owned
200-light GLASS artifacts only. It does not inspect external proprietary source
code, copy external algorithms, or modify input image directories.
