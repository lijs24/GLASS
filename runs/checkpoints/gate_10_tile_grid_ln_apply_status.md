# Gate 10 Tile/Grid LN Apply Status

## Gate

Gate 10 partial capability checkpoint: tile/grid Local Normalization building block.

This checkpoint does not claim full WBPP-like Local Normalization. It adds and validates a piecewise tile/grid coefficient model and CUDA apply kernel, which is a prerequisite for full tile/window LN.

## Completed Content

- Added CPU baseline helpers:
  - `estimate_grid_normalization_mean_std`;
  - `apply_grid_normalization`;
  - `normalize_grid_mean_std`.
- Added CUDA kernel `glass_local_norm_apply_grid_f32_kernel`.
- Added native binding `local_norm_apply_grid_f32`.
- Added Python wrapper `glass_cuda.local_norm_apply_grid_f32` with CPU fallback.
- Added CPU and CUDA tests for edge tiles, grid coefficient application, and tile mean/std matching.
- Updated `docs/local_normalization_model.md` to describe the grid model and its limitations.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cpu\local_norm.py src\glass\gpu\local_norm.py src\glass_cuda.py tests\test_cpu_local_norm.py tests\test_gpu_local_norm_vs_cpu.py
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "<repo>\.venv\Scripts\cmake.exe" --build "<repo>\build\native-cuda"'
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_local_norm.py tests\test_gpu_local_norm_vs_cpu.py tests\test_cuda_import.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Native CUDA extension build: passed.
- Targeted LN/CUDA tests: `11 passed in 1.09s`.
- Full test suite: `167 passed in 7.94s`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- This is a piecewise constant tile/grid apply model.
- Coefficient estimation currently runs through CPU baseline helpers; the CUDA layer applies the coefficient grid.
- Smooth interpolation between LN coefficients, background masks, robust/outlier-resistant local windows, and resident full-frame integration are not complete.
- This checkpoint is a tested building block for Gate 10, not the complete Gate 10 finish line.

## Next Step

- Add coefficient interpolation and/or GPU tile statistics, then wire the grid LN model into streaming and resident pipeline stage artifacts.

## Clean-room Compliance

- Compliant. The implementation uses general mean/std normalization math and project-owned CUDA code.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
