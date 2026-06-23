# S2-Gate 551 Status: Native Completion Lane-Wave Drain

- Gate: S2-Gate 551
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_551_completion_lane_wave_summary.json`
- Result: green checkpoint, small opt-in scheduling improvement, not promoted

## Completed

- Changed the opt-in native completion-to-calibration consumer from one-completion-at-a-time handling to lane-wave draining.
- After the first read completion wakes the consumer, currently ready completions are drained up to the active calibration lane count and submitted as one scheduling wave.
- Added native and resident artifact counters for consumer schedule mode, wave count, max wave size, and multi-frame wave count.
- Kept `GLASS_RESIDENT_NATIVE_COMPLETION_CALIBRATION=1` as the explicit opt-in gate; the default resident raw-u16 path is unchanged.
- Tested and rejected a FIFO-front-only slot query variant because it reduced event queries but worsened the light stage; that variant is not present in this commit.

## Commands Run

- Release native extension build:
  `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release'`
- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_path_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light completion opt-in:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate551_completion_lane_wave\runs_20260623_161354\completion_lane_wave_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Real 200-light fresh default:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate551_completion_lane_wave\runs_20260623_161410\default_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`

## Test Results

- Focused completion/path/default tests: `5 passed in 1.21 s`
- Full pytest: `1188 passed in 43.83 s`

## Real 200-Light A/B

- Completion run:
  `C:\glass_runs\phase2_s2_gate551_completion_lane_wave\runs_20260623_161354\completion_lane_wave_release`
- Fresh default run:
  `C:\glass_runs\phase2_s2_gate551_completion_lane_wave\runs_20260623_161410\default_release`
- Frame count: 200 lights
- Completion shell elapsed: `5.5835369 s`
- Fresh default shell elapsed: `5.6008087 s`
- Completion shell ratio versus default: `0.996916x`
- Completion light read/upload/calibrate: `2.882655 s`
- Fresh default light read/upload/calibrate: `2.588665 s`
- Completion light-stage slowdown versus default: `1.113568x`
- Completion light-stage improvement versus Gate550 completion (`2.911669 s`): `1.010x`
- Completion registration/warp: `0.254906 s`
- Fresh default registration/warp: `0.254457 s`
- Completion integration: `0.306447 s`
- Fresh default integration: `0.320908 s`
- Completion output write: `0.226364 s`
- Fresh default output write: `0.344932 s`
- Completion backend counts: `native_u16be_raw_completion_calibration: 200`
- Fresh default backend counts: `native_u16be_raw: 200`
- Completion workers: `16`
- Completion queue buffers: `24`
- Completion submits/completions: `200` / `200`
- Completion out-of-order completions: `118`
- Consumer schedule mode: `completion_lane_wave_drain`
- Consumer waves/max wave/multi-frame waves: `184` / `4` / `10`
- Slot release mode: `event_query_deferred_reuse`
- Slot reuses/query-ready/waits: `176` / `176` / `0`
- Slot reuse event queries: `2232`
- Final H2D collects: `24`
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

## Known Limitations

- The lane-wave drain is correct and slightly improves the opt-in completion path versus Gate550, but it still does not beat the default light stage.
- Only `10` of `184` consumer waves contained more than one frame, so the native queue mostly still wakes the consumer one frame at a time.
- The path remains opt-in and must not become the default.

## Next Step

- Build a deeper ready buffer or reuse the existing callback-release lane scheduler so native completions can fill true four-lane waves before H2D submission, instead of relying on momentary queue depth at wake time.

## Clean-Room

- This gate uses GLASS-owned code, public FITS byte-range structure, user image data, and GLASS-generated artifacts only.
- No external implementation source was inspected or copied.
- The gate does not alter calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
