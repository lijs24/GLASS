# S2-Gate 684 Status: Native Read Backend Policy

## Gate

S2-Gate 684 continues the Phase 2 resident CUDA I/O/calibration mainline by
turning the raw FITS payload reader into an explicit, auditable execution
policy.

## Completed

- Added native raw-FITS backend dispatch:
  - `auto`
  - `std_ifstream`
  - `win32_sequential_scan`
- `auto` resolves to `std_ifstream`, restoring the portable reader as the
  default resident native-completion backend.
- Kept the Gate683 Windows `CreateFileW + FILE_FLAG_SEQUENTIAL_SCAN` reader as
  an explicit A/B backend.
- Added CLI/audit option:
  `--resident-native-read-backend auto|std_ifstream|win32_sequential_scan`.
- Added timing/artifact fields:
  - `resident_native_read_backend`
  - `native_path_calibration_read_backend_policy`
  - `resident_light_pipeline_profile.native_completion.read_backend_policy`
- Added focused tests for:
  - throughput-v4 default backend policy;
  - explicit CLI override preservation;
  - default native completion `auto -> std_ifstream`;
  - explicit Win32 sequential native stack parity on Windows.

## Commands

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && ".venv\Scripts\cmake.exe" --build build --target _glass_cuda_native --config Release'

.\.venv\Scripts\python.exe -m ruff check src/glass/cli.py src/glass/engine/resident_cuda.py src/glass/engine/resident_light_pipeline_profile.py tests/test_cli_smoke.py tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py

.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_resident_runtime_preset_throughput_v4_native_completion_applies_default_values tests/test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v4_native_completion tests/test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_native_read_backend tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_runtime_preset_is_cli_opt_in

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe resident-runtime-compare --run gate682_default=C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --run gate683_win32=C:\glass_runs\phase2_s2_gate683_win32_sequential_read\runs_20260626_193000\win32_seq_default --run gate684_auto_std=C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm --baseline-label gate682_default --out C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_runtime_compare.md

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us --candidate-run C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm --out C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_regression_gate.md --max-elapsed-ratio 1.10 --min-active-frame-count 193 --max-masked-frame-count 7 --fail-on-failure

.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm --out C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_mainline_audit.md --min-lights 200 --min-active-frames 193 --max-masked-frames 7 --fail-on-not-green

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native CUDA rebuild: passed.
- Ruff: `All checks passed!`
- Focused tests: `6 passed in 2.24 s`.
- Full pytest: `1425 passed in 66.10 s`.

## Real 200-Light Validation

- Default candidate:
  `C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm`
- Candidate backend policy:
  `native_path_calibration_read_backend_policy=auto`
- Candidate effective backend:
  `native_path_calibration_read_backend=std_ifstream`
- Candidate total elapsed:
  `11.66652269999031 s`
- Gate682 baseline elapsed:
  `11.735124099999666 s`
- Gate683 Win32 sequential elapsed:
  `11.860965099884197 s`
- Runtime compare:
  `C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_runtime_compare.json`
  selected `gate684_auto_std` as best observed.
- Regression gate:
  `C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_regression_gate.json`
  passed with failed checks `[]` and elapsed ratio `0.9941541819732985`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_mainline_audit.json`
  passed with failed checks `[]`.
- Output hash comparison:
  `C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\gate684_output_hash_compare.json`
  reports bitwise-identical master, weight, coverage, low-rejection,
  high-rejection, and DQ FITS outputs versus Gate682.

## Cold I/O Outlier

A cold `auto -> std_ifstream` run at
`C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std`
completed in `34.373473399784416 s` and recorded aggregate worker read time
`361.414487 s`. The immediate warm rerun returned to `11.66652269999031 s`.
This outlier is retained as evidence of external disk/cache variability and is
not used as a promoted performance result.

## CUDA

- CUDA was available.
- Device observed during the Phase 2 run series:
  NVIDIA RTX PRO 6000 Blackwell, compute capability 12.0, driver 596.21,
  97886 MiB VRAM.

## Known Limits

- This gate adds backend policy and restores the default effective backend; it
  does not yet implement deeper read/decode/H2D double buffering.
- The explicit Win32 sequential backend remains available for A/B runs but is
  not promoted as the default on this workstation.
- Runtime is still sensitive to external USB disk/cache state.

## Next

- Use the new backend policy to run clean I/O matrices when the disk is quiet.
- Implement true multi-buffer overlap next: CPU raw read/decode into pinned RAM
  while CUDA H2D/calibration drains the previous wave.
- Continue resident registration/warp orchestration work only under the
  existing mainline/regression gates.

## Clean-Room

This gate uses GLASS-owned C++/CUDA/Python code, GLASS tests, and user-owned
benchmark outputs. It does not inspect, copy, summarize, or rework
external/proprietary implementation source, and it does not modify input image
directories.
