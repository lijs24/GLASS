# S2-Gate 547 Status: Native Path Calibration Coordinator Probe

- Gate: S2-Gate 547
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_547_native_path_calibration_summary.json`
- Result: green checkpoint, negative performance probe, not promoted

## Completed

- Added native `ResidentCalibratedStack.calibrate_frames_fits_u16be_bzero_paths_multistream_timed`.
- Added the `glass_cuda.ResidentCalibratedStack` Python wrapper.
- Added opt-in resident CUDA routing behind `GLASS_RESIDENT_NATIVE_PATH_CALIBRATION=1`.
- Required raw-u16 GPU decode, multistream batch calibration, source-DQ fast skip, and cached FITS specs for the opt-in path.
- Recorded native path calibration candidate/requested/available/enabled state, timing, frame counts, host buffer bytes, and calibration mode in resident artifacts.
- Added focused resident stack and CLI tests.

## Commands Run

- Native Release extension build:
  `cmd.exe /c "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe -S . -B build -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_CUDA_ALLOW_UNSUPPORTED_COMPILER=ON -Dpybind11_DIR=... -DCMAKE_BUILD_TYPE=Release && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release`
- Focused native stack tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_on_gpu_like_cpu tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_raw_on_gpu_like_cpu`
- Focused resident CLI tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_path_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light opt-in:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate547_native_path_calibration\runs_20260623_153816\native_path_calibration_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Real 200-light fresh default:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate547_native_path_calibration\runs_20260623_153838\default_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`

## Test Results

- Focused stack path/raw tests: `2 passed in 0.34 s`
- Focused resident path/default tests: `3 passed in 0.68 s`
- Full pytest: `1186 passed in 43.62 s`

## Real 200-Light A/B

- Opt-in run:
  `C:\glass_runs\phase2_s2_gate547_native_path_calibration\runs_20260623_153816\native_path_calibration_release`
- Fresh default run:
  `C:\glass_runs\phase2_s2_gate547_native_path_calibration\runs_20260623_153838\default_release`
- Frame count: 200 lights
- Opt-in backend counts: `native_u16be_raw_path_calibration: 200`
- Default backend counts: `native_u16be_raw: 200`
- Opt-in light read/upload/calibrate: `7.907601 s`
- Default light read/upload/calibrate: `2.572788 s`
- Opt-in registration/warp: `0.255650 s`
- Default registration/warp: `0.254171 s`
- Opt-in integration: `0.302695 s`
- Default integration: `0.327721 s`
- Opt-in output write: `0.229035 s`
- Default output write: `0.331448 s`
- Native path read total: `4.602468 s`
- Native path file-read cumulative: `17.841808 s`
- Raw H2D bytes: `24660480000`
- Avoided float32 host bytes: `49320960000`

## Numerical Validation

All six output FITS artifacts are SHA256-identical between the opt-in native path run and the fresh default run:

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

- The native path coordinator is correct but slower than the default by about `3.07x` for light read/upload/calibrate.
- The prototype uses pageable native lane buffers and wave-level file-read joins, so it loses the existing pinned prefetch and ready-order overlap.
- The path remains opt-in and must not become the default.

## Next Step

- Build a pinned native read-to-calibration queue: native workers should fill pinned raw buffers, expose completions, and feed H2D/decode/calibration waves without per-frame Python Future/cache materialization or pageable lane buffers.

## Clean-Room

- This gate uses GLASS-owned code, public FITS byte-range structure, user image data, and GLASS-generated artifacts only.
- No external implementation source was inspected or copied.
- The gate does not alter calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
