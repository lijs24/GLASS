# S2-Gate 47 Status: Batch Resident Triangle Pixel Refinement

## Gate

S2-Gate 47: Batch Resident Triangle Pixel Refinement

## Completed Content

- Added native `ResidentCalibratedStack.refine_matrix_translation_candidates_batch_to_reference`.
- Added Python wrapper normalization for batched matrix-refinement results.
- Routed resident `similarity_cuda_triangle` through deferred native batch pixel
  refinement when the backend exposes the batch API.
- Applied pixel quality gates and resident warp after the batch returns, so
  frame weights, rejected frames, coverage, and registration artifacts remain
  per-frame auditable.
- Added resident artifact fields:
  - `triangle_pixel_refine_batch`
  - `triangle_pixel_refine_batch_mode`
- Added timing field:
  - `triangle_pixel_refine_batch`
- Updated component timing accounting so diagnostic `_batch` aliases are not
  double-counted in `component_accounted_total`.
- Updated Phase 2 gate plan and algorithm source log.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_batches_matrix_translation_refine tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_batches_matrix_translation_refine tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\s2_gate_47_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 23.07577840005979 --reference-time-seconds 1092.541 --glass-label GLASS-S2G47-resident-batch-pixel-refine --reference-label WBPP-blackbox
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\s2_gate_47_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\phase2_contract_acceptance_audit_s2_gate_47.json --markdown C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\phase2_contract_acceptance_audit_s2_gate_47.md --min-active-frames 190 --min-speedup 2.0
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\phase2_contract_acceptance_audit_s2_gate_47.json --out C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\s2_gate_47_report.html
```

## Test Results

- Focused CUDA resident batch tests: `2 passed`
- Focused resident/report/CLI suite: `30 passed`
- Full suite: `259 passed`
- Ruff: `All checks passed`
- Real 200-light acceptance audit: `passed`

## CUDA Availability

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Real-Data Result

- Run directory:
  `C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601`
- Total resident CUDA runtime: `23.07577840005979 s`
- Reference runtime: `1092.541 s`
- Speedup vs reference: `47.34579181073992x`
- Coverage-masked RMS difference: `0.001558294284488301`
- Coverage-masked P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`
- Resident registration/warp total: `10.16752020129934 s`
- Triangle pixel refine total: `3.286880400031805 s`
- Triangle pixel refine batch: `3.286880400031805 s`
- Triangle warp component: `0.4437918025068939 s`
- I/O + upload + calibration: `6.183786300010979 s`
- Output write: `0.555405399762094 s`
- Resident triangle pixel refine batch mode:
  `native_batch_one_seed_per_frame`
- Acceptance performance regression status: `ok`

## Artifacts

- `C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\resident_artifacts.json`
- `C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\s2_gate_47_compare.html`
- `C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\s2_gate_47_compare.json`
- `C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\phase2_contract_acceptance_audit_s2_gate_47.json`
- `C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\phase2_contract_acceptance_audit_s2_gate_47.md`
- `C:\glass_runs\phase2_s2_gate_47_200\resident_batch_pixel_refine_v2_20260601\s2_gate_47_report.html`

## Known Limits

- The batch API reduces Python/native call count and provides a durable
  batch-refine contract, but the current native implementation still executes
  per-frame CUDA metric searches internally.
- Descriptor generation and triangle descriptor fit remain per-frame and are
  still major remaining registration costs.
- Deferred batch refine means pixel-refine quality gates are applied after the
  per-frame descriptor-fit pass; artifacts record the batch quality outcome.

## Next Step

S2-Gate 48 should batch triangle descriptor generation or descriptor-fit inputs
so the remaining resident registration cost moves further away from per-frame
host/device round trips.

## Clean-Room Compliance

Compliant. The gate changes only GLASS-owned resident CUDA refinement scheduling
and diagnostics, uses user-generated benchmark outputs as reference data, and
does not read, copy, summarize, or rework proprietary implementation source.
