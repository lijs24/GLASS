# S2-Gate 608 Status: Native 512-Frame Hardened Winsorized Capacity

## Gate

S2-Gate 608.

## Completed

- Raised the exact resident CUDA hardened winsorized capacity from `256` to `512` frames.
- Updated native CUDA kernel sample storage to sort up to `512` valid samples per pixel.
- Updated native wrapper guard to reject groups above `512` frames with a clear error.
- Updated resident runtime/pipeline tests so segmented CPU fallback starts at `513`.
- Added a 260-frame native CUDA vs CPU baseline hardened winsorized parity test.
- Rebuilt `_glass_cuda_native`.
- Ran synthetic 260-light validation and real 200-light regression.
- Updated docs and algorithm-source log.

## Commands Run

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && ".\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "winsorized_contract or segmented_cpu_hardened or hardened_winsorized_matches_cpu_baseline"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "segmented_resident_hardened" tests\test_resident_winsorized_benchmark_contract.py tests\test_resident_winsorized_sweep_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_benchmark_contract.py tests\test_resident_winsorized_sweep_contract.py`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate606_segmented_hardened\processing_plan.json --out C:\glass_runs\phase2_s2_gate608_native512_hardened\resident_260_native512 --backend cuda --memory-mode resident --until-stage integration --resident-registration off --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --resident-winsorized-mode auto --resident-output-maps audit --flat-floor 0.05 --resident-runtime-preset manual --resident-prefetch-frames 8 --resident-prefetch-workers 4 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 2`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate608_native512_hardened\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\python.exe -m ruff check cpp src tests`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native hardened CUDA focused tests: `4 passed, 50 deselected`.
- Resident winsorized/runtime focused tests: `10 passed, 105 deselected`.
- Pipeline segmented contract focused test: `1 passed, 57 deselected`.
- Resident benchmark/sweep contract tests: `11 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1289 passed in 52.80 s`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Native backend: available.

## Synthetic 260-Light Validation

- Run path: `C:\glass_runs\phase2_s2_gate608_native512_hardened\resident_260_native512`.
- Route: `native_cuda_resident_stack`.
- Resolution reason: `auto_hardened_frame_count_within_limit`.
- `resident_winsorized_mode`: `hardened_cpu_parity`.
- Native hardened timing: `0.00396340002771467 s`.
- Gate607 fallback hardened timing: `0.009082899894565344 s`.
- Pixel comparison against Gate607 fallback:
  - master max_abs/rms: `0.0 / 0.0`
  - weight max_abs/rms: `0.0 / 0.0`
  - coverage max_abs/rms: `0.0 / 0.0`
  - low rejection max_abs/rms: `0.0 / 0.0`
  - high rejection max_abs/rms: `0.0 / 0.0`
  - DQ map max_abs/rms: `0.0 / 0.0`
- `pipeline_contract.json`: passed.
- `resident_result_contract.json`: passed.

## Real 200-Light Regression

- Run path: `C:\glass_runs\phase2_s2_gate608_native512_hardened\real_200_default_regression`.
- `total_elapsed_s`: `11.92688700009603`.
- `resident_integration_s`: `3.8001627000048757`.
- Hardened native timing: `3.8001173000084236 s`.
- Route: `native_cuda_resident_stack`.
- Six integration FITS outputs are SHA256-identical to Gate607.
- `pipeline_contract.json`: passed.
- `resident_result_contract.json`: passed.

## Known Limitations

- This is a bounded exact native-capacity gate, not a scalable segmented CUDA reducer.
- The hardened kernel now uses a larger per-thread local sample buffer; it is correct for supported groups but not the final design for very large stacks.
- Groups above `512` frames still use the segmented CPUStackEngine resident-tile fallback when available.

## Next Step

Implement a scalable all-device segmented or selection-based hardened winsorized reducer for groups above `512` frames, preserving the CPUStackEngine parity tests and using the Gate607/608 artifacts as regression references.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA kernels, GLASS CPUStackEngine formulas, GLASS synthetic data, and user-owned real benchmark artifacts. No external or proprietary implementation source was inspected, copied, summarized, or reworked.
