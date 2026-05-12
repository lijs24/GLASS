# Gate 8 Resident Grid Star-Catalog Registration Status

## Gate

Gate 8 incremental capability: grid-distributed resident CUDA star-catalog
translation registration.

This checkpoint improves the resident star-catalog translation path by allowing
candidate stars to be selected as the brightest local maximum per image grid
cell. It reduces the chance that global top-N selection is dominated by clustered
bright structure or outliers.

## Completed Content

- Extended `ResidentCalibratedStack.estimate_translation_from_stars_to_reference`
  with `grid_cols` and `grid_rows`.
- Grid mode runs `gpwbpp_star_grid_candidates_f32_launch` directly on resident
  reference and moving frames.
- Pair-offset voting and mutual-nearest refinement remain on the GPU.
- Python wrapper now returns `candidate_selection`, `catalog_capacity`,
  `grid_cols`, and `grid_rows`.
- CLI now exposes `--resident-star-grid-cols` and `--resident-star-grid-rows`.
- Resident artifacts record the grid dimensions.
- Added resident stack and CLI tests for grid-catalog mode.
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
- Targeted CUDA/resident registration tests: `31 passed in 1.15s`.
- Full pytest suite: `106 passed in 5.84s`.

## Real Data Diagnostic

Ran a read-only calibrated M38 H-alpha pair diagnostic using the same two frames
from the astroalign/NCC comparison:

- Reference: `C:\gpwbpp_runs\final_m38_h_200\input\Light\LIGHT_H_0001.fits`
- Moving: `C:\gpwbpp_runs\final_m38_h_200\input\Light\LIGHT_H_0005.fits`
- Artifact:
  `runs/alignment_compare_resident_star_catalog_m38_pair_calibrated/resident_star_catalog_grid_pair_summary.md`

Best diagnostic trial:

- Grid: `16x8`
- Threshold: approximately p99.9, `1038.645`
- Resident GPU star-catalog result: `dx=9.0`, `dy=0.6875`
- Mutual inliers: `16`
- Star-catalog RMS: `0.8455 px`
- Device-side estimate time: `0.0021 s`
- Prior calibrated comparison: astroalign center displacement `dx=8.887`,
  `dy=0.715`; resident NCC `dx=8.5`, `dy=0.5`

## CUDA Availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: loaded and available to GPWBPP

## Known Limitations

- Translation only; similarity/affine/homography remain future work.
- Star centroids are still integer local maxima, not refined PSF centroids.
- The grid selector requires threshold/grid tuning on real frames.
- Real full-stack 200-light integration has not yet been repeated with grid
  star-catalog registration.

## Next Step

Add GPU centroid refinement and use the grid star-catalog mode inside a small
real multi-frame resident run before attempting full similarity/affine matching.

## Clean-Room Compliance

Compliant. This checkpoint used GPWBPP code and project-generated diagnostics.
It did not read or copy PixInsight/WBPP/PJSR official source.
