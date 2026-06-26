# S2 Gate 701 Status

Date: 2026-06-26
Branch: `main`
Status: green

## Gate

S2-Gate 701: Radix reducer admission evidence.

## Completed

- Added explicit resident hardened winsorized native profile fields:
  `radix_select_reason` and `radix_select_positive_sample_threshold`.
- Preserved existing reducer behavior: the opt-in radix-select path is still
  admitted only above `512` positive-weight resident samples.
- Added CUDA parity coverage for the case where
  `GLASS_CUDA_RADIX_SELECT_WINSORIZED=1` is requested but the active sample
  count remains within bounded-kernel capacity.
- Extended over-512 radix tests to assert the enabled reason and threshold.
- Fixed resident A/B matrix live-readiness default handling so explicit zero
  thresholds are not replaced by production defaults during recheck.
- Cleared the superseded temporary Gate701 probe directory under
  `C:\glass_runs\phase2_s2_gate701_radix_probe` to recover about `1.39 GB` on
  C drive before the formal run.

## Commands Run

- `cmake --build build --config Release --target _glass_cuda_native`
  - Failed because plain PowerShell did not have the VS/Windows SDK include
    environment.
- `cmd /c "call ...\VsDevCmd.bat -arch=x64 -host_arch=x64 && ...\cmake.exe --build build --config Release --target _glass_cuda_native"`
  - Passed; rebuilt `src\_glass_cuda_native.cp312-win_amd64.pyd`.
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma_radix or over_limit_active_count"`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma"`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate701_radix_admission\runs_20260626_100214\radix_reason_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
  - Run with `GLASS_CUDA_RADIX_SELECT_WINSORIZED=1` set only for this command.
- `.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate701_radix_admission\runs_20260626_100214\radix_reason_candidate --out C:\glass_runs\phase2_s2_gate701_radix_admission\gate701_radix_reason_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate701_radix_admission\gate701_radix_reason_mainline_audit.md`
- `.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --candidate-run C:\glass_runs\phase2_s2_gate701_radix_admission\runs_20260626_100214\radix_reason_candidate --out C:\glass_runs\phase2_s2_gate701_radix_admission\gate701_radix_reason_vs_gate699_ab.json --markdown C:\glass_runs\phase2_s2_gate701_radix_admission\gate701_radix_reason_vs_gate699_ab.md`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_ab_matrix_plan.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused radix/active-count CUDA tests: `5 passed, 76 deselected`.
- Focused hardened winsorized resident CUDA tests:
  `23 passed, 58 deselected`.
- First full pytest exposed an environment-dependent resident A/B matrix test
  failure because C drive free space was below the production `8 GiB` threshold.
- Focused resident A/B matrix tests after fixing explicit-threshold recheck:
  `10 passed`.
- Full pytest after fixes: `1449 passed in 70.44 s`.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate701_radix_admission\runs_20260626_100214\radix_reason_candidate`
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate701_radix_admission\gate701_radix_reason_mainline_audit.json`
- A/B versus Gate699:
  `C:\glass_runs\phase2_s2_gate701_radix_admission\gate701_radix_reason_vs_gate699_ab.json`
- Audit passed: `True`.
- Input lights / active frames / masked frames: `200 / 193 / 7`.
- A/B passed: `True`.
- Elapsed ratio versus Gate699: `0.9838090132320593`.
- Worst component ratio: `1.0081475096798698`.
- Hash mismatch/missing counts: `0 / 0`.
- Total elapsed: `11.76368820015341 s`.
- Component timings:
  - read/upload/calibrate: `2.9798155000898987 s`
  - registration/warp: `0.2652424005791545 s`
  - local normalization: `0.35907689994201064 s`
  - integration: `3.263650399981998 s`
  - output write: `0.2730445000343025 s`

## Native Reducer Evidence

- `native_kernel_capacity_selector`: `small_256`
- `native_kernel_frame_capacity`: `256`
- `native_admission_sample_count`: `193`
- `radix_select_requested`: `True`
- `radix_select_enabled`: `False`
- `radix_select_reason`:
  `disabled_positive_samples_within_bounded_kernel_capacity`
- `radix_select_positive_sample_threshold`: `512`
- `radix_select_positive_sample_count`: `193`
- `sample_reuse_strategy`:
  `frame_mask_global_reread_unit_positive_weights`
- `kernel_sync_s`: `3.1441155`
- `downloaded_bytes`: `616512000`
- `download_s`: `0.115997`

## CUDA

- CUDA was available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97887 MiB reported by `nvidia-smi`.
- Driver: 596.21.
- CUDA Toolkit used by the build: 13.2.

## Known Limitations

- This gate is admission/telemetry hardening, not a new speed optimization.
- The real M38 200-light data has only `193` active positive-weight frames, so
  it does not validate over-512 radix-select reducer performance.
- No calibration math, frame admission, registration, warp, local
  normalization, rejection formula, output pixels, or default reducer selection
  changed.
- C drive remained tight after the formal run, around the 7-8 GB range.

## Next Step

Return to substantive runtime/algorithm work. The highest-value next gate is a
real execution-path improvement in either read/upload/calibration overlap or
resident integration/reducer architecture, validated by synthetic parity plus
the 200-light mainline audit/A-B.

## Clean-Room

Compliant. The gate is derived from GLASS-owned CUDA/native profile logic,
GLASS tests, GLASS report readiness contracts, and user-owned 200-light
benchmark outputs. It does not inspect, copy, summarize, or rework external
proprietary implementation source, and it does not modify input image
directories.
