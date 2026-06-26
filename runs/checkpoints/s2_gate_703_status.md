# S2-Gate 703 Status: Post-Resident Reference Health Reuse

## Gate

- Gate: S2-Gate 703
- Date: 2026-06-26
- Status: green

## Completed

- Added `--resident-reference-health-phase auto|pre|post` for resident `run`
  and `audit`.
- Added default phase resolution that keeps explicit CUDA reference scouts on
  the pre-compute health path, but defers CUDA-auto CPU-fallback scouts to
  post-resident artifact validation.
- Added post-resident reference health generation from GLASS-owned
  `resident_reference_scout.json`, `resident_registration_quality.json`, and
  `resident_frame_masks.json`.
- Wired both resident `run` and `audit` flows so post health runs after
  `resident_registration_health` and before resident postcondition contracts.
- Updated Phase 2 mainline audit next-priority evidence for post-resident
  reference-health reuse.
- Updated Phase 2 hardening documentation and algorithm-source log.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_reference_health.py src/glass/cli.py tests/test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py -k "resident_reference_health or auto_cuda_attempt_health or reference_scout_auto"`
- `.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_reference_health.py src/glass/cli.py src/glass/report/phase2_mainline_audit.py tests/test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_phase2_mainline_audit.py tests/test_cli_smoke.py -k "resident_reference_health or auto_cuda_attempt_health or phase2_mainline_audit"`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\post_reference_health_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\post_reference_health_candidate --out C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\gate703_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\gate703_mainline_audit.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\runs_20260626_102533\pipeline_dq_ledger_candidate --candidate-run C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\post_reference_health_candidate --out C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\gate703_vs_gate702_regression.json --markdown C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\gate703_vs_gate702_regression.md --max-elapsed-ratio 1.05`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff over touched files: passed.
- Focused reference health / CLI tests: `9 passed, 85 deselected`.
- Focused reference health plus Phase 2 mainline audit tests:
  `17 passed, 88 deselected`.
- Full pytest: `1450 passed in 72.78s`.

## Real 200-Light Validation

- Candidate:
  `C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\post_reference_health_candidate`
- Baseline:
  `C:\glass_runs\phase2_s2_gate702_pipeline_dq_ledger\runs_20260626_102533\pipeline_dq_ledger_candidate`
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\gate703_mainline_audit.json`
- Resident regression:
  `C:\glass_runs\phase2_s2_gate703_post_reference_health\runs_20260626_104630\gate703_vs_gate702_regression.json`
- Mainline audit status: passed, failed checks `[]`.
- Regression status: passed, failed checks `[]`.
- Determinism summary: output, registration, frame accounting, frame signature,
  and artifact difference counts all `0`.
- Total elapsed: Gate702 `12.230225099949166 s`; Gate703
  `11.912095099687576 s`; ratio `0.9739882138176744`.
- Reference health elapsed: Gate702 `0.424323600018397 s`; Gate703
  `0.0033238999312743545 s`.
- Resident calibration/integration remains dominant at
  `10.474013799917884 s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limits

- This gate changes scheduling and validation for the CPU-guarded
  CUDA-attempt fallback reference path only.
- Explicit CUDA reference scouts still run pre-compute reference health.
- Science pixels, calibration, registration, local normalization, rejection,
  DQ formulas, output maps, and CUDA kernels are unchanged.
- The main remaining runtime target is resident calibration/integration,
  especially read/upload/calibrate and resident integration kernel time.

## Next

- Return to substantive resident calibration/integration work:
  reduce read/upload/calibrate wall time through deeper overlap or reduce
  resident integration kernel time with a larger CUDA reducer design.
- Alternatively, exercise nonzero source-DQ/mask semantics with synthetic plus
  real validation if correctness coverage is prioritized.

## Clean-Room

- Compliant. This gate uses only GLASS-owned runtime artifacts, tests, code,
  and user-owned 200-light benchmark outputs. It does not inspect external
  implementation source or modify input image directories.
