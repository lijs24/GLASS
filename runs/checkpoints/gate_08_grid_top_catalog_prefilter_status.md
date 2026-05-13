# Gate 08 Increment: CUDA Grid-Top Catalog Prefilter

Date: 2026-05-13

## Completed

- Added a CUDA star-catalog prefilter that keeps the top-K local maxima per
  image grid cell and then applies CUDA-side minimum-distance suppression:
  `star_grid_top_nms_candidates_f32`.
- Exposed the prefilter through the native pybind module, the Python
  `glass_cuda` compatibility wrapper, and
  `glass.gpu.registration.register_similarity_from_star_catalogs_f32`.
- Extended `benchmarks/compare_astroalign_gpu_alignment.py` so the same two
  calibrated FITS frames can compare:
  - astroalign transform search and apply;
  - GLASS CUDA matrix warp using astroalign's transform;
  - GLASS CUDA similarity fit using astroalign's matched control points;
  - GLASS-owned CUDA NCC translation diagnostics;
  - GLASS-owned CUDA catalog-similarity diagnostics with grid-top prefilter.
- Added `catalog_similarity_agreement_vs_astroalign` to the benchmark artifact,
  so speed results are separated from transform/output agreement.
- Updated CUDA backend and registration docs with the current capability and
  limitation.

## Commands Run

```powershell
cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release'
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_benchmarks.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits --moving C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits --out C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v13_gridtop_agreement.json --max-shift 16 --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-min-inliers 6 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Targeted registration/benchmark tests: 18 passed in 1.39 s.
- Full suite: 129 passed in 7.00 s.

## Real Pair Benchmark

Input frames:

- `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits`
- `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits`

Output artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v13_gridtop_agreement.json`

Key results:

- astroalign total: 9.569 s.
- astroalign transform search: 6.753 s.
- astroalign apply: 2.817 s.
- CUDA standalone matrix warp using the astroalign matrix: 0.141 s.
- CUDA resident matrix warp device-only using the astroalign matrix: 0.0070 s.
- CUDA resident matrix warp including upload plus device work: 0.0444 s.
- CUDA similarity fit from astroalign control points plus warp: 0.092 s.
- GLASS-owned CUDA grid-top catalog similarity: 2.916 s.
- Grid-top catalog-similarity speedup vs astroalign total: 3.28x.
- Grid-top catalog-similarity agreement vs astroalign: failed.
- Agreement failure details: translation delta 1.15 px, output median absolute
  difference 13.27 ADU, output RMS difference 62.18 ADU.

Interpretation:

- GPU pixel resampling is clearly faster than astroalign's pixel application and
  numerically close when both use the same transform.
- The fast grid-top catalog prefilter gives the right performance direction for
  a future all-GPU matcher.
- The current grid-top catalog-similarity matcher is not yet accepted as an
  astroalign replacement because it can pick a transform that is internally
  plausible but disagrees with the open-source reference.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97,886 MiB.

## Known Limitations

- This increment does not complete production registration. It adds a fast
  prefilter and a benchmark agreement check.
- The global top-NMS pure GPU catalog-similarity path previously produced an
  astroalign-close matrix on this pair, but it was slower than astroalign.
- The grid-top path is faster than astroalign on this pair, but the current
  two-star seed scorer still needs stronger descriptor/RANSAC-style scoring,
  better inlier validation, or an NCC/image metric reduction before it can be
  the default all-GPU registration path.

## Next Step

- Implement a robust GPU asterism/descriptor matcher or a hybrid seed validation
  stage that keeps the grid-top speed but rejects near-identity false positives
  before warp/integration.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or used.
- astroalign was used only as an open-source external reference/backend for the
  same two input images.
- Input FITS files were read only; no source data directory was modified.
