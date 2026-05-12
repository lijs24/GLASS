# Gate 08 Increment: Resident Star-Catalog NCC Prior

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Added `--resident-star-prior ncc` for resident CUDA star-catalog registration.
- The resident pipeline can now estimate a coarse/subpixel NCC translation on
  the GPU, pass it as a compact `(dx, dy, radius)` prior to the GPU
  star-catalog pair-offset scorer, and record the prior diagnostics per frame.
- Added `--resident-star-prior-radius-px`.
- Fixed a CUDA catalog scorer bug: if the prior/max-shift filters reject all
  pair offsets, the kernel now returns NaN shift and zero inliers instead of
  silently refining around `(0, 0)`.
- Added a regression test covering the no-valid-prior-window case.
- Rebuilt the native CUDA extension.
- Ran the real M38 subset12 resident star-catalog auto-threshold + NCC-prior
  diagnostic.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cuda_resident_stack.py
.\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -Dpybind11_DIR=<venv pybind11> -DCMAKE_MAKE_PROGRAM=<venv ninja> -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120
.\.venv\Scripts\cmake.exe --build build\native-cuda --config Release
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_resident_cuda_run.py tests\test_cuda_resident_stack.py
.\.venv\Scripts\gpwbpp.exe run --plan "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\processing_plan.json" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_star_auto_nccprior2_fixed_subset12" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration translation_star_catalog --resident-star-threshold 0 --resident-star-max-candidates 128 --resident-star-tolerance-px 1.0 --resident-registration-max-shift 32 --resident-star-grid-cols 16 --resident-star-grid-rows 8 --resident-star-prior ncc --resident-star-prior-radius-px 2
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

## Test Result

- Ruff: all checks passed.
- Native CUDA build: passed.
- Targeted CUDA registration/resident tests: 26 passed.
- Full pytest: 108 passed in 5.90 s.
- `git diff --check`: no whitespace errors.

## Real Data Diagnostic

- Run path:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_star_auto_nccprior2_fixed_subset12`
- Input plan:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset12\processing_plan.json`
- Frame counts: 12 light frames with existing subset calibration frames.
- Status counts: 1 reference, 11 ok, 0 failed.
- Runtime: 21.43 s.
- Compared with the existing resident NCC subset12 registration:
  - mean star-catalog-vs-NCC translation delta: about 1.00 px
  - max delta: about 1.84 px
- Interpretation: NCC prior removes false zero-shift catalog matches and keeps
  the star-catalog path useful for inlier/RMS diagnostics, but resident NCC
  remains the stronger current alignment driver for the full 200-light timing
  comparison until richer star descriptors/similarity matching are implemented.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend loaded: true.

## Known Limitations

- Star-catalog registration remains translation-only.
- NCC prior improves robustness but does not make this a full astroalign-style
  asterism/similarity/affine solver.
- Some real subset frames still differ from NCC by about 1-2 px, so the current
  full pipeline should keep using resident NCC/subpixel registration for image
  alignment and use star-catalog diagnostics as supporting evidence.

## Next Step

- Promote the resident NCC/subpixel path as the default high-VRAM alignment mode
  for the 200-light comparison.
- Continue GPU star matching with bounded descriptors or asterism-style matching
  before using star-catalog transforms as the primary full-run alignment.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- The implementation uses project-owned CUDA/Python code and black-box project
  artifacts only.
- Input data directories were not modified.
