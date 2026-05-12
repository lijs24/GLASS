# Gate 07 Increment: CUDA Grid Star Catalog

- Gate: 07
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Added CUDA `star_grid_candidates_f32`.
- The kernel visits local maxima above threshold and keeps the brightest
  candidate in each image grid cell.
- Added Python wrapper and CPU fallback.
- Extended the astroalign comparison benchmark so the catalog path can use
  `--catalog-grid-cols/--catalog-grid-rows`.
- Added catalog acceptance diagnostics that reject catalog alignment when image
  RMS is worse than the integer-NCC fallback by more than 5%.
- Added a CUDA unit test for the grid selector.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\compare_astroalign_gpu_alignment.py src\gpwbpp_cuda.py tests\test_gpu_star_detect.py
cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py tests\test_gpu_registration_search.py tests\test_gpu_warp_vs_cpu.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --out runs\alignment_compare\astroalign_vs_gpu_alignment_grid_catalog_synth.json --width 512 --height 512 --synthetic-dx 7 --synthetic-dy -5 --max-shift 16 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-threshold-sigma 6 --catalog-tolerance-px 1
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --catalog-max-shift 20 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-threshold-sigma 6 --catalog-tolerance-px 3 --out runs\alignment_compare\astroalign_vs_gpu_alignment_grid_catalog_m38_crop_061_080_checked.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: all checks passed.
- Native CUDA build: passed.
- Targeted CUDA star/registration/warp tests: 15 passed.
- Full pytest: 96 passed.
- Synthetic grid-catalog comparison:
  - Astroalign: 0.2925 s.
  - CUDA integer NCC: 0.0792 s, 3.69x faster than astroalign.
  - CUDA grid catalog + bilinear warp: 0.0113 s, 25.86x faster than astroalign.
  - Catalog accepted: true, 39 mutual inliers, RMS 0.0.
- M38 calibrated crop comparison:
  - Astroalign: 0.3503 s.
  - CUDA integer NCC: 0.1279 s, 2.74x faster than astroalign.
  - CUDA grid catalog + bilinear warp: 0.0393 s, 8.90x faster than astroalign.
  - Catalog accepted: false because image RMS was worse than integer NCC.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/alignment_compare/astroalign_vs_gpu_alignment_grid_catalog_synth.json`
- `runs/alignment_compare/astroalign_vs_gpu_alignment_grid_catalog_m38_crop_061_080_checked.json`

## Known Limitations

- Grid distribution reduces global brightness bias but is not enough to make
  real-data catalog translation robust.
- The current catalog scorer is translation-only and lacks asterism/triangle
  descriptors, scale/rotation support, and robust geometric verification.
- Grid selection is currently exposed for standalone arrays, not yet as a
  resident stack method.

## Next Step

- Implement GPU-friendly asterism or descriptor matching so real star catalogs
  reject zero-shift/static-artifact coincidences before transform refinement.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Astroalign is used only as an open-source behavioral comparison reference.
- Original input data directories were not modified.
