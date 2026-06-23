# S2-Gate 549 Status: Native Completion-To-Calibration Queue Probe

- Gate: S2-Gate 549
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_549_completion_calibration_summary.json`
- Result: green checkpoint, viable direction, not promoted

## Completed

- Added native `ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_paths_completion_queue_timed`.
- Added the `glass_cuda.ResidentCalibratedStack` Python wrapper.
- Added resident CUDA opt-in routing behind `GLASS_RESIDENT_NATIVE_COMPLETION_CALIBRATION=1`.
- Implemented a pinned raw FITS completion ring inside the native resident stack.
- Native worker threads read raw FITS payloads into pinned buffers while the native consumer submits completed frames to H2D/decode/calibration lanes.
- Recorded completion candidate/requested/available/enabled state, worker count, queue buffer count, submit/completion counts, out-of-order completion count, and completion order sample in resident artifacts.
- Kept the default raw-u16 callback-release path unchanged.

## Commands Run

- Native Release extension build:
  `cmd.exe /c "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe -S . -B build -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_CUDA_ALLOW_UNSUPPORTED_COMPILER=ON -Dpybind11_DIR=... -DCMAKE_BUILD_TYPE=Release && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release`
- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_path_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light completion opt-in:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate549_completion_calibration\runs_20260623_155714\completion_calibration_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Real 200-light fresh default:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate549_completion_calibration\runs_20260623_155727\default_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`

## Test Results

- Focused completion/path/default tests: `5 passed in 1.23 s`
- Full pytest: `1188 passed in 45.22 s`

## Real 200-Light A/B

- Completion run:
  `C:\glass_runs\phase2_s2_gate549_completion_calibration\runs_20260623_155714\completion_calibration_release`
- Fresh default run:
  `C:\glass_runs\phase2_s2_gate549_completion_calibration\runs_20260623_155727\default_release`
- Frame count: 200 lights
- Completion shell elapsed: `5.500664 s`
- Fresh default shell elapsed: `5.481433 s`
- Shell ratio completion/default: `1.0035084x`
- Completion light read/upload/calibrate: `2.910837 s`
- Fresh default light read/upload/calibrate: `2.574862 s`
- Completion light-stage slowdown versus default: `1.1304827x`
- Completion improvement versus Gate548 pinned native path (`6.625002 s`): `2.2759784x`
- Completion improvement versus Gate547 pageable native path (`7.907601 s`): `2.7166073x`
- Completion registration/warp: `0.253603 s`
- Fresh default registration/warp: `0.254161 s`
- Completion integration: `0.302728 s`
- Fresh default integration: `0.323021 s`
- Completion output write: `0.224726 s`
- Fresh default output write: `0.364525 s`
- Completion backend counts: `native_u16be_raw_completion_calibration: 200`
- Fresh default backend counts: `native_u16be_raw: 200`
- Completion workers: `16`
- Completion queue buffers: `24`
- Completion submits/completions: `200` / `200`
- Completion out-of-order completions: `123`
- Completion pinned buffer model: `cuda_host_alloc_portable_pinned_completion_ring`
- Completion native read total: `29.271370 s`
- Completion native file-read cumulative: `27.875448 s`
- Completion wave H2D elapsed sum: `0.951774 s`
- Raw H2D bytes: `24660480000`
- Avoided float32 host bytes: `49320960000`

## Numerical Validation

All six output FITS artifacts are SHA256-identical between the completion run and the fresh default run:

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

- The completion queue recovers most of the lost overlap from Gate547/Gate548 but remains slower than the default light stage.
- The prototype synchronizes each H2D event before pinned slot reuse and has a single native consumer thread.
- The path remains opt-in and must not become the default.

## Next Step

- Build a deeper native scheduler that batches ready completions into lane waves or connects native read completions to the existing callback-release lane machinery, so pinned slots can be released safely without per-frame main-consumer H2D synchronization.

## Clean-Room

- This gate uses GLASS-owned code, public FITS byte-range structure, user image data, and GLASS-generated artifacts only.
- No external implementation source was inspected or copied.
- The gate does not alter calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
