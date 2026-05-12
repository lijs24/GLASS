# Gate 08 Increment: CUDA Subpixel NCC Translation Refinement

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Added a native CUDA subpixel translation estimator:
  `estimate_translation_subpixel_ncc_f32(reference, moving, center_dx,
  center_dy, radius_steps, step)`.
- The estimator refines a coarse translation by scoring a bounded fractional
  offset grid with bilinear sampling and normalized cross-correlation.
- Added Python wrapper and CPU fallback support.
- Extended the astroalign comparison benchmark with:
  - refinement-only `gpwbpp_cuda_subpixel`;
  - fair combined `gpwbpp_cuda_ncc_subpixel`, which includes integer NCC search
    plus subpixel refinement time.
- Added CUDA regression coverage for subpixel NCC refinement.
- Documented the current CUDA registration scope and limitations.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\compare_astroalign_gpu_alignment.py src\gpwbpp_cuda.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_gpu_warp_vs_cpu.py
$pybind = (& .\.venv\Scripts\python.exe -m pybind11 --cmakedir).Trim(); $ninja = (Resolve-Path .\.venv\Scripts\ninja.exe).Path; $cmd = 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -Dpybind11_DIR="' + $pybind + '" -DCMAKE_MAKE_PROGRAM="' + $ninja + '" -DCMAKE_CUDA_COMPILER="C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release'; cmd /c $cmd
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --width 512 --height 512 --synthetic-dx 7 --synthetic-dy -5 --max-shift 16 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_alignment_subpixel_synth.json
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --subpixel-radius-steps 4 --subpixel-step 0.25 --catalog-max-shift 20 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-threshold-sigma 6 --catalog-tolerance-px 3 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_alignment_subpixel_m38_crop_061_080.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: all checks passed.
- Native CUDA build: passed.
- Targeted CUDA registration/warp tests: 10 passed.
- Full pytest: 98 passed.
- Synthetic 512x512 comparison:
  - Astroalign: 0.2579 s, RMS 0.0085.
  - CUDA integer NCC: 0.0652 s, RMS 0.0.
  - CUDA NCC + subpixel: 0.0669 s, RMS 0.0, 3.86x faster than astroalign.
  - CUDA grid catalog path: 0.0093 s, accepted, 39 mutual inliers.
- M38 calibrated 1024x1024 crop comparison:
  - Astroalign: 0.3101 s, RMS 72.35, 24 matched control points.
  - CUDA integer NCC: 0.1264 s, RMS 81.49.
  - CUDA NCC + subpixel: 0.1308 s, RMS 63.80, 2.37x faster than astroalign.
  - CUDA grid catalog path: 0.0340 s, rejected by quality gate; image RMS was
    worse than integer NCC for this run.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/alignment_compare/astroalign_vs_gpu_alignment_subpixel_synth.json`
- `runs/alignment_compare/astroalign_vs_gpu_alignment_subpixel_m38_crop_061_080.json`

## Known Limitations

- The accepted CUDA result in this increment is still translation-only.
- The subpixel NCC refinement is a bounded brute-force grid search, not a full
  descriptor/asterism registration model.
- The benchmark currently copies host arrays into wrappers; it is not yet the
  fully resident VRAM pipeline requested for the final 200+ light test.
- Rotation, scale, affine, homography, Lanczos/resampling policy, and full
  resident transform application remain future gates.
- The real-data catalog path is still diagnostic-only until it passes both
  inlier and image-RMS gates.

## Next Step

- Convert the registration comparison into the resident high-VRAM path and add
  descriptor-level GPU star matching so catalog registration can replace NCC
  fallback on real data.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Astroalign is used only as an open-source behavioral comparison reference.
- Original input data directories were not modified.
