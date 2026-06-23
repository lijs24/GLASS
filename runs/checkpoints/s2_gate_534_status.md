# S2-Gate 534 Status: Parallel Native Count-Map DQ

## Gate

S2-Gate 534

## Completed

- Profiled the real 200-light default audit route and identified native
  count-map DQ construction as a significant host-side hot path.
- Parallelized `_glass_cuda_native.resident_dq_map_count_maps_i16` with
  disjoint output slices, local per-thread stats, and final reduction.
- Added `dq_map_stats_native_thread_count` to resident artifacts.
- Rebuilt the native extension in true Release mode and verified the runtime
  chooses native count-map DQ by default.
- Ran real 200-light validation and bitwise map comparison against Gate533.

## Commands Run

- `cmd.exe /d /s /c "... VsDevCmd.bat ... && .venv\Scripts\cmake.exe -S . -B build-release-native -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -DCMAKE_BUILD_TYPE=Release ... && .venv\Scripts\cmake.exe --build build-release-native --target _glass_cuda_native -j 8"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_dq_map_count_maps_native_matches_fast_python_when_available tests\test_resident_cuda_run.py::test_resident_dq_map_dispatch_uses_native_count_maps_fast_path tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_dq_map_count_maps_native_matches_fast_python_when_available tests\test_resident_cuda_run.py::test_resident_dq_map_dispatch_uses_native_count_maps_fast_path tests\test_resident_cuda_run.py::test_light_prefetcher_counts_pinned_ring_inflight_slots`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate534_parallel_dq_final\runs_20260623_142500\parallel_dq_final_default --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`

## Test Results

- Focused native DQ/CUDA smoke: `5 passed in 0.26s`.
- Focused native DQ/prefetch smoke: `3 passed in 0.25s`.
- Full pytest: `1175 passed in 43.68s`.

## Real 200-Light Results

- Baseline Gate533:
  `C:\glass_runs\phase2_s2_gate533_prefetch_inflight_fix\runs_20260623_134500\default_after`.
- Gate534 final:
  `C:\glass_runs\phase2_s2_gate534_parallel_dq_final\runs_20260623_142500\parallel_dq_final_default`.
- Baseline shell/internal: `5.795757 s` / `5.4339563000248745 s`.
- Gate534 shell/internal: `5.278554 s` / `4.924247499962803 s`.
- Artifact records:
  - `dq_map_stats_backend=native_host_fast_count_maps`;
  - `dq_map_stats_native_method=resident_dq_map_count_maps_i16`;
  - `dq_map_stats_native_thread_count=16`.
- Master, weight, coverage, low rejection, high rejection, and DQ maps are
  bitwise identical to Gate533.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- CUDA Toolkit used for local Release rebuild: 13.2.

## Known Limits

- This optimization applies to the validated finite/nonnegative count-map DQ
  fast path.
- Debug native builds correctly fall back to Python DQ by default; Release build
  evidence is required for performance claims.

## Next

- Continue with resident registration/warp batching or native FITS read overlap.

## Clean-Room

- Compliant. The gate uses GLASS source, GLASS-generated artifacts, user-owned
  benchmark images, and prior user-generated WBPP black-box comparison evidence
  only. It does not inspect or copy PixInsight/WBPP/PJSR source or modify input
  directories.
