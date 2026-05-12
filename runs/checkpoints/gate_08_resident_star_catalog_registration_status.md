# Gate 8 Resident Star-Catalog Registration Status

## Gate

Gate 8 incremental capability: resident CUDA star-catalog translation
registration.

This checkpoint does not claim similarity, affine, homography, Lanczos warp, or
full astroalign-equivalent asterism matching. It adds a pure GPU translation
path for resident frames as a bridge from star matching toward the final GPU
registration stack.

## Completed Content

- Added `ResidentCalibratedStack.estimate_translation_from_stars_to_reference`.
- The new native method runs top-N star selection for reference and moving
  resident frames on the GPU.
- Star catalogs stay on device for pair-offset translation voting and
  mutual-nearest refinement.
- The Python wrapper returns compact diagnostics: `dx`, `dy`, `refined_dx`,
  `refined_dy`, `mutual_inliers`, `rms_px`, star counts, tolerance, bounds, and
  model name.
- Added CLI mode:
  `--resident-registration translation_star_catalog`.
- Added CLI controls:
  `--resident-star-threshold`, `--resident-star-max-candidates`,
  `--resident-star-tolerance-px`.
- Resident registration artifacts now record star-catalog parameters and
  non-placeholder star/inlier/RMS diagnostics for this mode.
- Added resident stack and CLI smoke tests.
- Updated CUDA and registration documentation.

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
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_gpu_registration_search.py tests\test_gpu_star_detect.py
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Native CUDA extension rebuild: passed.
- Targeted resident/star registration tests: `30 passed in 1.29s`.
- Full pytest suite: `105 passed in 5.89s`.

## CUDA Availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: loaded and available to GPWBPP

## Known Limitations

- Translation only; similarity/affine/homography are still future work.
- Top-N local maxima do not yet include subpixel centroid refinement.
- The pair-offset scorer is not a full astroalign asterism matcher.
- Resident warp remains bilinear translation only.
- Real 200-frame run has not yet been repeated with this new mode.

## Next Step

Validate `translation_star_catalog` on calibrated real M38 pairs and compare its
RMS/timing against `translation_ncc_subpixel` and `astroalign`, then extend the
GPU registration model toward similarity/affine.

## Clean-Room Compliance

Compliant. This checkpoint used GPWBPP code, existing open-source dependency
interfaces only as behavior references, and project-generated tests/artifacts.
It did not read or copy PixInsight/WBPP/PJSR official source.
