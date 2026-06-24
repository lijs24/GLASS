# S2-Gate 606 Status - Segmented CPU-Parity Hardened Winsorized Fallback

## Gate

- Gate: S2-Gate 606
- Status: PASS
- Date: 2026-06-24
- Scope: Provide an auditable CPU-baseline parity fallback for resident hardened `winsorized_sigma` groups above the native 256-frame CUDA prototype limit, while preserving the current 200-light native CUDA default path.

## Completed Work

- Added resident hardened execution-route constants:
  - `native_cuda_resident_stack`
  - `cpu_stack_engine_segmented_resident_download`
- Extended resident rejection descriptors with:
  - `hardened_execution_route`
  - `native_frame_limit`
  - `segmented_cpu_fallback`
  - segmented fallback algorithm name
- Extended resident winsorized runtime contracts so:
  - `auto` uses native CUDA hardened winsorized when the frame count is within the native limit;
  - `auto` and explicit `hardened_cpu_parity` use the segmented CPUStackEngine fallback above the native limit;
  - native-limit failures still raise clearly if the fallback is unavailable.
- Added a resident calibrated-stack image source adapter that exposes `read_tile()` by calling `ResidentCalibratedStack.download_frame_tile()`.
- Added `_integrate_resident_hardened_winsorized_with_cpu_stack_engine()` to run the GLASS CPUStackEngine median/IQR winsorized implementation from resident calibrated tiles.
- Extended resident result-contract semantics to accept the segmented CPU parity route only when it discloses:
  - `approximation=false`
  - `cpu_baseline_parity=true`
  - `hardened_execution_route=cpu_stack_engine_segmented_resident_download`
  - `segmented_cpu_fallback=true`
- Updated integration and limitation docs so `>256` resident hardened groups are documented as correctness-first CPUStackEngine fallback, not final segmented CUDA.

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_result_contract.py tests\test_pipeline_contract.py src\glass\engine\rejection.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "resident_result_contract or segmented_resident_hardened"
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "winsorized_contract or segmented_cpu_hardened"
.\.venv\Scripts\glass.exe synthetic --out C:\glass_runs\phase2_s2_gate606_segmented_hardened\synthetic_260 --frames 260 --width 32 --height 32 --filter H --known-shift
.\.venv\Scripts\glass.exe scan --root C:\glass_runs\phase2_s2_gate606_segmented_hardened\synthetic_260 --out C:\glass_runs\phase2_s2_gate606_segmented_hardened\manifest.json
.\.venv\Scripts\glass.exe plan --manifest C:\glass_runs\phase2_s2_gate606_segmented_hardened\manifest.json --out C:\glass_runs\phase2_s2_gate606_segmented_hardened\processing_plan.json
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate606_segmented_hardened\processing_plan.json --out C:\glass_runs\phase2_s2_gate606_segmented_hardened\resident_260_segmented_fixed --backend cuda --memory-mode resident --until-stage integration --resident-registration off --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --resident-winsorized-mode auto --resident-output-maps audit --flat-floor 0.05 --resident-runtime-preset manual --resident-prefetch-frames 8 --resident-prefetch-workers 4 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 2
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate606_segmented_hardened\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident winsorized/runtime tests: 8 passed, 106 deselected
- Focused pipeline contract tests: 4 passed, 43 deselected
- Ruff: passed
- Full pytest: 1286 passed in 52.52 s

## Synthetic 260-Light Result

- Run: `C:\glass_runs\phase2_s2_gate606_segmented_hardened\resident_260_segmented_fixed`
- Dataset: 260 H lights, 65 bias, 65 dark, 65 flat, 32x32
- `pipeline_contract.json`: passed
- Effective mode: `hardened_cpu_parity`
- Execution route: `cpu_stack_engine_segmented_resident_download`
- Algorithm: `median_iqr_winsorized_sigma_cpu_stack_engine_resident_tile_download`
- Segmented CPU fallback: true
- CPUStackEngine fallback timing: `0.016401000088080764 s`
- Low rejected samples: 102
- High rejected samples: 11834
- All required integration outputs were written.

## Real 200-Light Regression

- Run: `C:\glass_runs\phase2_s2_gate606_segmented_hardened\real_200_default_regression`
- Plan: `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json`
- Runtime preset: `throughput-v4-native-completion`
- Total elapsed: `11.820206300122663 s`
- Pipeline contract: passed
- Effective mode: `hardened_cpu_parity`
- Execution route: `native_cuda_resident_stack`
- Segmented CPU fallback: false
- Native hardened integration: `3.729744700016454 s`
- Six integration FITS outputs are SHA256-identical to Gate605:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`
  - `resident_dq_map_H.fits`

## CUDA Status

- CUDA available to GLASS: yes
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Native backend: true
- Resident memory admission: passed
- Estimated 200-light peak: `56.49848874285817 GiB`
- Budget source: `device_total_memory_safety_fraction`

## Known Limitations

- The `>256` route is correctness-first and downloads resident calibrated tiles to host for CPUStackEngine processing.
- The native CUDA hardened winsorized implementation remains limited to 256 frames.
- This gate does not implement the final segmented CUDA median/IQR reduction.
- This gate does not change resident registration, warp, or local-normalization math.

## Next Step

- Implement a true segmented/batched CUDA hardened winsorized reduction for groups above 256 frames, or continue the larger mainline performance work on resident registration/warp batching and orchestration.

## Clean-Room Compliance

- No official external/proprietary implementation source was read, copied, summarized, or reworked.
- Validation used GLASS code, GLASS synthetic artifacts, GLASS runtime artifacts, and user-owned benchmark data.
- Input image directories were treated as read-only.
