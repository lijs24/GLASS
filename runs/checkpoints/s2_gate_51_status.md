# S2 Gate 51 Status: Resident Grid Catalog Timing Decomposition

## Gate
- Gate: S2-Gate 51
- Name: Resident grid catalog timing decomposition
- Status: green
- Completed at: 2026-06-01 Asia/Shanghai

## Completed Content
- Added native timing decomposition for resident grid/NMS star catalog batch extraction.
- Propagated timing fields through the `glass_cuda` wrapper, resident CUDA engine artifacts, per-frame warnings, and HTML report rows.
- Added regression tests for native batch catalog timing fields and resident triangle registration artifact propagation.
- Updated Phase 2 algorithm plan and algorithm source notes.

## Commands Run
- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\s2_gate_51_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 23.048557700123638 --reference-time-seconds 1092.541 --glass-label GLASS-S2G51-resident-catalog-timing --reference-label WBPP-blackbox`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\s2_gate_51_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\phase2_contract_acceptance_audit_s2_gate_51.json --markdown C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\phase2_contract_acceptance_audit_s2_gate_51.md --min-active-frames 190 --min-speedup 2.0`
- `.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\phase2_contract_acceptance_audit_s2_gate_51.json --out C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\s2_gate_51_report.html`

## Test Results
- Native CUDA build: passed (`ninja: no work to do`)
- Ruff: passed
- Focused pytest: `2 passed in 2.29s`
- Full pytest: `261 passed in 11.16s`
- 200-light contract audit: passed

## CUDA
- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## 200-Light Benchmark
- Dataset: M38 H, 200 light frames, 20 bias, 20 dark, 20 flat
- GLASS run: `C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601`
- GLASS elapsed: 23.048557700123638 s (`run_timing.json`)
- Measured process wall time: 23.3580396 s
- WBPP black-box reference elapsed: 1092.541 s
- Speedup vs WBPP black-box reference: 47.40170791659295x
- Active/integrated frames: 193/200
- Excluded zero-weight frames: 7
- Coverage fraction: 0.9574613308418977
- RMS difference vs WBPP reference: 0.001558294284488301
- P99 absolute difference vs WBPP reference: 0.00043095467146486016

## Resident Catalog Timing Findings
- `triangle_moving_catalog_batch`: 5.3614857997745275 s
- `triangle_moving_catalog_native_total`: 5.3519441 s
- `triangle_moving_catalog_native_sync`: 5.3314358 s
- `triangle_moving_catalog_native_enqueue`: 0.0080857 s
- `triangle_moving_catalog_native_count_download`: 0.0082544 s
- `triangle_moving_catalog_native_output_download`: 0.0041682 s
- Conclusion: catalog extraction time is dominated by native GPU synchronization/kernel work, not Python orchestration or D2H catalog download.

## Artifacts
- Compare report: `C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\s2_gate_51_compare.html`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\s2_gate_51_compare.json`
- Acceptance JSON: `C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\phase2_contract_acceptance_audit_s2_gate_51.json`
- Acceptance markdown: `C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\phase2_contract_acceptance_audit_s2_gate_51.md`
- HTML report: `C:\glass_runs\phase2_s2_gate_51_200\resident_catalog_timing_20260601\s2_gate_51_report.html`

## Known Limitations
- Gate51 is diagnostic instrumentation only; it does not yet optimize the resident grid/NMS catalog kernel.
- Timing model remains per-frame launch/sync/download inside the native batch wrapper.
- Local normalization remains off for this benchmark contract.
- The 7 zero-weight frames remain explicitly excluded to match the established 200-light benchmark contract.

## Next Step
- S2-Gate52 should optimize the resident catalog GPU work itself: batch/grid-level NMS strategy, reduced full-frame scan cost, or persistent/resident candidate buffers with less per-frame device synchronization.

## Clean-Room Compliance
- Compliant. This gate used GLASS code, generated artifacts, user-owned test data, and user-generated WBPP black-box timing/output metadata only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or reworked.
