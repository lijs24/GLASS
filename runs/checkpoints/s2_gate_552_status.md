# S2-Gate 552 Status: Native Completion Ready-Buffer Wave-Fill

- Gate: S2-Gate 552
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_552_completion_wave_fill_summary.json`
- Result: green checkpoint, opt-in scheduling evidence retained, not promoted

## Completed

- Added a bounded ready-buffer fill wait to the opt-in native completion-to-calibration consumer.
- After the first completed read wakes the consumer, the consumer drains currently ready completions and then waits up to `100 us` at a time for additional completions until the active lane count is filled or no more submitted reads are outstanding.
- Added native and resident artifact counters for wave-fill policy, wait budget, wait count, timeout count, and accumulated wait seconds.
- Kept `GLASS_RESIDENT_NATIVE_COMPLETION_CALIBRATION=1` as the explicit opt-in gate; the default resident raw-u16 path is unchanged.
- Preserved bitwise output identity versus the same-session default run.

## Commands Run

- Release native extension build:
  `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release'`
- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_path_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light completion wave-fill opt-in:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate552_completion_wave_fill\runs_20260623_162509\completion_wave_fill_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Real 200-light fresh default:
  `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate552_completion_wave_fill\runs_20260623_162509\default_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`

## Test Results

- Focused completion/path/default tests: `5 passed in 0.71 s`
- Full pytest: `1188 passed in 43.80 s`

## Real 200-Light A/B

- Completion wave-fill run:
  `C:\glass_runs\phase2_s2_gate552_completion_wave_fill\runs_20260623_162509\completion_wave_fill_release`
- Fresh default run:
  `C:\glass_runs\phase2_s2_gate552_completion_wave_fill\runs_20260623_162509\default_release`
- Frame count: 200 lights
- Active frame count after registration masks: 193
- Masked frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`
- Completion shell elapsed: `5.4283625 s`
- Fresh default shell elapsed: `5.7409071 s`
- Shell speedup, default over completion: `1.057576x`
- Completion run-timing total: `5.0590255 s`
- Fresh default run-timing total: `5.3754435 s`
- Completion resident stage elapsed: `5.0555342 s`
- Fresh default resident stage elapsed: `5.3722712 s`
- Completion light read/upload/calibrate: `2.856499 s`
- Fresh default light read/upload/calibrate: `2.566939 s`
- Completion light-stage ratio versus default: `1.112807x`
- Completion native H2D/decode/calibrate/store: `1.857241 s`
- Fresh default native H2D/decode/calibrate/store: `0.783179 s`
- Completion registration/warp: `0.254409 s`
- Fresh default registration/warp: `0.257511 s`
- Completion integration: `0.303845 s`
- Fresh default integration: `0.348234 s`
- Completion output write: `0.221734 s`
- Fresh default output write: `0.393786 s`
- Completion backend counts: `native_u16be_raw_completion_calibration: 200`
- Fresh default backend counts: `native_u16be_raw: 200`
- Completion workers: `16`
- Completion queue buffers: `24`
- Completion submits/completions: `200` / `200`
- Completion out-of-order completions: `104`
- Consumer schedule mode: `completion_lane_wave_drain`
- Consumer waves/max wave/multi-frame waves: `67` / `4` / `53`
- Wave-fill policy/wait: `timed_wait_100us` / `100 us`
- Wave-fill waits/timeouts/seconds: `151` / `33` / `0.466731 s`
- Slot release mode: `event_query_deferred_reuse`
- Slot reuses/query-ready/waits: `176` / `176` / `0`
- Slot reuse event queries: `841`
- Final H2D collects: `24`

## Numerical Validation

All six output FITS artifacts are SHA256-identical between the completion wave-fill run and the fresh default run:

- `resident_master_H.fits`: `8BC069CE6858AB5E065B5D9AF297C35C36D4240C13980546E43CFB480115E110`
- `resident_weight_map_H.fits`: `5862111EE6F527A40671AC13F1FAA43F037C90271F872F27AF4ACF17040FBFE8`
- `resident_coverage_map_H.fits`: `B87517BE794A3B4BDCFF0D8536EE0188DA6AFA54ED2BE818BD911BA6CF1BE1B3`
- `resident_low_rejection_map_H.fits`: `F1181E0CE52A7FF77B988AFAF8A8911A1BEAF94DF54B25B0AA51014CB0D66E23`
- `resident_high_rejection_map_H.fits`: `ADB66C931C5A48D6E0D7F5C2FCBCC58481420AD4912304843A3802089050C805`
- `resident_dq_map_H.fits`: `934F661119CE18BBCAC1D369488AED4D959669C6EF614D6076D74BE06E69CCFB`

Resident StackEngine surface contract passed, and DQ pixel closure passed.

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Known Limitations

- The ready-buffer wave-fill is correct and greatly improves native completion wave packing versus Gate551, but it still does not beat the default light stage.
- The fixed `100 us` fill wait accumulated `0.466731 s`, so the policy is too blunt for default promotion.
- The path remains opt-in and must not become the default.

## Next Step

- Replace the fixed fill wait with an adaptive policy or connect native completions to the default callback-release scheduler so full lane waves can form without paying a fixed wait penalty.

## Clean-Room

- This gate uses GLASS-owned code, public FITS byte-range structure, user image data, and GLASS-generated artifacts only.
- No external implementation source was inspected or copied.
- The gate does not alter calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
