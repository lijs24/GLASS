# S2-Gate 548 Status: Pinned Native Path Calibration Probe

- Gate: S2-Gate 548
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_548_pinned_native_path_summary.json`
- Result: green checkpoint, negative performance probe, not promoted

## Completed

- Replaced the Gate547 native path coordinator's pageable per-lane raw FITS staging buffers with scoped `cudaHostAllocPortable` pinned lane buffers.
- Added a native `CudaHostUCharFree` RAII deleter.
- Recorded `native_path_host_buffer_model` and `native_path_host_buffer_pinned` in native timing and resident artifacts.
- Added focused assertions for pinned buffer reporting in resident stack and CLI tests.

## Commands Run

- Native Release extension build:
  `cmd.exe /c "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe -S . -B build -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_CUDA_ALLOW_UNSUPPORTED_COMPILER=ON -Dpybind11_DIR=... -DCMAKE_BUILD_TYPE=Release && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release`
- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_path_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light pinned native path:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate548_pinned_native_path_calibration\runs_20260623_154626\pinned_native_path_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Real 200-light fresh default:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate548_pinned_native_path_calibration\runs_20260623_154643\default_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`

## Test Results

- Focused resident path/default tests: `3 passed in 1.06 s`
- Full pytest: `1186 passed in 44.08 s`

## Real 200-Light A/B

- Pinned native path run:
  `C:\glass_runs\phase2_s2_gate548_pinned_native_path_calibration\runs_20260623_154626\pinned_native_path_release`
- Fresh default run:
  `C:\glass_runs\phase2_s2_gate548_pinned_native_path_calibration\runs_20260623_154643\default_release`
- Frame count: 200 lights
- Pinned native path shell elapsed: `9.187321 s`
- Fresh default shell elapsed: `5.495093 s`
- Pinned native path light read/upload/calibrate: `6.625002 s`
- Fresh default light read/upload/calibrate: `2.586849 s`
- Pinned native path slowdown versus default light stage: `2.5610316x`
- Pinned native path improvement versus Gate547 pageable native path (`7.907601 s`): `1.1935998x`
- Pinned native path registration/warp: `0.256614 s`
- Fresh default registration/warp: `0.253927 s`
- Pinned native path integration: `0.305583 s`
- Fresh default integration: `0.343677 s`
- Pinned native path output write: `0.219301 s`
- Fresh default output write: `0.360092 s`
- Pinned native path backend counts: `native_u16be_raw_path_calibration: 200`
- Fresh default backend counts: `native_u16be_raw: 200`
- Pinned native path buffer model: `cuda_host_alloc_portable_pinned_lane_buffers`
- Pinned native path host buffer pinned: `true`
- Native path read total: `4.601690 s`
- Native path file-read cumulative: `17.798358 s`
- Native path wave H2D elapsed sum: `0.565367 s`
- Raw H2D bytes: `24660480000`
- Avoided float32 host bytes: `49320960000`

## Numerical Validation

All six output FITS artifacts are SHA256-identical between the pinned native path run and the fresh default run:

- `resident_master_H.fits`: `8BC069CE6858AB5E065B5D9AF297C35C36D4240C13980546E43CFB480115E110`
- `resident_weight_map_H.fits`: `5862111EE6F527A40671AC13F1FAA43F037C90271F872F27AF4ACF17040FBFE8`
- `resident_coverage_map_H.fits`: `B87517BE794A3B4BDCFF0D8536EE0188DA6AFA54ED2BE818BD911BA6CF1BE1B3`
- `resident_low_rejection_map_H.fits`: `F1181E0CE52A7FF77B988AFAF8A8911A1BEAF94DF54B25B0AA51014CB0D66E23`
- `resident_high_rejection_map_H.fits`: `ADB66C931C5A48D6E0D7F5C2FCBCC58481420AD4912304843A3802089050C805`
- `resident_dq_map_H.fits`: `934F661119CE18BBCAC1D369488AED4D959669C6EF614D6076D74BE06E69CCFB`

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Known Limitations

- Pinned staging improves the Gate547 native path but does not make it competitive with the default resident raw-u16 path.
- The native path still waits for an entire read wave before H2D/decode/calibration and therefore loses ready-order prefetch overlap.
- The path remains opt-in and must not become the default.

## Next Step

- Implement a true pinned native completion-to-calibration queue: native workers should fill pinned raw buffers, expose completions, and feed H2D/decode/calibration waves as frames complete rather than after a whole wave joins.

## Clean-Room

- This gate uses GLASS-owned code, public FITS byte-range structure, user image data, and GLASS-generated artifacts only.
- No external implementation source was inspected or copied.
- The gate does not alter calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
