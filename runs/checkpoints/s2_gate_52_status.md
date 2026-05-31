# S2 Gate 52 Status: Resident Grid Catalog Bitonic Shared Sort

## Gate
- Gate: S2-Gate 52
- Name: Resident grid catalog bitonic shared sort
- Status: green
- Completed at: 2026-06-01 Asia/Shanghai

## Completed Content
- Replaced the resident grid/NMS catalog shared-memory odd-even sort with a shared bitonic sort for grid capacities up to 4096.
- Preserved the GLASS catalog ordering comparator: flux descending, then y ascending, then x ascending.
- Added `catalog_sort_mode` diagnostics to native results, the Python wrapper, resident per-frame warnings, `resident_artifacts.json`, and HTML resident summary rows.
- Added a CPU-reference CUDA catalog test for a non-power-of-two grid capacity.
- Updated Phase 2 gate documentation and algorithm source notes.

## Commands Run
- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_keeps_spatial_candidates tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_matches_cpu_reference_for_non_power2_capacity tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_tie_breaks_saturated_plateau_deterministically tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\s2_gate_52_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 23.71175550017506 --reference-time-seconds 1092.541 --glass-label GLASS-S2G52-resident-catalog-bitonic --reference-label WBPP-blackbox`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\s2_gate_52_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\phase2_contract_acceptance_audit_s2_gate_52.json --markdown C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\phase2_contract_acceptance_audit_s2_gate_52.md --min-active-frames 190 --min-speedup 2.0`
- `.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\phase2_contract_acceptance_audit_s2_gate_52.json --out C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\s2_gate_52_report.html`

## Test Results
- Native CUDA build: passed
- Ruff: passed
- Focused pytest: `5 passed in 2.08s`
- Full pytest: `262 passed in 11.27s`
- 200-light contract audit: passed

## CUDA
- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## 200-Light Benchmark
- Dataset: M38 H, 200 light frames, 20 bias, 20 dark, 20 flat
- GLASS run: `C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601`
- GLASS elapsed: 23.71175550017506 s (`run_timing.json`)
- Measured process wall time: 24.0366228 s
- WBPP black-box reference elapsed: 1092.541 s
- Speedup vs WBPP black-box reference: 46.0759221303515x
- Active/integrated frames: 193/200
- Excluded zero-weight frames: 7
- Coverage fraction: 0.9574613308418977
- RMS difference vs WBPP reference: 0.001558294284488301
- P99 absolute difference vs WBPP reference: 0.00043095467146486016
- Estimated peak resident memory: 47.3117358982563 GiB

## Resident Catalog Timing
- Catalog sort mode: `shared_bitonic_power2`
- `triangle_moving_catalog_batch`: 5.2614773996174335 s
- `triangle_moving_catalog_native_sync`: 5.2315108 s
- `triangle_moving_catalog_native_total`: 5.2523278 s
- Gate51 comparison: `triangle_moving_catalog_batch` was 5.3614857997745275 s, so this gate improved catalog batch time by about 0.10 s on the 200-light run.
- Total run time was slightly slower than Gate51 in this single run, likely due to normal I/O/write/runtime variance; it remains faster than the Phase 1 release runtime envelope and passes the benchmark contract.

## Artifacts
- Compare report: `C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\s2_gate_52_compare.html`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\s2_gate_52_compare.json`
- Acceptance JSON: `C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\phase2_contract_acceptance_audit_s2_gate_52.json`
- Acceptance markdown: `C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\phase2_contract_acceptance_audit_s2_gate_52.md`
- HTML report: `C:\glass_runs\phase2_s2_gate_52_200\resident_catalog_bitonic_20260601\s2_gate_52_report.html`

## Known Limitations
- The optimization only replaces the shared-memory sort for grid capacities up to 4096 candidates.
- Larger grid capacities still use the previous single-thread selection-sort fallback.
- The remaining catalog cost is still dominated by the full-frame local-maximum/grid top-k scan and per-cell atomic locks.
- Local normalization remains off for the benchmark contract.

## Next Step
- S2-Gate53 should target the full-frame grid top-k kernel itself, likely by reducing per-local-maximum lock contention or by introducing a two-stage block-local candidate reduction before per-cell merge.

## Clean-Room Compliance
- Compliant. This gate changed only GLASS-owned CUDA sorting code and used GLASS tests/artifacts plus user-generated benchmark/reference outputs.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or reworked.
