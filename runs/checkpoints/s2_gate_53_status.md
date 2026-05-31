# S2 Gate 53 Status: Resident Grid Top-K Strict Flux Precheck

## Gate
- Gate: S2-Gate 53
- Name: Resident grid top-k strict flux precheck
- Status: green
- Completed at: 2026-06-01 Asia/Shanghai

## Completed Content
- Added a resident CUDA grid top-k mode, `strict_flux_precheck_per_cell_lock`, to reduce per-cell lock contention during full-frame star catalog selection.
- Added a per-cell filled-slot counter so sparse cells continue through the locked insertion path until all `candidates_per_cell` slots can be filled.
- Preserved equal-flux and saturated-plateau tie handling by routing equal-flux candidates through the existing locked comparator.
- Surfaced `catalog_topk_mode` through native CUDA results, Python wrappers, resident registration warnings, `resident_artifacts.json`, and HTML report rows.
- Added CPU-reference, tie-break, resident batch/single equivalence, and resident registration smoke coverage for the top-k mode.
- Updated Phase 2 hardening docs and algorithm source notes.

## Commands Run
- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_keeps_spatial_candidates tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_matches_cpu_reference_for_non_power2_capacity tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_precheck_preserves_tie_breaks tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_tie_breaks_saturated_plateau_deterministically tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_triangle_descriptor_image_registration_supports_grid_top_selector tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_precheck_preserves_tie_breaks tests\test_gpu_registration_search.py::test_gpu_star_grid_top_nms_candidates_matches_cpu_reference_for_non_power2_capacity`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\s2_gate_53_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 18.619107900187373 --reference-time-seconds 1092.541 --glass-label GLASS-S2G53-resident-catalog-precheck --reference-label WBPP-blackbox`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\s2_gate_53_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\phase2_contract_acceptance_audit_s2_gate_53.json --markdown C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\phase2_contract_acceptance_audit_s2_gate_53.md --min-active-frames 190 --min-speedup 2.0`
- `.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\phase2_contract_acceptance_audit_s2_gate_53.json --out C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\s2_gate_53_report.html`

## Test Results
- Native CUDA build: passed
- Ruff: passed
- Focused pytest: `6 passed in 2.14s`; post-fix regression subset: `3 passed in 1.59s`
- Full pytest: `263 passed in 11.30s`
- 200-light contract audit: passed

## CUDA
- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB reported by GLASS, 97887 MiB reported by `nvidia-smi`
- Driver: 596.21

## 200-Light Benchmark
- Dataset: M38 H, 200 light frames, 20 bias, 20 dark, 20 flat
- GLASS run: `C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601`
- GLASS elapsed: 18.619107900187373 s (`run_timing.json`)
- Measured process wall time: 18.92812 s
- WBPP black-box reference elapsed: 1092.541 s
- Speedup vs WBPP black-box reference: 58.67848265646525x
- Active/integrated frames: 193/200
- Excluded zero-weight frames: 7
- Coverage fraction: 0.9602948685508149
- RMS difference vs WBPP reference: 0.0016497070845466818
- P99 absolute difference vs WBPP reference: 0.0004150900989770903
- Estimated peak resident memory: 47.3117358982563 GiB

## Resident Catalog Timing
- Catalog sort mode: `shared_bitonic_power2`
- Catalog top-k mode: `strict_flux_precheck_per_cell_lock`
- `triangle_moving_catalog_batch`: 1.0978165999986231 s
- `triangle_moving_catalog_native_sync`: 1.0685829 s
- `triangle_moving_catalog_native_total`: 1.0899369 s
- `triangle_moving_catalog_native_count_download`: 0.007444 s
- Gate52 comparison: `triangle_moving_catalog_batch` was 5.2614773996174335 s, so this gate improved moving-catalog batch time by about 4.16 s.
- Gate52 total comparison: total GLASS elapsed improved from 23.71175550017506 s to 18.619107900187373 s.

## Artifacts
- Compare report: `C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\s2_gate_53_compare.html`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\s2_gate_53_compare.json`
- Acceptance JSON: `C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\phase2_contract_acceptance_audit_s2_gate_53.json`
- Acceptance markdown: `C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\phase2_contract_acceptance_audit_s2_gate_53.md`
- HTML report: `C:\glass_runs\phase2_s2_gate_53_200\resident_catalog_precheck_20260601\s2_gate_53_report.html`

## Known Limitations
- The full-frame local-maximum scan still runs for every resident frame.
- The precheck reduces lock pressure only after a grid cell has filled all top-k slots.
- The resident benchmark keeps Local Normalization off by contract.
- The 200-light run uses the established M38 H benchmark exclusions and fixed reference frame; broader target diversity remains future work.

## Next Step
- S2-Gate54 should target the remaining resident registration cost, especially pixel-refine and warp scheduling, or batch more of the descriptor / refine path under fewer per-frame launches.

## Clean-Room Compliance
- Compliant. This gate changed only GLASS-owned CUDA candidate-selection code and used GLASS tests/artifacts plus user-generated benchmark/reference outputs.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or reworked.
