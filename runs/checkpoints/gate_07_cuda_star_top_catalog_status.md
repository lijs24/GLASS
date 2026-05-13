# Gate 07 CUDA Star Top Catalog Status

- Gate: 07 star detection + quality metrics, CUDA-resident preregistration increment
- Date: 2026-05-13
- Scope:
  - Added GPU top-N local-maximum star catalog selection.
  - Added descending flux sorting on device before returning compact diagnostics.
  - Exposed standalone API: `glass_cuda.star_top_candidates_f32(...)`.
  - Exposed resident API:
    `ResidentCalibratedStack.star_top_candidates(index, threshold, max_candidates)`.
  - Kept the previous `star_candidates_f32` compact API unchanged for backward
    compatibility.

## Commands

```powershell
cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "<repo>\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\gpu\star_detect.py tests\test_gpu_star_detect.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Targeted CUDA star/registration tests: 7 passed.
- Ruff: all checks passed.
- Full pytest: 89 passed in 5.70 s.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- Updated CUDA native module in local `src/_glass_cuda_native*.pyd` build output.
- Added tests in `tests/test_gpu_star_detect.py`.
- Updated CUDA backend documentation.

## Known Limitations

- The current top-N implementation uses a simple device lock and device-side
  selection sort. It is correct and pure GPU for bounded catalogs, but it is an
  engineering baseline rather than the final high-throughput catalog sorter.
- The catalog returns local-maximum pixel coordinates and peak flux only; it
  does not yet include subpixel centroids, FWHM, eccentricity, or descriptors.
- Asterism matching, subpixel transform refinement, and similarity/affine model
  scoring are still pending.

## Next Step

Use the GPU-sorted top catalogs as inputs for a device-side clean-room
asterism/transform scorer, with CPU limited to orchestration and compact
diagnostics.

## Clean-Room

No official PixInsight WBPP/PJSR source was read or used. This increment is a
clean-room CUDA implementation based on GLASS's own local-maximum detector and
general GPU selection/sorting techniques.
