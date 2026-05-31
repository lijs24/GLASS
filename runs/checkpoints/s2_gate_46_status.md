# S2-Gate 46 Status: Async Resident Warp Copy Dispatch

## Gate

S2-Gate 46: Async Resident Warp Copy Dispatch

## Completed Content

- Removed per-frame host `cudaDeviceSynchronize()` calls from resident CUDA:
  - integer translation warp
  - bilinear translation warp
  - matrix bilinear warp
  - matrix Lanczos3 warp
- Replaced synchronous device-to-device frame-stack copies with default-stream
  `cudaMemcpyAsync` calls.
- Preserved same-stream ordering for later resident registration, integration,
  coverage-map download, and output download synchronization points.
- Added native/Python `warp_copy_mode` reporting:
  `default_stream_async_device_to_device`.
- Recorded `resident_warp_copy_mode` and `resident_io_pipeline.warp_copy_mode`
  in `resident_artifacts.json`.
- Surfaced the warp copy mode in the HTML resident CUDA summary.
- Updated Phase 2 gate plan and algorithm source log.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_reuses_warp_scratch_buffers tests\test_cuda_resident_stack.py::test_resident_stack_translation_warp_uses_nan_coverage tests\test_cuda_resident_stack.py::test_resident_stack_estimates_and_warps_subpixel_translation_on_device tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\python.exe -c "import glass_cuda; s=glass_cuda.ResidentCalibratedStack(1,2,2); print(s.warp_copy_mode)"
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\s2_gate_46_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 23.44897719984874 --reference-time-seconds 1092.541 --glass-label GLASS-S2G46-resident-async-warp-copy --reference-label WBPP-blackbox
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\s2_gate_46_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\phase2_contract_acceptance_audit_s2_gate_46.json --markdown C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\phase2_contract_acceptance_audit_s2_gate_46.md --min-active-frames 190 --min-speedup 2.0
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\phase2_contract_acceptance_audit_s2_gate_46.json --out C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\s2_gate_46_report.html
```

## Test Results

- Focused CUDA resident tests: `4 passed`
- Focused resident/report/CLI suite: `49 passed`
- Full suite: `258 passed`
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
  `C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601`
- Total resident CUDA runtime: `23.44897719984874 s`
- Reference runtime: `1092.541 s`
- Speedup vs reference: `46.59226671972061x`
- Coverage-masked RMS difference: `0.001558294284488301`
- Coverage-masked P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`
- Resident registration/warp total: `10.018980199005455 s`
- Triangle warp component: `0.025039998814463615 s`
- I/O + upload + calibration: `6.255973000079393 s`
- Output write: `0.5037056999281049 s`
- Resident warp copy mode: `default_stream_async_device_to_device`
- Resident warp scratch bytes: `493209636`
- Acceptance performance regression status: `ok`

## Artifacts

- `C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\resident_artifacts.json`
- `C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\s2_gate_46_compare.html`
- `C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\s2_gate_46_compare.json`
- `C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\phase2_contract_acceptance_audit_s2_gate_46.json`
- `C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\phase2_contract_acceptance_audit_s2_gate_46.md`
- `C:\glass_runs\phase2_s2_gate_46_200\resident_async_warp_copy_20260601\s2_gate_46_report.html`

## Known Limits

- This gate reduces host synchronization in warp application, but descriptor
  generation, descriptor fit, pixel refinement, and warp launches are still
  per-frame.
- Asynchronous kernel execution errors are surfaced at later CUDA
  synchronization points such as integration/download. Kernel launch errors are
  still checked immediately.
- Default-stream ordering is the current contract; future stream-pool work will
  need explicit dependency management.

## Next Step

S2-Gate 47 should batch more of the resident triangle registration ladder:
descriptor fit, pixel refinement, and warp dispatch should be grouped to reduce
per-frame Python/native call overhead and host-device round trips.

## Clean-Room Compliance

Compliant. The gate changes only GLASS-owned CUDA scheduling and diagnostics,
uses user-generated benchmark outputs as reference data, and does not read,
copy, summarize, or rework proprietary implementation source.
