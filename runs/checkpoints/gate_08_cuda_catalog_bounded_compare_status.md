# Gate 08 Increment: Bounded CUDA Catalog Alignment Compare

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Extended CUDA catalog translation scoring with optional
  `max_abs_dx/max_abs_dy` search bounds.
- Preserved the existing unbounded API behavior by default.
- Added Python wrapper parameters and CPU fallback support for the same bounds.
- Extended the astroalign comparison benchmark with a second GPU path:
  `gpwbpp_cuda_catalog`.
- The catalog benchmark path now runs GPU top-star extraction, GPU bounded
  catalog offset voting/refinement, and CUDA bilinear translation warp.
- Added `accepted` and `warnings` diagnostics so weak catalog matches are not
  silently treated as valid alignment.
- Added a CUDA regression test for bounded catalog search.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\compare_astroalign_gpu_alignment.py src\gpwbpp_cuda.py tests\test_gpu_registration_search.py
cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_gpu_warp_vs_cpu.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --out runs\alignment_compare\astroalign_vs_gpu_alignment_catalog_bounded_final.json --width 512 --height 512 --synthetic-dx 7 --synthetic-dy -5 --max-shift 16 --catalog-stars 64 --catalog-threshold-sigma 6 --catalog-tolerance-px 1
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\gpwbpp_runs\final_m38_h_200\gpwbpp_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --catalog-max-shift 20 --catalog-stars 64 --catalog-threshold-sigma 6 --catalog-tolerance-px 3 --out runs\alignment_compare\astroalign_vs_gpu_alignment_catalog_bounded_final_m38_crop_061_080.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: all checks passed.
- Native CUDA build: passed.
- Targeted CUDA registration/warp tests: 8 passed.
- Full pytest: 95 passed.
- Synthetic comparison:
  - Astroalign: 0.3774 s.
  - CUDA integer NCC: 0.0731 s, 5.16x faster than astroalign.
  - CUDA catalog + bilinear warp: 0.0114 s, 33.16x faster than astroalign.
  - Catalog accepted: true, 53 mutual inliers, RMS 0.0.
- M38 calibrated crop comparison:
  - Astroalign: 0.4748 s.
  - CUDA integer NCC: 0.1176 s, 4.04x faster than astroalign.
  - CUDA catalog + bilinear warp: 0.0396 s, 11.99x faster than astroalign.
  - Catalog accepted: false, 3 mutual inliers below the configured minimum of 6.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/alignment_compare/astroalign_vs_gpu_alignment_catalog_bounded_final.json`
- `runs/alignment_compare/astroalign_vs_gpu_alignment_catalog_bounded_final_m38_crop_061_080.json`

## Known Limitations

- CUDA catalog alignment is still translation-only.
- The real M38 crop shows that the current local-maximum catalog needs stronger
  star selection/descriptor matching before it can replace astroalign-style
  registration on real data.
- The robust fallback for real crops remains CUDA integer NCC translation.
- Similarity, affine, homography, rotation/scale handling, and fully resident
  warp application remain future work.

## Next Step

- Add a GPU-friendly descriptor or grid-filtered star selection stage so real
  images produce enough consistent inliers before the bilinear warp is accepted.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Astroalign is used only as an open-source behavioral comparison reference.
- Original input data directories were not modified.
