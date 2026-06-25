# S2-Gate 646 Status: Resident Stage Ledger

## Gate

- Gate: S2-Gate 646
- Status: passed
- Date: 2026-06-25
- Objective: centralize resident CUDA stage/artifact expectations in a reusable
  stage ledger, make resident `run`/`audit` write that ledger, and make
  resident `resume` consume the same ledger before deciding whether a completed
  run can safely no-op.

## Completed

- Added `src/glass/engine/resident_stage_ledger.py`.
- Defined one `RESIDENT_STAGE_ARTIFACTS` table for resident stages and required
  artifacts.
- Resident `run` and resident `audit` now write `resident_stage_ledger.json`
  after resident postcondition artifacts.
- Resident `resume` now writes and consumes `resident_stage_ledger.json` before
  writing `resident_resume_preflight.json`.
- `run_state.json` records `resident_stage_ledger.json` for completed resident
  runs and for resume preflight.
- Added focused tests for:
  - missing artifact detection for a started resident stage;
  - overlapping artifact safety, so a shared file does not falsely start a
    stage;
  - completed resident resume no-op through the ledger;
  - incomplete resident resume blocking the legacy CPU/tile fallback.
- Updated Phase 2 hardening docs, validation notes, and algorithm-source log.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_stage_ledger.py src\glass\engine\resident_resume.py src\glass\cli.py tests\test_resident_stage_ledger.py tests\test_resident_resume.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_stage_ledger.py tests/test_resident_resume.py
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10
.\.venv\Scripts\glass.exe resume --run C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict --candidate-run C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict --out C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_vs_gate644_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_vs_gate644_regression_gate.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_vs_wbpp_compare.html --glass-time-seconds 12.633456600131467 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict\warp_quality_contract.json --require-warp-quality-contract
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict --acceptance-audit C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_mainline_audit.md --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli doctor --json C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_doctor.json --allow-cpu-only
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident stage-ledger/resume tests: `4 passed`.
- Ruff: all touched files passed.
- Full pytest: `1354 passed in 58.51 s`.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict`.
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\gate646_ab_summary.json`.
- `resident_stage_ledger.json`: resident run true, started stages `15`,
  complete stages `15`, expected artifact rows `23`, missing artifact rows `0`,
  `can_noop_resume=true`.
- `glass resume`: exit code `0`, `resume_action=noop_complete`, no stages
  repeated.
- GLASS elapsed: `12.633456600131467 s`.
- Resident calibration/integration stage: `10.656172699993476 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `86.47997413381154x`.
- Frame accounting: `200` planned lights, `193` integrated frames, `7` masked
  frames.
- Resident regression versus Gate644: passed, elapsed ratio
  `1.1025927238327333`.
- Compare at coverage >= `190`: shape match true, RMS
  `0.0056241382952344435`, p99 absolute difference
  `0.002143551869085057`, coverage fraction `0.9749333995120938`, compared
  pixels `60105814`.
- Acceptance audit: passed.
- Phase 2 mainline audit: passed.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `resident_stage_ledger.json`
- `resident_resume_preflight.json`
- `gate646_vs_gate644_regression_gate.json`
- `gate646_vs_wbpp_compare.json`
- `gate646_acceptance_audit.json`
- `gate646_mainline_audit.json`
- `gate646_ab_summary.json`
- `gate646_doctor.json`

## Known Limitations

- This gate centralizes stage/artifact expectations and supports completed-run
  no-op resume.
- It does not yet implement partial resident re-entry from an interrupted
  calibration/integration stage.
- Pixel math was not changed; the speed delta versus Gate644 is treated as run
  variance and stayed within the regression gate threshold.

## Next Step

- Use `resident_stage_ledger.json` to define explicit partial re-entry points
  inside `resident_calibration_integration`, beginning with master-cache reuse
  and resident calibrated-frame/admission boundaries.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned runtime artifacts, GLASS stage/accounting
  semantics, and user-owned benchmark outputs.
- No external/proprietary implementation source was read, copied, summarized, or
  reworked.
- Input image directories were treated as read-only.
