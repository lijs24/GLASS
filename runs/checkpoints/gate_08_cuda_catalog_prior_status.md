# Gate 08 Increment: CUDA Catalog NCC Prior Window

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Extended CUDA catalog translation voting with optional
  `prior_dx/prior_dy/prior_radius_px`.
- The optional prior restricts candidate pair offsets to a radius around a
  coarse translation, intended for GPU NCC coarse estimate plus catalog
  subpixel refinement.
- Preserved existing unprioritized behavior by default.
- Added Python wrapper and CPU fallback support for prior windowing.
- Added benchmark `--catalog-prior-radius`; when set, the benchmark passes the
  CUDA NCC estimate as the catalog prior.
- Added CUDA regression coverage for prior-window catalog voting.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check benchmarks\compare_astroalign_gpu_alignment.py src\glass_cuda.py tests\test_gpu_registration_search.py
cmd /c ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && "<repo>\.venv\Scripts\python.exe" -m cmake --build build\native-cuda --config Debug"
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_gpu_warp_vs_cpu.py tests\test_gpu_star_detect.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --out runs\alignment_compare\astroalign_vs_gpu_alignment_catalog_prior_synth.json --width 512 --height 512 --synthetic-dx 7 --synthetic-dy -5 --max-shift 16 --catalog-stars 64 --catalog-threshold-sigma 6 --catalog-tolerance-px 1 --catalog-prior-radius 2
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\glass_runs\final_m38_h_200\glass_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --catalog-max-shift 20 --catalog-stars 64 --catalog-threshold-sigma 6 --catalog-tolerance-px 3 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_alignment_catalog_prior_m38_crop_061_080.json
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_cuda_run\calib_cache\calibrated\calibrated_F000061.fits --moving C:\glass_runs\final_m38_h_200\glass_cuda_run\calib_cache\calibrated\calibrated_F000080.fits --center-crop 1024 --max-shift 128 --catalog-max-shift 20 --catalog-grid-cols 8 --catalog-grid-rows 8 --catalog-threshold-sigma 6 --catalog-tolerance-px 3 --catalog-prior-radius 4 --out runs\alignment_compare\astroalign_vs_gpu_alignment_grid_catalog_prior_m38_crop_061_080.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Ruff: all checks passed.
- Native CUDA build: passed.
- Targeted CUDA registration/warp/star tests: 16 passed.
- Full pytest: 97 passed.
- Synthetic catalog-prior comparison:
  - Astroalign: 0.3050 s.
  - CUDA integer NCC: 0.0996 s, 3.06x faster than astroalign.
  - CUDA catalog + prior + bilinear warp: 0.0116 s, 26.19x faster than
    astroalign.
  - Catalog accepted: true, 53 mutual inliers, RMS 0.0.
- M38 top-catalog prior comparison:
  - Astroalign: 0.3142 s.
  - CUDA integer NCC: 0.1238 s, 2.54x faster than astroalign.
  - CUDA catalog + prior + bilinear warp: 0.0367 s, 8.57x faster than
    astroalign.
  - Catalog accepted: false, only 2 mutual inliers.
- M38 grid-catalog prior comparison:
  - Astroalign: 0.3573 s.
  - CUDA integer NCC: 0.1290 s, 2.77x faster than astroalign.
  - CUDA grid catalog + prior + bilinear warp: 0.0357 s, 10.01x faster than
    astroalign.
  - Catalog accepted: false, only 4 mutual inliers.
  - Pixel RMS improved to 67.81 versus astroalign 72.35 and integer NCC 81.49,
    but the match evidence remains below the configured inlier gate.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/alignment_compare/astroalign_vs_gpu_alignment_catalog_prior_synth.json`
- `runs/alignment_compare/astroalign_vs_gpu_alignment_catalog_prior_m38_crop_061_080.json`
- `runs/alignment_compare/astroalign_vs_gpu_alignment_grid_catalog_prior_m38_crop_061_080.json`

## Known Limitations

- Prior windowing improves diagnostics but does not solve real-data catalog
  robustness by itself.
- M38 grid-prior result has promising pixel RMS but insufficient mutual inliers,
  so it remains rejected.
- Rotation, scale, affine, homography, and descriptor-level geometric matching
  are still missing.

## Next Step

- Add descriptor/asterism matching or a second-stage geometric verifier so real
  catalog matches can satisfy both pixel RMS and inlier-count gates.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Astroalign is used only as an open-source behavioral comparison reference.
- Original input data directories were not modified.
