# S2-Gate 683 Status: Windows Native Sequential Raw FITS Reads

## Gate

S2-Gate 683 continues the Phase 2 resident CUDA mainline by hardening the
Windows raw-FITS read backend used by native-completion calibration.

## Completed

- Added a Windows-only raw payload reader using `CreateFileW` with
  `FILE_FLAG_SEQUENTIAL_SCAN`.
- Kept the portable `std::ifstream` raw reader as the non-Windows fallback.
- Added native timing fields:
  - `native_path_read_backend`
  - `native_completion_read_backend`
- Propagated the aggregate backend to:
  - `resident_io_pipeline.native_path_calibration_read_backend`
  - `resident_light_pipeline_profile.native_completion.read_backend`
- Added focused tests requiring `win32_sequential_scan` on Windows and
  `std_ifstream` elsewhere.
- Ran the real 200-light resident CUDA default route and compared it with the
  Gate682 timing baseline.

## Commands

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && ".venv\Scripts\cmake.exe" --build build --target _glass_cuda_native --config Release'

.\.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_cuda.py src/glass/engine/resident_light_pipeline_profile.py tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py

.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate683_win32_sequential_read\runs_20260626_193000\win32_seq_default --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe resident-runtime-compare --run gate682_default=C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --run gate683_win32_seq=C:\glass_runs\phase2_s2_gate683_win32_sequential_read\runs_20260626_193000\win32_seq_default --baseline-label gate682_default --out C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_runtime_compare.md

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --candidate-run C:\glass_runs\phase2_s2_gate683_win32_sequential_read\runs_20260626_193000\win32_seq_default --out C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_regression_gate_realistic.json --markdown C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_regression_gate_realistic.md --max-elapsed-ratio 1.10 --min-active-frame-count 193 --max-masked-frame-count 7 --fail-on-failure

.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate683_win32_sequential_read\runs_20260626_193000\win32_seq_default --out C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_mainline_audit_realistic.json --markdown C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_mainline_audit_realistic.md --min-lights 200 --min-active-frames 193 --max-masked-frames 7 --fail-on-not-green

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native CUDA rebuild: succeeded (`ninja: no work to do` after source changes
  were already built into `src\_glass_cuda_native.cp312-win_amd64.pyd`).
- Ruff: `All checks passed!`
- Focused tests: `2 passed in 1.64 s`.
- Full pytest: `1424 passed in 66.23 s`.

## Real 200-Light Validation

- Candidate run:
  `C:\glass_runs\phase2_s2_gate683_win32_sequential_read\runs_20260626_193000\win32_seq_default`
- Baseline:
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us`
- Candidate backend:
  `native_path_calibration_read_backend=win32_sequential_scan`
- Candidate total elapsed:
  `11.860965099884197 s`
- Gate682 baseline total elapsed:
  `11.735124099999666 s`
- Elapsed ratio:
  `1.0107234485815566`
- Runtime compare:
  `C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_runtime_compare.json`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_regression_gate_realistic.json`
  passed with failed checks `[]`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_mainline_audit_realistic.json`
  passed with failed checks `[]`.
- Output hash comparison:
  `C:\glass_runs\phase2_s2_gate683_win32_sequential_read\gate683_output_hash_compare.json`
  reports bitwise-identical master, weight, coverage, low-rejection,
  high-rejection, and DQ FITS outputs versus Gate682.

## CUDA

- CUDA was available.
- Device observed during the Phase 2 run series:
  NVIDIA RTX PRO 6000 Blackwell, compute capability 12.0, driver 596.21,
  97886 MiB VRAM.

## Known Limits

- Gate683 is not a speed promotion. Gate682 remains the best observed timing
  baseline on this workstation.
- The cumulative worker file-read time is larger than wall time because native
  completion workers overlap reads; it should be read as aggregate worker time,
  not serialized stage time.
- The active/masked frame threshold is intentionally `193 / 7`, matching the
  established registration-quality outcome for this 200-light dataset.

## Next

- Return to substantive hot-path work:
  - multi-buffer CPU read/decode, pinned-memory H2D, and CUDA calibration
    overlap;
  - resident registration/warp orchestration with fewer host/device round trips;
  - deterministic resident reducer redesign only if it can be validated against
    the 200-light gate without output drift.

## Clean-Room

This gate uses GLASS-owned C++/CUDA code, GLASS Python artifacts, GLASS tests,
and user-owned benchmark outputs. It does not inspect, copy, summarize, or
rework external/proprietary implementation source, and it does not modify input
image directories.
