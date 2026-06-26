# S2 Gate 706 Status: Mainline Calibration-Lane Budget Guard

- Gate: S2-Gate 706
- Status: green
- Date: 2026-06-26
- Scope: real 200-light mainline A/B guard for resident calibration lane overprovision.

## Completed

- Retested the obvious post-Gate705 calibration scaling candidate on the real
  200-light mainline: `--resident-calibration-streams 8` and
  `--resident-calibration-wave-frames 8`.
- Verified the candidate preserved the scientific output surface:
  - Phase 2 mainline audit passed.
  - Resident regression gate versus Gate705 passed under the total elapsed
    threshold.
  - Tracked resident integration FITS maps had `0` hash mismatches and `0`
    missing map classes.
  - Active/masked frame accounting stayed `193 / 7`.
- Rejected the candidate for default promotion because
  `light_read_upload_calibrate` regressed from `2.982370199984871 s` to
  `3.173723299987614 s`, ratio `1.0641614176548955`.
- Tightened `glass phase2-mainline-ab` default
  `light_read_upload_calibrate` component budget from `1.50x` to `1.05x`.
- Added a focused unit test proving that a candidate can pass total elapsed
  budget while failing the hot-component budget.
- Updated Phase 2 hardening, validation, and known-limitations docs.

## Real 200-Light Artifacts

- Baseline:
  `C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000`
- Candidate:
  `C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\streams8_wave8_candidate`
- Candidate mainline audit:
  `C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_mainline_audit.json`
- Existing resident regression gate:
  `C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_vs_gate705_regression.json`
- Mainline A/B with tightened budget:
  `C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_phase2_mainline_ab.json`
- CUDA doctor:
  `C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_doctor.json`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\streams8_wave8_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-calibration-streams 8 --resident-calibration-wave-frames 8

.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000 --candidate-run C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\streams8_wave8_candidate --out C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_vs_gate705_regression.json --markdown C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_vs_gate705_regression.md --max-elapsed-ratio 1.05 --fail-on-failure

.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\streams8_wave8_candidate --out C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green

.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000 --candidate-run C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\streams8_wave8_candidate --out C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_phase2_mainline_ab.json --markdown C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_streams8_phase2_mainline_ab.md --max-elapsed-ratio 1.05 --min-active-frame-count 190

.\.venv\Scripts\python.exe -m pytest -q tests/test_phase2_mainline_ab.py
.\.venv\Scripts\python.exe -m ruff check src/glass/report/phase2_mainline_ab.py tests/test_phase2_mainline_ab.py
.\.venv\Scripts\python.exe -m glass.cli doctor --json C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\gate706_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused `phase2-mainline-ab` tests: `8 passed in 0.44 s`.
- Ruff on touched Python files: passed.
- Full pytest: `1452 passed in 73.23 s`.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limits

- Gate706 does not change CUDA kernels or scientific math.
- The rejected 8-lane candidate is a scheduling negative result, not a
  correctness failure.
- The current 4-lane Gate705 default remains the resident calibration schedule.
- Remaining substantive work is still in actual H2D/calibration overlap,
  resident orchestration, and the resident winsorized integration reducer.

## Next Step

- Return to a substantive implementation gate that reduces real hot-path work,
  preferably native H2D/calibration overlap or resident integration internals,
  while keeping `phase2-mainline-ab` as the default-promotion guard.

## Clean-Room Compliance

- Uses GLASS-owned code, tests, and artifacts plus user-owned real benchmark
  data.
- No proprietary or external implementation source was inspected or used.
- Input image directories were not modified.
