# S2 Gate 622 Status: Guarded Unit-Weight Local-Reuse Integration Probe

## Gate

- Gate: S2-Gate 622
- Status: green checkpoint
- Branch: `main`
- Scope: resident CUDA hardened winsorized integration and measured 200-light scheduling probes

## Completed

- Added an opt-in native CUDA branch guarded by `GLASS_CUDA_UNIT_WEIGHT_LOCAL_REUSE=1`.
- The branch is used only when all positive finite integration weights are exactly `1.0`.
- The branch keeps a second frame-order local sample copy so winsorized mean/variance, rejection counting, and final accumulation can reuse ordered samples after quickselect mutates the selector array.
- Default resident hardened winsorized integration remains unchanged: `global_reread_weighted_samples`.
- `GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX=1` remains a separate opt-in experiment and takes precedence if both local reuse and active-index are requested.
- Native profiles now record:
  - `unit_positive_local_reuse_requested`
  - `unit_positive_local_reuse_enabled`
  - `unit_positive_weight_frame_count`
  - `sample_reuse_strategy`
- Added focused CUDA parity coverage for the local-reuse route and default-off behavior.
- Ran three real 200-light probes and recorded negative results for default promotion.

## Real 200-Light Results

Baseline:

- Run: `C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_default_audit_guarded_20260625_022933`
- Total elapsed: `10.49075440003071 s`
- Resident calibration/integration: `9.655427400022745 s`
- Light read/upload/calibrate: `3.2439714000793174 s`
- Resident integration: `3.2403203999856487 s`
- Native hardened kernel sync: `3.1234866 s`
- Strategy: `global_reread_weighted_samples`

Scheduling probes:

- `fill0`: `10.639579100068659 s`; slower than baseline.
- `queue64_workers32`: `11.797367000253871 s`; slower than baseline.
- `queue64_workers32` regression gate passed correctness/contract checks but reported baseline as fastest; elapsed ratio `1.1245489647741003`.

Local-reuse opt-in:

- Run: `C:\glass_runs\phase2_s2_gate622_resident_calibration_pipeline\real_200_local_reuse_optin_20260625_024449`
- Total elapsed: `11.206340099917725 s`
- Resident calibration/integration: `10.363780500018038 s`
- Light read/upload/calibrate: `3.2750233999686316 s`
- Resident integration: `3.9029811000218615 s`
- Native hardened kernel sync: `3.7804679 s`
- Strategy: `local_ordered_reuse_unit_positive_weights`
- Positive unit-weight frames detected: `193`
- Regression gate: passed correctness/contract/frame-mask checks versus baseline.
- Elapsed ratio: `1.0682110811673295`.

Decision:

- Do not promote local reuse or the scheduling probes.
- Keep `GLASS_CUDA_UNIT_WEIGHT_LOCAL_REUSE=1` diagnostic-only.
- The measured conclusion is that duplicating per-thread sample arrays increases local-memory pressure enough to outweigh fewer global stack rereads on the current 200-light RTX PRO 6000 benchmark.

## Commands Run

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8'`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_default_off tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_local_reuse_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_matches_cpu_baseline`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_default_off tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_local_reuse_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_matches_cpu_baseline tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_minimal_output_master_only`
- `.\.venv\Scripts\python.exe -m ruff check cpp src tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\glass.exe run ... --resident-native-completion-wave-fill-us 0`
- `.\.venv\Scripts\glass.exe run ... --resident-prefetch-frames 64 --resident-prefetch-workers 32 --resident-calibration-batch-frames 64`
- `$env:GLASS_CUDA_UNIT_WEIGHT_LOCAL_REUSE='1'; .\.venv\Scripts\glass.exe run ...`
- `.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_default_audit_guarded_20260625_022933 --candidate-run C:\glass_runs\phase2_s2_gate622_resident_calibration_pipeline\real_200_local_reuse_optin_20260625_024449 --out C:\glass_runs\phase2_s2_gate622_resident_calibration_pipeline\resident_regression_gate_local_reuse_vs_default.json --markdown C:\glass_runs\phase2_s2_gate622_resident_calibration_pipeline\resident_regression_gate_local_reuse_vs_default.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Result

- Focused CUDA resident-stack tests: `4 passed in 1.81s`.
- Focused resident-stack/CLI hardened tests: `6 passed in 0.76s`.
- Ruff: passed.
- Full pytest: `1308 passed in 52.83s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Native backend: available.
- CUDA Toolkit used for rebuild: `13.2`.

## Known Limitations

- The local-reuse kernel is slower on the real 200-light benchmark and is intentionally not a default path.
- The default resident hardened reducer remains a bounded per-pixel local-array implementation up to 512 frames.
- Groups above the native hardened limit still require the existing segmented CPUStackEngine fallback.
- The next integration performance step should redesign the reducer around lower local-memory pressure, not add another per-thread sample array.

## Next Step

- Start the next substantive gate on a redesigned resident hardened reducer strategy, such as segmented/cooperative order-statistic computation, or return to a higher-level pipeline completeness target if reducer design needs a larger implementation window.

## Clean-Room Compliance

- This gate used only GLASS-owned CUDA/C++/Python code, GLASS tests, GLASS CPU-baseline formulas, and user-owned real benchmark outputs.
- No external proprietary implementation source was read, copied, summarized, or reworked.
