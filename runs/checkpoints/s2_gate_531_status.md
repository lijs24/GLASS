# S2-Gate 531 Status: Resident Triangle Catalog 8-Stream Fanout

- Gate: S2-Gate 531
- Status: green
- Completed at: 2026-06-23T04:30:22.787723+00:00
- Scope: resident CUDA registration scheduling, not report-only evidence handoff

## Completed

- Raised native batched grid/NMS star-catalog stream fanout cap from 4 to 8.
- Added `catalog_stream_limit` to native catalog results and `triangle_catalog_stream_limit` to resident artifacts.
- Updated focused CUDA resident catalog tests and Phase 2 algorithm/source documentation.
- Rebuilt the native extension in Release mode with Visual Studio BuildTools and CUDA 13.2.

## Real 200-Light Validation

- Dataset: M38 H-alpha, 200 light + 20 bias + 20 dark + 20 flat.
- Baseline run: `C:\glass_runs\phase2_mainline_real_200_ab_current\runs_20260623_122002\glass_current_default`
- Candidate run: `C:\glass_runs\phase2_s2_gate531_catalog_stream8_real\runs_20260623_122624\catalog_stream8_repeat`
- Baseline internal/shell: `5.721311400004197 s` / `6.088693 s`
- Candidate internal/shell: `5.650653899996541 s` / `6.001961 s`
- Registration component: `1.8479182995140835 s` -> `1.530751099891913 s`
- Catalog native sync: `0.23199929999999996 s` -> `0.1254431 s`
- Candidate artifact records `triangle_catalog_stream_limit=8` and `triangle_catalog_stream_count=8`.

## Numerical Validation

- Six audit maps are bitwise identical to the previous default: master, weight, coverage, low rejection, high rejection, DQ.
- Bitwise compare JSON: `C:\glass_runs\phase2_s2_gate531_catalog_stream8_real\runs_20260623_122624\catalog_stream8_repeat\gate531_bitwise_vs_previous_default.json`
- Scaled compare JSON: `C:\glass_runs\phase2_s2_gate531_catalog_stream8_real\runs_20260623_122624\catalog_stream8_repeat\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance audit JSON: `C:\glass_runs\phase2_s2_gate531_catalog_stream8_real\runs_20260623_122624\catalog_stream8_repeat\acceptance_audit_scaled.json`
- Acceptance status: passed
- Coverage fraction: `0.9892770479074376`
- RMS diff: `0.0004279821839256963`
- abs diff p99: `0.0001313822576776147`
- Internal speedup vs WBPP black-box `1092.541 s`: `193.3477114924113x`

## Commands Run

- Native Release build through CMake/Ninja/Visual Studio BuildTools.
- Focused tests: `python -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- Real run: `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident ... --resident-output-maps audit`
- Compare: `glass compare ... --min-coverage 190 --glass-scale 1.545301547671945e-05 --glass-offset=-9.765786009702931e-05`
- Speedup: `glass speedup-summary --min-speedup 2.0`
- Acceptance: `glass acceptance-audit --min-active-frames 190 --min-speedup 2.0 --max-rms-diff 0.01 --max-abs-diff-p99 0.01`
- Full tests: `python -m pytest -q`
- Doctor: `glass doctor`

## Test Results

- Focused tests: `2 passed in 0.46s`
- Full pytest: `1174 passed in 43.24s`
- Doctor: CUDA available; GPU 0 NVIDIA RTX PRO 6000 Blackwell Workstation Edition, cc 12.0, VRAM 97886 MiB, driver 596.21.

## CUDA Availability

CUDA is available and the native extension is loaded. The gate remains optional-CUDA safe: CPU-only tests are not dependent on this native path, and CUDA tests skip when CUDA is unavailable.

## Known Limitations

- The remaining registration/warp bottleneck is batched Lanczos3 warp sync around `0.47 s`.
- The stream fanout is a scheduling optimization validated on the local RTX PRO 6000 Blackwell; lower-end GPUs may show different timing while preserving output identity.
- Scaled WBPP compare is used because GLASS and WBPP masters differ by output normalization scale.

## Next Step

Target resident Lanczos3 warp sync and deeper catalog/descriptor/warp residency overlap.

## Clean-Room

Compliant. This gate uses GLASS code, GLASS-generated artifacts, and user-generated WBPP black-box timing/reference outputs only. No official WBPP/PJSR source was read or copied.
