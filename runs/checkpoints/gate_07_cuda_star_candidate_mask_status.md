# Gate 7 Checkpoint: CUDA Resident Star Candidate Catalog

Gate: 7

Completed content:
- Added `cpp/cuda/star_detect_kernels.cu` local-maximum candidate mask kernel.
- Added native Python bindings `star_local_max_mask_f32(image, threshold)` and `star_candidates_f32(image, threshold, max_candidates)`.
- Added `ResidentCalibratedStack.star_local_max_mask(index, threshold)` and `ResidentCalibratedStack.star_candidates(index, threshold, max_candidates)` so star candidates can be detected and compacted directly from calibrated frames that already live in VRAM.
- Added Python wrapper `gpwbpp_cuda.star_local_max_mask_f32`.
- Added Python wrapper `gpwbpp_cuda.star_candidates_f32`.
- Added `src/gpwbpp/gpu/star_detect.py` wrapper.
- Vectorized the CPU fallback local-max detector for correctness comparison and cpu-only operation.
- Added CUDA tests for standalone image mask/catalog and resident-stack mask/catalog.

Commands run:
- `.\.venv\Scripts\python.exe -m cmake --build build\native-cuda --config Debug` (failed outside the VS developer environment because `cl.exe`/MSVC include paths were not active).
- `cmd /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m ruff check src\gpwbpp_cuda.py src\gpwbpp\gpu\star_detect.py src\gpwbpp\cpu\star_detect.py src\gpwbpp\engine\quality.py tests\test_gpu_star_detect.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

Test results:
- CUDA targeted tests after mask binding: 5 passed.
- CUDA star catalog tests: 4 passed.
- Full pytest after catalog binding: 86 passed in 5.68s.
- Ruff Python check: passed.

CUDA availability:
- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

Known limitations:
- This gate produces local-max candidate masks and bounded `(x, y, flux)` catalogs, but does not yet run top-N sorting on the GPU.
- Centroid refinement, flux-window ranking, and asterism matching are still pending GPU work.
- The current resident pipeline does not yet use this mask for transform estimation.
- `astroalign` was not installed; the attempted `pip install astroalign` timed out. It remains a public MIT reference option, not a runtime dependency.

Next step:
- Add a GPU compaction/top-N star catalog kernel from the local-max mask.
- Implement device-side asterism matching/transform scoring using the resident star catalogs.
- Wire resident registration to use GPU-generated transforms before GPU warp/integration.

Clean-room compliance:
- Compliant. This gate implements a generic local-maximum candidate detector and does not read or copy official WBPP/PJSR source.
- Public astroalign documentation was checked only to choose the correct open-source algorithm family; no source was copied.
