# S2-Gate 528 Status: Resident Calibration Wave Lane Guard

Date: 2026-06-23

## Completed

- Fixed the resident CUDA calibration scheduling contract when requested wave frames exceed available native streams.
- Python scheduling now clamps effective wave frames to the stream/lane count before callback-release capability selection.
- Native callback-release functions also clamp `wave_frames` defensively, preserving `requested_wave_frames` for audit.
- Resident artifacts now record requested effective wave frames, final effective wave frames, clamp source, stream-count limit, and whether the lane guard was applied.
- Resident light-pipeline profile knobs now expose the guarded effective wave size.
- Added a resident CUDA regression proving `wave > streams` remains on callback-release with a safe effective wave size.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py tests\test_resident_cuda_run.py`
- `cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "callback_queue_clamps_wave_to_stream_count or callback_queue_releases_inside_native_batch or io_pipeline or native_u16"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_light_pipeline_profile.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_528_doctor.json`
- `.\.venv\Scripts\python.exe -m ruff check cpp src tests`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused resident CUDA tests: `4 passed, 87 deselected in 0.93s`.
- CUDA import/device/smoke tests: `3 passed in 0.23s`.
- Resident light-pipeline profile tests: `3 passed in 0.04s`.
- Ruff: passed.
- Full pytest: `1171 passed in 43.17s`.

## CUDA Status

- CUDA available: yes.
- Native CUDA extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Real 200-Light Validation

- Pre-fix problematic run:
  `C:\glass_runs\phase2_mainline_calibration_schedule_sweep\runs_20260623_113629\b32_s4_w8`.
- Post-fix guarded run:
  `C:\glass_runs\phase2_s2_gate528_wave_guard_real\runs_20260623_114527\b32_s4_w8_guarded`.
- Current default baseline:
  `C:\glass_runs\phase2_mainline_real_200_ab\runs_20260623_113423\glass_current`.
- Configuration: `batch=32`, `streams=4`, `wave=8`, `release_mode=callback_queue`.
- Pre-fix shell time: `22.639912 s`; internal total: `22.263613699993584 s`.
- Post-fix shell time: `6.422997 s`; internal total: `6.050774999952409 s`.
- Post-fix artifact records:
  - `calibration_wave_requested_frames=8`;
  - `calibration_wave_requested_effective_frames=8`;
  - `calibration_wave_effective_frames=4`;
  - `calibration_wave_effective_source=requested_wave_frames_clamped_to_stream_count`;
  - `calibration_wave_lane_guard_applied=true`;
  - `calibration_release_mode_effective=callback_queue`;
  - `raw_gpu_decode_enabled=true`;
  - `fits_read_mode_effective=native_u16_gpu`.
- Post-fix light-pipeline wall: `2.621918899996672 s`.
- Post-fix native H2D/calibrate/store: `0.8112155 s`.
- Post-fix consumer read wait: `1.0221229999442585 s`.
- Speedup versus problematic route: `3.524821035172522x` shell and `3.679464993989495x` internal.

## Numerical Validation

- Post-fix guarded master, weight map, coverage map, low rejection map, high rejection map, and DQ map match the current default 200-light output bitwise.
- RMS and max absolute difference are `0.0` for all six compared outputs.

## Known Limitations

- This gate fixes a high-batch/high-wave scheduling fallback and native bounds contract; it is not a new default-route speedup because the default route already uses `wave=streams=4`.
- The next runtime target is still larger: reduce consumer read wait/native H2D synchronization or batch resident registration/warp more deeply.

## Clean-Room Compliance

- Only GLASS code, GLASS-generated artifacts, and user-owned 200-light data were used.
- No official PixInsight/WBPP/PJSR source code was accessed, summarized, copied, or reworked.
- Input image directories were treated as read-only.

