# S2-Gate 643 Status: StackEngine DQ Runtime Postcondition

## Gate

- Gate: S2-Gate 643
- Status: passed
- Date: 2026-06-25
- Objective: move StackEngine default-readiness and DQ-ledger readiness from
  a separately inspected contract into the resident mainline strict
  postcondition, so default resident runs cannot pass while StackEngine/DQ
  runtime evidence is regressed.

## Completed

- Extended `resident_mainline_framework.json` with a normalized
  `stack_engine` summary from `stack_engine_contract.json`.
- Added hard resident-mainline checks for:
  - StackEngine contract presence;
  - top-level StackEngine contract pass status;
  - StackEngine `default_promotion.ready`;
  - zero Phase 2 StackEngine default gaps;
  - master-calibration plus integration surface coverage;
  - pipeline DQ ledger readiness when resident StackEngine surfaces require it.
- Added focused negative tests proving strict mode blocks StackEngine default
  gaps and failed pipeline DQ ledger readiness.
- Tightened the resident CUDA source-DQ cache route test so real CLI execution
  must pass the new StackEngine checks.
- Updated Phase 2 documentation, validation summary, and algorithm-source
  independence log.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_mainline_framework.py tests\test_resident_mainline_framework.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py tests/test_phase2_mainline_audit.py tests/test_stack_engine_contract.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route tests/test_cli_smoke.py::test_cli_help_commands tests/test_cli_smoke.py::test_cli_report_summarizes_stack_engine_contract
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_mainline_framework.py tests\test_resident_mainline_framework.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route tests/test_stack_engine_contract.py
.\.venv\Scripts\glass.exe synthetic --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\synthetic_source_dq_stackengine --frames 4 --width 64 --height 64 --filter H --known-shift --source-dq-sidecars --source-dq-light-index 1 --source-dq-y 20 --source-dq-x 21
.\.venv\Scripts\glass.exe scan --root C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\synthetic_source_dq_stackengine --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\manifest.json
.\.venv\Scripts\glass.exe plan --manifest C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\manifest.json --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\processing_plan.json --source-dq-manifest C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\synthetic_source_dq_stackengine\source_dq_manifest.json
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\processing_plan.json --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\resident_source_dq_stackengine_strict --backend cuda --memory-mode resident --resident-runtime-preset manual --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration translation_preview --resident-prefetch-frames 2 --resident-prefetch-workers 2 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 2 --resident-calibration-streams 2 --resident-output-maps audit --resident-mainline-framework-gate strict --resident-mainline-framework-scope source_dq_positive --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --tile-size 32
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_vs_wbpp_compare.html --glass-time-seconds 11.895962899900042 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict --candidate-run C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_vs_gate642_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_vs_gate642_regression_gate.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict\warp_quality_contract.json --require-warp-quality-contract
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict --acceptance-audit C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_mainline_audit.md --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli doctor --json C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\doctor_after.json --allow-cpu-only
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident-mainline, StackEngine contract, and resident CUDA tests:
  `28 passed`.
- Full pytest: `1350 passed in 60.17 s`.
- Ruff: all touched files passed.

## Synthetic StackEngine/DQ Validation

- Run:
  `C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\resident_source_dq_stackengine_strict`.
- `resident_mainline_framework.json`: passed.
- Source-DQ invalid/applied samples: `1 / 1`.
- StackEngine default promotion ready: `true`.
- StackEngine pipeline DQ ledger ready: `true`.
- StackEngine default gap count: `0`.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict`.
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\gate643_ab_summary.json`.
- `resident_mainline_framework.json`: passed, no failed checks.
- StackEngine runtime evidence: default promotion ready `true`, pipeline DQ
  ledger ready `true`, default gap count `0`, surface count `4`.
- GLASS elapsed: `11.895962899900042 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `91.84132543059464x`.
- Resident calibration/integration stage: `9.4771528999554 s`.
- Frame accounting: `200` planned lights, `193` integrated frames, `7`
  zero-weight/masked frames.
- Resident regression versus Gate642: passed, elapsed ratio
  `1.0034555130975373`.
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
- Package guidance from doctor: try `cuda13`, then `cuda12`, `cuda11`, then
  `cpu`.

## Artifacts

- `resident_mainline_framework.json`
- `stack_engine_contract.json`
- `pipeline_contract.json`
- `resident_source_dq_execution.json`
- `gate643_synthetic_summary.json`
- `gate643_vs_wbpp_compare.json`
- `gate643_vs_gate642_regression_gate.json`
- `gate643_acceptance_audit.json`
- `gate643_mainline_audit.json`
- `gate643_ab_summary.json`
- `doctor_after.json`

## Known Limitations

- Gate643 hardens runtime postconditions and tests; it does not change
  calibration, registration, warp, local normalization, rejection, or CUDA
  pixel math.
- The largest measured real-data stage remains resident calibration/integration.
- More work is still required to move additional execution surfaces into the
  unified StackEngine path and reduce resident orchestration overhead.

## Next Step

- Continue with a substantive execution gate: either reduce resident
  calibration/registration orchestration under 200-light regression, or move
  another legacy/default surface into StackEngine execution with DQ/mask
  provenance and CPU/CUDA parity tests.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned StackEngine, resident CUDA, pipeline
  DQ, and mainline artifact schemas, tests, synthetic fixtures, and user-owned
  benchmark/reference outputs.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
