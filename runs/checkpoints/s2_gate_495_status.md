# S2 Gate 495 Status: Resident CUDA Isolated Cosmetic Source-DQ

## Gate

S2-Gate 495: port the Gate494 structure-aware isolated cosmetic source-DQ
baseline to resident CUDA for opt-in `cosmetic_cuda`.

## Completed

- Added resident CUDA isolated cosmetic count/apply kernels for single frames
  and frame batches.
- Exposed Python/native APIs:
  - `ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frame`
  - `ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frame`
  - `ResidentCalibratedStack.apply_isolated_cosmetic_threshold_mask_frames`
  - `ResidentCalibratedStack.count_isolated_cosmetic_threshold_mask_frames`
- Routed `--resident-inline-source-dq cosmetic_cuda` through the isolated CUDA
  detector while preserving old scalar threshold APIs for compatibility.
- Recorded candidate/protected hot/cold counts, structure parameters, native
  method names, and isolated detector execution in source-DQ artifacts.
- Fixed the high-fraction guard continuation path so count-only rows below the
  guard threshold continue into apply instead of returning incomplete rows.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native
Copy-Item -LiteralPath src\Release\_glass_cuda_native.cp312-win_amd64.pyd -Destination src\_glass_cuda_native.cp312-win_amd64.pyd -Force
.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq_strategy.py src\glass_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq_strategy.py src\glass_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_isolated_cosmetic_threshold_count_matches_cpu_without_modifying_pixels tests\test_cuda_resident_stack.py::test_resident_stack_isolated_cosmetic_threshold_apply_protects_star_core tests\test_cuda_resident_stack.py::test_resident_stack_isolated_cosmetic_threshold_batch_apply tests\test_resident_source_dq.py::test_inline_cosmetic_thresholds_match_cpu_baseline_scalar_thresholds tests\test_resident_source_dq.py::test_apply_resident_inline_cosmetic_thresholds_batch_records_batch_native_route tests\test_resident_source_dq.py::test_apply_resident_inline_cosmetic_thresholds_batch_skips_high_invalid_fraction tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_skips_inline_cosmetic_cuda_high_fraction_guard
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_defers_inline_cosmetic_cuda_source_dq_until_after_registration
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_stack_engine_contract.md --expected-integration-engine cuda_resident_stack --require-default-ready
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate494_structure_cosmetic_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\compare\ab_current_vs_gate494_master.html --glass-label GLASS-Gate495 --reference-label GLASS-Gate494
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.html --glass-label GLASS-Gate495 --reference-label WBPP-fastIntegration --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.md --min-speedup 20
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\manifest.json --glass-run C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\acceptance\ab_current_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\acceptance\ab_current_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --pipeline-contract-json C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_stack_engine_contract.json
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\reports\ab_current_report.html --compare-json C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\acceptance\ab_current_acceptance_audit.json --pipeline-contract C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_pipeline_contract.json --stack-engine-contract C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\contracts\ab_current_stack_engine_contract.json
git diff --check
```

## Test Results

- Focused CUDA/source-DQ/CLI tests: `8 passed`.
- Deferred registration source-DQ focused test after expectation update:
  `1 passed`.
- Full test suite: `1141 passed in 41.41 s`.
- `py_compile`, `ruff check`, native CUDA build, and `git diff --check`
  passed.

## CUDA Status

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- Driver: `596.21`.
- VRAM: `97886 MiB`.

## Real 200-Light A/B

- Dataset plan:
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current`.
- GLASS elapsed: `17.566973500011954 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup vs WBPP: `62.192898509197185x`.
- Active/weighted frames: `193 / 200`.
- GLASS-vs-Gate494 master difference: RMS `0.0`, p99 `0.0`, max `0.0`.
- GLASS-vs-WBPP compare at coverage >= `190`:
  - RMS `0.0017794216505176163`
  - p99 abs diff `0.00042621337808668863`
  - coverage fraction `0.960532609259836`
  - compared pixels `59217988`
- Pipeline contract: passed.
- StackEngine contract: passed.
- Acceptance audit: passed.

## Artifacts

- Gate495 run:
  `C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current`.
- Gate494 compare:
  `C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\runs\default_runtime_stack_ab_current\compare\ab_current_vs_gate494_master.json`.
- WBPP compare:
  `C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json`.
- Speedup summary:
  `C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.json`.
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\acceptance\ab_current_acceptance_audit.json`.
- HTML report:
  `C:\glass_runs\phase2_s2_gate495_isolated_cuda_ab_real\reports\ab_current_report.html`.

## Disk / Cleanup Note

- C: free space before final checkpoint was about `285.51 GiB`.
- No project or historical run directories were deleted in this gate.
- The repository itself remains small compared with `C:\glass_runs` and
  `C:\gpwbpp_runs`; if space pressure returns, old sweep/run artifacts are the
  safe cleanup candidates, not input data or WBPP black-box references.

## Known Limitations

- `cosmetic_cuda` is still opt-in. The default production route keeps inline
  source-DQ off.
- The isolated detector is a conservative hot/cold defect heuristic, not a full
  bad-pixel-map workflow and not a semantic star classifier.
- Local normalization remains off in the current 200-light A/B recipe.
- The old scalar threshold CUDA APIs remain for compatibility but are no
  longer the preferred `cosmetic_cuda` route.

## Next Step

Return to Phase 2 mainline optimization: resident registration/warp batching
and I/O/upload/calibration overlap, using the same 200-light A/B harness and
maintaining WBPP agreement thresholds.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned CPU baseline logic, GLASS CUDA code,
synthetic fixtures, user-owned image data, and user-generated WBPP black-box
timing/output artifacts only. It did not inspect or copy external
implementation source and did not modify input image directories.
