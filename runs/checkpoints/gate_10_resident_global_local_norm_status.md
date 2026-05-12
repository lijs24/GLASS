# Gate 10 Resident Global Local Normalization Status

## Gate

Gate 10 incremental capability: resident CUDA global mean/std local normalization.

This is not the full tile/window Local Normalization gate. It is a high-VRAM
resident capability flag that keeps calibrated/registered frames in VRAM,
computes per-frame finite-pixel mean/std on the GPU, applies a global affine
normalization to non-reference frames, writes `local_norm_results.json`, and
continues into resident integration.

## Completed Content

- Added CUDA frame statistics reduction for resident frames:
  `frame_global_stats(index)`.
- Added resident in-place global normalization:
  `apply_global_normalization_frame(index, scale, offset)`.
- Exposed both methods through `gpwbpp_cuda.ResidentCalibratedStack`.
- Enabled `gpwbpp run --memory-mode resident --local-normalization on`.
- Resident runs now write `local_norm_results.json` with mode
  `resident_global_mean_std`, reference frame, per-frame coefficients, status,
  warnings, timing, and `crop_box: null`.
- Resident artifacts and integration outputs record the LN mode.
- Updated CUDA and Local Normalization documentation.
- Added GPU unit tests and CLI smoke coverage.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp_cuda.py src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py
```

```powershell
$pybind = (& .\.venv\Scripts\python.exe -m pybind11 --cmakedir).Trim()
$ninja = (Resolve-Path .\.venv\Scripts\ninja.exe).Path
cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -Dpybind11_DIR="..." -DCMAKE_MAKE_PROGRAM="..." -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release'
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_gpu_local_norm_vs_cpu.py
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Native CUDA extension rebuild: passed.
- Targeted CUDA/resident LN tests: `15 passed in 1.17s`.
- Full pytest suite: `103 passed in 5.79s`.

## CUDA Availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: loaded and available to GPWBPP

## Known Limitations

- This checkpoint implements global mean/std matching, not full tile/window
  Local Normalization.
- Resident registration remains translation-only.
- Resident winsorized rejection remains a two-stage mean/std approximation, not
  a byte-for-byte PixInsight FastIntegration reproduction.
- Full Local Normalization still needs tile/window statistics, masks, and CPU/GPU
  equivalence tests over realistic gradients.

## Next Step

Extend Gate 10 from `resident_global_mean_std` to tile/window Local
Normalization with masked local statistics and CPU/GPU comparison tests.

## Clean-Room Compliance

Compliant. This checkpoint used local project code, public CUDA/C++/Python
interfaces, and project-generated artifacts only. It did not read or copy
PixInsight/WBPP/PJSR official source.
