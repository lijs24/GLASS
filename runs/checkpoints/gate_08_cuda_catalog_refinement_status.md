# Gate 08 CUDA Catalog Refinement Status

- Gate: 08 registration, CUDA star-catalog refinement increment
- Date: 2026-05-13
- Scope:
  - Extended `estimate_translation_from_catalogs_f32(...)` with a GPU
    mutual-nearest refinement pass.
  - The function now returns:
    - `dx`, `dy`: highest-vote pair-offset translation.
    - `refined_dx`, `refined_dy`: average delta from mutual-nearest inliers.
    - `mutual_inliers`: count of mutual-nearest catalog matches.
    - `rms_px`: RMS residual after the refined translation.
  - Added Python CPU fallback parity for the new diagnostic fields.

## Commands

```powershell
cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "<repo>\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_gpu_star_detect.py
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\gpu\registration.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Targeted CUDA registration/star tests: 10 passed.
- Ruff: all checks passed.
- Full pytest: 92 passed in 5.65 s.

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

- Refinement is still translation-only.
- Mutual-nearest matching is performed around the highest-vote translation, not
  around similarity/affine candidates.
- GPU subpixel centroid extraction is not yet implemented; refined deltas only
  reflect the precision of the input catalog coordinates.
- The pair-offset scorer remains O(pair_count^2), appropriate for bounded
  top-N catalogs but not final production-scale matching.

## Next Step

Use the refined GPU translation to drive device-side warp validation, then add
GPU similarity/affine candidate generation and scoring from triangle/asterism
features.

## Clean-Room

No official PixInsight WBPP/PJSR source was read or used. This is a clean-room
CUDA refinement pass based on general mutual-nearest catalog matching.
