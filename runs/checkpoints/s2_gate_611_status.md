# S2-Gate 611 Status: Native Hardened Quickselect Percentiles

## Gate

- Gate: S2-Gate 611
- Status: green
- Date: 2026-06-24
- Objective: optimize the resident CUDA hardened `winsorized_sigma` kernel bottleneck identified by S2-Gate 610 while keeping CPU-baseline semantics auditable.

## Completed Content

- Replaced the native hardened median/q25/q75 per-pixel insertion sort with quickselect order statistics.
- Kept the S2-Gate 609 `small_256` and `large_512` native kernel dispatch.
- Changed winsorized mean/std accumulation to reread valid resident samples in input frame-axis order after percentile selection.
- Added native profile field `winsorized_accumulation_order=frame_axis_input_order`.
- Kept native profile field `percentile_strategy=quickselect_order_statistics`.
- Updated CUDA/API tests and resident CLI tests to require the new profile fields.
- Updated integration model, known limitations, Phase 2 plan, and algorithm source/audit documentation.

## Commands Run

```powershell
cmd /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && ".\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "hardened_winsorized_matches_cpu_baseline"
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate606_segmented_hardened\processing_plan.json --out C:\glass_runs\phase2_s2_gate611_quickselect_frame_order\resident_260_quickselect_frame_order --backend cuda --memory-mode resident --until-stage integration --resident-registration off --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --resident-winsorized-mode auto --resident-output-maps audit --flat-floor 0.05 --resident-runtime-preset manual --resident-prefetch-frames 8 --resident-prefetch-workers 4 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 2
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate611_quickselect_frame_order\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
```

## Test Results

- Native CUDA rebuild: passed; warnings only from CUDA/MSVC headers and one existing signed/unsigned warning.
- Focused CUDA hardened tests: `4 passed, 50 deselected`.
- Focused resident CLI hardened parity test: `1 passed, 114 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1289 passed in 52.92 s`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Driver: 596.21.
- VRAM: 97886 MiB reported by GLASS, 97887 MiB reported by `nvidia-smi`.

## Validation Artifacts

- Synthetic 260-light run:
  `C:\glass_runs\phase2_s2_gate611_quickselect_frame_order\resident_260_quickselect_frame_order`
  - `native_kernel_capacity_selector=large_512`
  - `hardened_winsorized_timing_s.total_s=0.008832699968479574`
  - `native_profile.kernel_sync_s=0.0087259`
  - `native_profile.percentile_strategy=quickselect_order_statistics`
  - `native_profile.winsorized_accumulation_order=frame_axis_input_order`
  - `pipeline_contract.json`: passed
  - `resident_result_contract.json`: passed
  - Six FITS outputs were bit-identical to the S2-Gate 609 260-light output.

- Real 200-light default regression:
  `C:\glass_runs\phase2_s2_gate611_quickselect_frame_order\real_200_default_regression`
  - `total_elapsed_s=11.453746799845248`
  - `native_kernel_capacity_selector=small_256`
  - `hardened_winsorized_timing_s.total_s=3.4022495999233797`
  - `native_profile.kernel_sync_s=3.2809923`
  - `native_profile.download_s=0.1150331`
  - `native_profile.allocation_s=0.0015426`
  - `native_profile.free_s=0.0044863`
  - `native_profile.percentile_strategy=quickselect_order_statistics`
  - `native_profile.winsorized_accumulation_order=frame_axis_input_order`
  - `pipeline_contract.json`: passed
  - `resident_result_contract.json`: passed

## Real 200-Light Difference Against S2-Gate 610

- S2-Gate 610 hardened native timing: `3.752243599970825 s`.
- S2-Gate 611 hardened native timing: `3.4022495999233797 s`.
- Kernel+sync improved from `3.6350664 s` to `3.2809923 s`.
- Master map changed in `41 / 61651200` pixels (`6.650316619952247e-07`), with `max_abs=1.8656654357910156` and `rms=0.0006160635903431593`.
- Weight and coverage maps changed in the same `41` threshold-boundary pixels with `max_abs=2.0`.
- Low rejection map changed in `19` pixels.
- High rejection map changed in `32` pixels.
- DQ map changed in `29` pixels.
- Interpretation: the old sorted local buffer made winsorized mean/std accumulation order depend on the full-sort implementation. S2-Gate 611 makes the order explicit and CPU-baseline aligned by using input frame-axis order after percentile selection.

## Known Limitations

- The native hardened resident path remains bounded to 512 active frames.
- Groups above 512 still need the segmented CPUStackEngine fallback until an all-device segmented reducer exists.
- The real 200-light output is not bit-identical to S2-Gate 610 because Gate611 intentionally aligns accumulation order with CPU baseline semantics instead of the old sorted-buffer side effect.
- The next larger performance costs are still resident registration/warp orchestration, local normalization, and remaining calibration/I/O scheduling.

## Next Step

- Continue the Phase 2 substantive mainline by either:
  - implementing a scalable resident CUDA segmented/order-statistics reducer for groups above 512, or
  - batching more resident registration/warp orchestration and reducing host/device synchronization in the 200-light default path.

## Clean-Room Compliance

- This gate uses GLASS-owned CUDA kernels, GLASS CPU-baseline formulas, GLASS synthetic data, and user-owned benchmark artifacts.
- No external or proprietary implementation source was inspected, copied, summarized, or reworked.
- Input image directories were not modified.
