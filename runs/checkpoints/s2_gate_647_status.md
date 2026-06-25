# S2-Gate 647 Status: Resident Pre-Integration Reentry

## Gate

- Gate: S2-Gate 647
- Status: passed
- Date: 2026-06-25
- Objective: make resident resume perform a conservative real reentry when a
  resident CUDA run stopped before `resident_calibration_integration`, using a
  machine-readable stored run invocation instead of falling back to CPU/tile
  resume or requiring a full manual restart.

## Completed

- `glass run` now writes `run_invocation.json` with argv, subcommand, cwd, and
  the human-readable command string remains in `run_command.txt`.
- Resident resume preflight now records a `reentry` block with eligibility,
  reasons, stored invocation, and whether `resident_calibration_integration`
  has already started.
- `glass resume` now supports `resume_action=reenter_from_run_invocation`.
- Reentry is allowed only when:
  - the stored invocation is a `run` command;
  - stored `--out` resolves to the current run directory;
  - `run_state.failed_stage` is empty;
  - `resident_calibration_integration` has not started.
- Reentry writes `resident_resume_reentry.json`.
- After successful reentry, `glass resume` rewrites the resident stage ledger and
  preflight, records reentry artifacts in `run_state.json`, and ends with final
  `resume_action=noop_complete`.
- Added focused test coverage for the stored-invocation reentry path.
- Updated Phase 2 hardening docs, validation notes, and algorithm-source log.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_resume.py src\glass\engine\resident_stage_ledger.py src\glass\cli.py tests\test_resident_resume.py tests\test_resident_stage_ledger.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_resume.py tests/test_resident_stage_ledger.py
.\.venv\Scripts\glass.exe resume --run C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate646_resident_stage_ledger\runs_20260625_183731\candidate_stage_ledger_strict --candidate-run C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout --out C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_vs_gate646_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_vs_gate646_regression_gate.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_vs_wbpp_compare.html --glass-time-seconds 11.2256182001438 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout\warp_quality_contract.json --require-warp-quality-contract
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout --acceptance-audit C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_mainline_audit.md --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli doctor --json C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_doctor.json --allow-cpu-only
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident resume/stage-ledger tests: `5 passed`.
- Ruff: all touched files passed.
- Full pytest: `1355 passed in 59.92 s`.

## Real 200-Light Validation

- Partial skeleton:
  `C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout`.
- Initial skeleton state: `resident_reference_scout` completed;
  `resident_calibration_integration` not started.
- Initial resume action: `reenter_from_run_invocation`.
- Reentry artifact:
  `C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout\resident_resume_reentry.json`.
- Reentry status: passed, exit code `0`.
- Final resume action: `noop_complete`.
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_ab_summary.json`.
- GLASS elapsed after reentry: `11.2256182001438 s`.
- Resident calibration/integration stage: `9.59789230010938 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `97.325686703473x`.
- Frame accounting: `200` planned lights, `193` integrated frames, `7` masked
  frames.
- Resident stage ledger: started stages `15`, complete stages `15`, expected
  artifact rows `23`, missing artifact rows `0`, `can_noop_resume=true`.
- Resident regression versus Gate646: passed, elapsed ratio
  `0.8885626915461112`.
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

- `run_invocation.json`
- `resident_resume_reentry.json`
- `resident_resume_preflight.json`
- `resident_stage_ledger.json`
- `gate647_vs_gate646_regression_gate.json`
- `gate647_vs_wbpp_compare.json`
- `gate647_acceptance_audit.json`
- `gate647_mainline_audit.json`
- `gate647_ab_summary.json`
- `gate647_doctor.json`

## Known Limitations

- Reentry is pre-integration only. If `resident_calibration_integration` has
  started or failed, resume still blocks.
- The next checkpoint boundary inside the heavy CUDA resident stage is not yet
  implemented.

## Next Step

- Add a safe checkpoint/reentry boundary inside `resident_calibration_integration`,
  starting with resident master-cache reuse and calibration/admission evidence.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned run invocation, stage ledger, and resume
  semantics plus user-owned benchmark outputs.
- No external/proprietary implementation source was read, copied, summarized, or
  reworked.
- Input image directories were treated as read-only.
