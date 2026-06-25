# S2-Gate 641 Status: Resident Mainline Framework Postcondition

## Gate

- Gate: S2-Gate 641
- Status: passed
- Date: 2026-06-25
- Objective: move Phase 2 mainline framework checks into the resident execution
  path so default resident `run`/`audit` can write a postcondition artifact and
  `strict` runs can fail on broken framework closure.

## Completed

- Added `src/glass/engine/resident_mainline_framework.py`.
- Added `resident_mainline_framework.json` postcondition artifact.
- Added `--resident-mainline-framework-gate off|warn|strict` to resident
  `glass run` and `glass audit`.
- Added per-run thresholds:
  `--resident-mainline-min-lights`,
  `--resident-mainline-min-active-frames`, and
  `--resident-mainline-max-masked-frames`.
- Refactored resident postconditions so `audit` now follows the same
  local-normalization, pipeline, StackEngine, warp-quality, and mainline
  framework contract chain as `run`.
- Added focused tests in `tests/test_resident_mainline_framework.py`.
- Updated resident CUDA timing-stage expectations for the new default
  postcondition stage.
- Updated `docs/phase2_algorithm_hardening.md`, `docs/validation.md`, and
  `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py tests/test_phase2_mainline_audit.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py -k "resident_run or help_commands or resident_mainline or guardrails_auto_discovers or report_includes_resident"
.\.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\engine\resident_mainline_framework.py tests\test_resident_mainline_framework.py
.\.venv\Scripts\python.exe -m glass.cli doctor --json C:\glass_runs\phase2_s2_gate641_mainline_framework\doctor_before.json --allow-cpu-only
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_vs_wbpp_compare.html --glass-time-seconds 11.873292400152422 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate640_reference_health_reuse\runs_20260625_161859\candidate_reference_health_reuse --candidate-run C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict --out C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_vs_gate640_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_vs_gate640_regression_gate.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict\warp_quality_contract.json --require-warp-quality-contract
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict --acceptance-audit C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\gate641_mainline_audit.md --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident mainline tests: `5 passed`.
- Focused mainline/CLI resident tests: `29 passed, 60 deselected`.
- Full pytest: `1345 passed in 58.46 s`.
- Ruff: all touched files passed.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict`.
- `resident_mainline_framework.json`: passed, strict gate did not block.
- GLASS elapsed: `11.873292400152422 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `92.0166844359004x`.
- Frame accounting: `200` planned lights, `193` active frames, `7` masked
  frames.
- Resident calibration/integration stage: `9.586103999987245 s`.
- Resident integration component: `3.241891600075178 s`.
- Resident regression versus Gate640: passed, elapsed ratio
  `0.9981213621153441`, no failed checks.
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

- `resident_mainline_framework.json`
- `run_timing.json`
- `run_state.json`
- `resident_artifacts.json`
- `pipeline_contract.json`
- `stack_engine_contract.json`
- `warp_quality_contract.json`
- `gate641_vs_gate640_regression_gate.json`
- `gate641_vs_wbpp_compare.json`
- `gate641_acceptance_audit.json`
- `gate641_mainline_audit.json`

## Known Limitations

- Gate641 changes runtime contract closure, not image math or CUDA kernels.
- `resident_mainline_framework.json` does not embed external acceptance or
  compare evidence; those remain separate acceptance/mainline audit artifacts.
- The largest measured stage remains resident calibration/integration.
- The M38 real dataset has no nonzero source-DQ invalid samples, so richer
  source-DQ behavior still needs synthetic plus targeted real validation.

## Next Step

- Return to Phase 2 substantive execution work: resident calibration/integration
  hot path, resident calibrated-reference-health reuse, or nonzero source-DQ/mask
  pipeline validation.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned artifact schemas, runtime contract
  checks, tests, and user-owned benchmark/reference outputs.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
