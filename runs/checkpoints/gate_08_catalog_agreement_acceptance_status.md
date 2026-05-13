# Gate 08 Increment: Catalog Agreement Acceptance Guard

Date: 2026-05-13

## Completed

- Tightened the astroalign-vs-GLASS benchmark acceptance semantics.
- `benchmarks/compare_astroalign_gpu_alignment.py` now marks the GLASS-owned
  CUDA catalog-similarity path as `accepted=false` when its transform/output
  fails `catalog_similarity_agreement_vs_astroalign`, even if the internal
  catalog fit reports enough inliers.
- Added pytest assertions that the synthetic benchmark records and passes the
  external agreement check.
- Updated registration documentation with the latest real-pair artifact and the
  current accepted/failed interpretation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py tests\test_gpu_registration_search.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits --moving C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits --out C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v14_gridtop_acceptance.json --max-shift 16 --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-min-inliers 6 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01
```

## Test Results

- Targeted registration/benchmark tests: 18 passed in 1.42 s.

## Real Pair Benchmark

Output artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v14_gridtop_acceptance.json`

Key results:

- astroalign total: 9.568 s.
- astroalign transform search: 6.745 s.
- astroalign apply: 2.824 s.
- CUDA standalone matrix warp using astroalign matrix: 0.143 s.
- CUDA resident matrix warp using astroalign matrix, device-only: 0.0070 s.
- CUDA resident matrix warp including upload plus device work: 0.0463 s.
- CUDA similarity fit from astroalign control points plus warp: 0.089 s.
- GLASS-owned CUDA grid-top catalog similarity: 2.964 s.
- Grid-top catalog-similarity speedup vs astroalign total: 3.23x.
- Grid-top catalog-similarity agreement vs astroalign: failed.
- `glass_cuda_catalog_similarity.accepted`: false.
- Agreement failure details: translation delta 1.56 px, output median absolute
  difference 16.71 ADU, output RMS difference 75.68 ADU.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97,886 MiB.

## Known Limitations

- This increment does not make pure GPU catalog registration production-ready.
- It prevents a fast but astroalign-disagreeing catalog transform from being
  reported as accepted in benchmark artifacts.
- The next registration step remains a stronger GPU matcher/validator that
  preserves the grid-top speed while converging to the astroalign-like transform.

## Next Step

- Add a stronger GPU-side seed validation score, likely image/NCC-backed or
  descriptor/RANSAC-style, before accepting catalog similarity transforms.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or used.
- astroalign was used only as an open-source external reference/backend.
- Input FITS files were read only; no source data directory was modified.
