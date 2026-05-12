# Gate 09 CUDA Matrix Warp Status

Gate: 09 - warp streaming / CUDA warp increment

Date: 2026-05-13

## Completed content

- Added a CUDA bilinear 3x3 matrix warp kernel for float32 images.
- Added Python native binding `gpwbpp_cuda.warp_matrix_bilinear_f32(data, matrix, fill=0.0)`.
- Added CPU fallback for the same wrapper when the native CUDA module is unavailable.
- Added resident GPU in-place matrix warp through `ResidentCalibratedStack.apply_matrix_bilinear_frame(...)`.
- Exported the wrapper from `src/gpwbpp/gpu/warp.py`.
- Added GPU-vs-CPU tests for standalone matrix warp and resident in-place matrix warp.
- Documented the CUDA matrix warp capability as the bridge from translation-only GPU alignment toward similarity/affine registration.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp_cuda.py src\gpwbpp\gpu\warp.py tests\test_gpu_warp_vs_cpu.py
```

Result: passed.

```powershell
$pybind = (& .\.venv\Scripts\python.exe -m pybind11 --cmakedir).Trim()
$ninja = (Resolve-Path .\.venv\Scripts\ninja.exe).Path
$cmd = 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -Dpybind11_DIR="' + $pybind + '" -DCMAKE_MAKE_PROGRAM="' + $ninja + '" -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release'
cmd /c $cmd
```

Result: native CUDA Python module rebuilt successfully.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_cuda_resident_stack.py tests\test_cuda_smoke.py
```

Result: 19 passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 116 passed.

## CUDA availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Test result

The new CUDA matrix warp path matches the CPU bilinear reference within the configured float32 tolerance. The resident in-place path also matches the same CPU reference.

## Known limitations

- This increment validates the CUDA warp primitive, but the main resident pipeline still does not automatically apply similarity/affine registration matrices.
- Homography, Lanczos/resampling selection, distortion models, and final non-translation acceptance policy remain future work.
- Current resident real-data acceleration is still primarily translation NCC plus optional catalog diagnostics.

## Next step

Wire similarity/affine registration outputs into the resident CUDA matrix warp path and compare against the astroalign CPU baseline on a small real pair before scaling to the 200-light run.

## Clean-room compliance

This work used only GPWBPP-owned code, open-source astroalign as an external behavioral baseline, and user-provided image data/artifacts. No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
