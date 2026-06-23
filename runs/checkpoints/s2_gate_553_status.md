# S2-Gate 553 Status: Native Completion Wave-Fill Tuning Matrix

- Gate: S2-Gate 553
- Date: 2026-06-23
- Branch: `main`
- Checkpoint summary: `runs/checkpoints/s2_gate_553_wave_fill_matrix_summary.json`
- Result: green checkpoint, configurable opt-in tuning retained, fixed wait not promoted

## Completed

- Added `GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_US` for the opt-in native completion calibration path.
- Native completion calibration now reads `native_completion_consumer_wave_fill_wait_us` from the policy payload and validates `0..10000`.
- `0` disables ready-buffer fill waiting and records policy `disabled`; positive values record `timed_wait_<N>us`.
- Resident CUDA records wave-fill source (`env` or `default_disabled`) and requested wait budget in `resident_io_pipeline`.
- Changed no-env completion calibration default from Gate552's implicit `100 us` to `0 us`, because the 200-light matrix showed fixed waits improved wave packing but hurt or failed to improve the target light stage.

## Commands Run

- Release native extension build:
  `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release'`
- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_path_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real 200-light matrix:
  - completion explicit `0 us`, `25 us`, `50 us`, `100 us`;
  - completion no-env default-disabled;
  - postpatch default release.

## Test Results

- Focused completion/path/default tests: `5 passed in 0.88 s`
- Full pytest: `1188 passed in 43.69 s`

## Real 200-Light Matrix

- Matrix root:
  `C:\glass_runs\phase2_s2_gate553_wave_fill_matrix\runs_20260623_163435`
- Full summary:
  `C:\glass_runs\phase2_s2_gate553_wave_fill_matrix\runs_20260623_163435\gate553_matrix_metrics_summary.json`
- Frame count: 200 lights
- Active frame count after registration masks: 193
- Masked frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`

| Run | Shell s | Light read/upload/calibrate s | Fill policy | Fill wait s | Consumer waves | Multi-frame waves |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| completion `50 us` | `5.572498` | `2.883491` | `timed_wait_50us` | `0.307064` | `59` | `53` |
| completion `0 us` | `5.584446` | `2.869436` | `disabled` | `0.000000` | `184` | `9` |
| completion `25 us` | `5.587291` | `2.883540` | `timed_wait_25us` | `0.323574` | `64` | `51` |
| completion no-env | `5.630820` | `2.923844` | `disabled` | `0.000000` | `179` | `13` |
| completion `100 us` | `5.758776` | `3.024602` | `timed_wait_100us` | `0.344149` | `64` | `53` |
| default postpatch | `5.434383` | `2.556746` | n/a | `0.000000` | `0` | `0` |

## Numerical Validation

All completion variants are SHA256-identical to the postpatch default run for all six output FITS artifacts:

- `resident_master_H.fits`: `8BC069CE6858AB5E065B5D9AF297C35C36D4240C13980546E43CFB480115E110`
- `resident_weight_map_H.fits`: `5862111EE6F527A40671AC13F1FAA43F037C90271F872F27AF4ACF17040FBFE8`
- `resident_coverage_map_H.fits`: `B87517BE794A3B4BDCFF0D8536EE0188DA6AFA54ED2BE818BD911BA6CF1BE1B3`
- `resident_low_rejection_map_H.fits`: `F1181E0CE52A7FF77B988AFAF8A8911A1BEAF94DF54B25B0AA51014CB0D66E23`
- `resident_high_rejection_map_H.fits`: `ADB66C931C5A48D6E0D7F5C2FCBCC58481420AD4912304843A3802089050C805`
- `resident_dq_map_H.fits`: `934F661119CE18BBCAC1D369488AED4D959669C6EF614D6076D74BE06E69CCFB`

Resident StackEngine surface contract and DQ pixel closure passed in the inspected runs.

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Decision

- Completion calibration remains opt-in behind `GLASS_RESIDENT_NATIVE_COMPLETION_CALIBRATION=1`.
- Wave-fill waits are disabled by default and must be explicitly requested with `GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_US`.
- Fixed waits are not promoted: they improve multi-frame wave packing but did not beat the default light stage.

## Known Limitations

- The native completion queue still loses to the current default read/upload/calibration scheduler on the target light stage.
- Timing variation in integration and output write can make shell rankings look friendlier than the light-stage ranking; the light-stage metric is the optimization target here.
- This gate does not solve resident registration/warp or StackEngine rejection parity work.

## Next Step

- Stop tuning fixed fill waits. The next useful optimization should either connect native raw FITS reads to the faster callback-release/ready-first scheduler or reduce native completion orchestration so the completion path can match the default light stage without explicit waiting.

## Clean-Room

- This gate uses GLASS-owned code, public FITS byte-range structure, user image data, and GLASS-generated artifacts only.
- No external implementation source was inspected or copied.
- The gate does not alter calibration formulas, registration, warp, rejection, DQ, integration, accepted frames, or output pixels.
