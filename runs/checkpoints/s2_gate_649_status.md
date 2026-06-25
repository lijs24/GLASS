# S2-Gate 649 Status: Resident Calibration Boundary Reentry

## Gate

- Gate: S2-Gate 649.
- Status: passed.
- Date: 2026-06-25.
- Scope: make the ready resident calibration/master-cache reentry boundary executable through `glass resume`.

## Completed Content

- `resident_reentry_boundary.json` now marks `resident_master_cache` and `resident_calibration` as resume-supported only when a matching `run_invocation.json` targets the same run directory.
- Resident resume preflight now emits a `boundary_reentry` decision for ready calibration/master-cache boundaries.
- `glass resume` now handles:
  - `reenter_from_calibration_boundary`;
  - `reenter_from_master_cache_boundary`.
- `resident_resume_reentry.json` records `reentry_key=boundary_reentry` and the concrete `boundary_name`.
- Added focused tests for matching-invocation boundary support and real CLI reentry behavior.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Real 200-Light Validation

- Candidate run:
  `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary`.
- Initial skeleton state: incomplete resident CUDA run with `resident_calibration_integration` started, ready `resident_master_cache`, ready `resident_calibration` boundary evidence, and a matching stored `run_invocation.json`.
- Initial boundary preflight:
  - `passed=true`;
  - `resume_action=reenter_from_calibration_boundary`;
  - `boundary_reentry_eligible=true`;
  - `boundary_reentry_name=resident_calibration`.
- Resume result:
  - `resident_resume_reentry.json` status `passed`;
  - `preflight_action=reenter_from_calibration_boundary`;
  - `reentry_key=boundary_reentry`;
  - `boundary_name=resident_calibration`;
  - `exit_code=0`;
  - final preflight `resume_action=noop_complete`.
- Final ledger/preflight:
  - `16` completed stages;
  - `24` expected resident artifact rows;
  - `0` missing artifact rows.
- Total elapsed: `11.485255000297911 s`.
- Resident calibration/integration stage: `9.839130699983798 s`.
- Resident reentry boundary stage: about `0.013113 s`.
- Frame accounting: `200` planned lights, `193` active frames, `7` masked frames.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_reentry_boundary.py tests\test_resident_resume.py
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_reentry_boundary.py src\glass\engine\resident_resume.py src\glass\cli.py tests\test_resident_reentry_boundary.py tests\test_resident_resume.py
.\.venv\Scripts\glass.exe resident-reentry-boundary --run C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary --fail-on-missing
.\.venv\Scripts\glass.exe resume --run C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate648_reentry_boundary\runs_20260625_200000\candidate_boundary_strict --candidate-run C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary --out C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_gate648_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_gate648_regression_gate.md --max-elapsed-ratio 1.2 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.json --glass-time-seconds 11.485255 --reference-time-seconds 1092.541 --glass-label GLASS_gate649_resident_calibration_boundary_reentry --reference-label WBPP_blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --clip-low 0 --clip-high 1 --diagnostics-dir C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare_diagnostics --ignore-border-px 0 --glass-coverage-map C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.01 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\warp_quality_contract.json --require-warp-quality-contract
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary --acceptance-audit C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.01 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\glass.exe doctor --json C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident boundary/resume tests: `9 passed in 0.48 s`.
- Ruff over touched Python files and tests: passed.
- Full pytest: `1361 passed in 60.33 s`.

## Regression And Acceptance Results

- Resident regression gate versus Gate648: passed.
- Candidate/baseline elapsed ratio: `0.9899309067228078`.
- Determinism summary: `0` artifact differences, `0` frame-accounting differences, `0` frame-signature differences, `0` output differences, and `0` registration differences.
- WBPP compare:
  - reference elapsed: `1092.541 s`;
  - GLASS elapsed: `11.485255 s`;
  - speedup: `95.12553269387574x`;
  - coverage fraction: `0.9749333995120938`;
  - compared pixels: `60105814`;
  - RMS difference: `0.005624135079195954`;
  - p99 absolute difference: `0.0021429822302888963`.
- Acceptance audit: passed, speedup `95.12553269140832x`.
- Phase 2 mainline audit: passed.

## CUDA

- CUDA available: yes.
- CUDA native extension loaded: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Package recommendation: `cuda`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\resident_resume_reentry.json`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\resident_resume_preflight.json`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\candidate_from_calibration_boundary\resident_reentry_boundary.json`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_gate648_regression_gate.json`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.json`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_vs_wbpp_compare.html`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.json`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_phase2_mainline_audit.json`
- `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_doctor.json`

## Known Limitations

- Boundary reentry currently invokes the stored resident CUDA run command and relies on shared master-cache reuse.
- Calibrated light pixels are still VRAM-resident during the heavy stage and are not persisted as a restartable mid-stage cache.
- True continuation from an interrupted calibration/registration/integration sub-step remains future work.
- The largest measured stage remains `resident_calibration_integration` at `9.839130699983798 s`; within it the largest resident components are `light_read_upload_calibrate` at `3.5132379999849945 s` and `resident_integration` at `3.2337921999860555 s`.

## Next Step

Return to the substantive hot path: reduce resident calibration read/upload/calibrate time, reduce resident integration time, or split resident calibration/admission so more work survives a boundary reentry.

## Clean-Room Compliance

- This gate uses GLASS-owned resume state, GLASS artifacts, user-owned real data, and user-generated black-box reference outputs.
- No external/proprietary implementation source was read, copied, summarized, or reworked.
- Input image directories were treated as read-only.
