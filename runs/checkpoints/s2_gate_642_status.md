# S2-Gate 642 Status: Source-DQ Positive Mainline Gate

## Gate

- Gate: S2-Gate 642
- Status: passed
- Date: 2026-06-25
- Objective: keep Phase 2 on the substantive DQ/mask mainline by making a
  resident strict run able to require nonzero source-DQ invalid samples to be
  resident-applied and visible in integration provenance.

## Completed

- Extended `resident_mainline_framework.json` with `framework_scope`.
- Added `source_dq_positive` scope for positive source-DQ fixtures.
- Added strict thresholds:
  `--resident-mainline-min-source-dq-invalid-samples` and
  `--resident-mainline-min-source-dq-applied-samples`.
- Added source-DQ summary extraction from `resident_source_dq_execution.json`.
- Added explicit mainline checks for required source-DQ artifact presence,
  pass status, invalid sample count, and applied sample count.
- Added CLI support for `glass run` and `glass audit`.
- Added focused unit coverage and tightened the resident CUDA source-DQ cache
  test so strict mainline closure must pass when source-DQ samples are expected.
- Updated Phase 2 docs, validation summary, and algorithm-source independence
  log.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_mainline_framework.py src\glass\cli.py tests\test_resident_mainline_framework.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe synthetic --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\synthetic_source_dq_positive --frames 4 --width 64 --height 64 --filter H --known-shift --source-dq-sidecars --source-dq-light-index 1 --source-dq-y 20 --source-dq-x 21
.\.venv\Scripts\glass.exe scan --root C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\synthetic_source_dq_positive --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\manifest.json
.\.venv\Scripts\glass.exe plan --manifest C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\manifest.json --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\processing_plan.json --source-dq-manifest C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\synthetic_source_dq_positive\source_dq_manifest.json
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\processing_plan.json --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\resident_source_dq_positive_translation_strict --backend cuda --memory-mode resident --resident-runtime-preset manual --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --resident-registration translation_preview --resident-prefetch-frames 2 --resident-prefetch-workers 2 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 2 --resident-calibration-streams 2 --resident-output-maps audit --resident-mainline-framework-gate strict --resident-mainline-framework-scope source_dq_positive --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --tile-size 32
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_vs_wbpp_compare.html --glass-time-seconds 11.854997799731791 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate641_mainline_framework\runs_20260625_1641\candidate_mainline_framework_strict --candidate-run C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_vs_gate641_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_vs_gate641_regression_gate.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict\warp_quality_contract.json --require-warp-quality-contract
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict --acceptance-audit C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_mainline_audit.md --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli doctor --json C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\doctor_after.json --allow-cpu-only
```

## Test Results

- Focused source-DQ/mainline pytest: `10 passed in 3.05 s`.
- Full pytest: `1348 passed in 60.55 s`.
- Ruff: all touched files passed.

## Synthetic Positive Source-DQ Validation

- Run:
  `C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\resident_source_dq_positive_translation_strict`.
- `resident_mainline_framework.json`: passed.
- `resident_source_dq_execution.json`: passed.
- `pipeline_contract.json`: passed.
- `warp_quality_contract.json`: passed.
- Source-DQ route: `resident_in_memory_mask_streaming`.
- Invalid samples before rejection: `1`.
- Applied invalid samples: `1`.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\candidate_default_strict`.
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate642_source_dq_positive_mainline\runs_20260625_165708\gate642_ab_summary.json`.
- `resident_mainline_framework.json`: passed, no failed checks.
- GLASS elapsed: `11.854997799731791 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `92.15868433351525x`.
- Resident calibration/integration stage: `9.52495039999485 s`.
- Frame accounting: `200` planned lights, `193` integrated frames, `7`
  zero-weight/masked frames.
- Resident regression versus Gate641: passed, elapsed ratio
  `0.9984591805032615`.
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
- `resident_source_dq_execution.json`
- `pipeline_contract.json`
- `stack_engine_contract.json`
- `warp_quality_contract.json`
- `gate642_vs_wbpp_compare.json`
- `gate642_vs_gate641_regression_gate.json`
- `gate642_acceptance_audit.json`
- `gate642_mainline_audit.json`
- `gate642_ab_summary.json`
- `doctor_after.json`

## Known Limitations

- The real M38 200-light dataset has zero nonzero source-DQ sidecar invalid
  samples, so positive source-DQ behavior is validated with a targeted
  synthetic resident run.
- Gate642 changes resident framework/postcondition enforcement and tests; it
  does not change calibration, registration, warp, local normalization,
  rejection, or CUDA pixel math.
- The largest measured real-data stage remains resident calibration/integration.

## Next Step

- Continue with a substantive Phase 2 mainline gate: default StackEngine
  execution/DQ mask surface coverage, or measured resident
  calibration/registration batching with 200-light regression evidence.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned artifact schemas, tests, synthetic
  fixtures, runtime contracts, and user-owned benchmark/reference outputs.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
