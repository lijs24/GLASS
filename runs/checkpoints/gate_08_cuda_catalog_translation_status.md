# Gate 08 CUDA Catalog Translation Status

- Gate: 08 registration, CUDA star-catalog transform scoring increment
- Date: 2026-05-13
- Scope:
  - Added `estimate_translation_from_catalogs_f32(...)`.
  - The CUDA implementation forms reference/moving star pair offsets on device,
    scores offset clusters on device, and returns the highest-vote translation.
  - Added Python compatibility wrapper and CPU fallback for importability.
  - Added tests for direct coordinate catalogs and catalogs produced by
    `star_top_candidates_f32`.

## Commands

```powershell
cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "<repo>\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_gpu_star_detect.py
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\gpu\registration.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Targeted CUDA registration/star tests: 9 passed.
- Ruff: all checks passed.
- Full pytest: 91 passed in 5.68 s.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- Updated CUDA native module in local `src/_glass_cuda_native*.pyd` build output.
- Updated tests in `tests/test_gpu_registration_search.py`.
- Updated docs:
  - `docs/cuda_backend.md`
  - `docs/registration_model.md`

## Known Limitations

- This is still a translation-only scorer.
- It clusters pair offsets and reports the highest-vote offset, but does not yet
  enforce one-to-one star assignment.
- It does not yet estimate subpixel centroids, similarity/affine transforms,
  rotation, scale, or warp interpolation.
- The O(pair_count^2) scoring kernel is acceptable for bounded top-N catalogs
  and tests, but should be replaced by a tiled/histogram or RANSAC-style scorer
  before large production catalogs.

## Next Step

Add GPU one-to-one inlier scoring/refinement around the selected catalog
translation, then extend the same device-side catalog path to similarity/affine
candidate generation.

## Clean-Room

No official PixInsight WBPP/PJSR source was read or used. This is a clean-room
CUDA pair-offset voting implementation based on general star-catalog matching
principles.
