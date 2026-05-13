# Gate 08 Incremental Status: Resident GPU Star-Core Alignment Compare

Date: 2026-05-13

## Gate

Gate 8: Registration, incremental checkpoint for astroalign vs GLASS CUDA alignment on one real calibrated image pair.

## Completed

- Added resident CUDA star-core candidate scoring for similarity transform candidates.
- Exposed `ResidentCalibratedStack.star_core_metrics_candidates_to_reference(...)` through the native binding and Python wrapper.
- Updated `benchmarks/compare_astroalign_gpu_alignment.py` to report:
  - strict matrix + output agreement against astroalign;
  - output-only agreement;
  - best GLASS CUDA method by agreement class.
- Ran the same real calibrated FITS pair through astroalign and GLASS CUDA resident alignment:
  - reference: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits`
  - moving: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits`
  - shape: `6422 x 9600`
- Best balanced benchmark artifact:
  - `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v42_top32.json`

## Commands

```powershell
.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_benchmarks.py

.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v42_top32.json" --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 32 --catalog-pixel-refine-radius 1.0 --catalog-pixel-refine-coarse-step 0.25 --catalog-pixel-refine-fine-radius 0.25 --catalog-pixel-refine-fine-step 0.0625 --catalog-pixel-refine-coarse-stride 4 --catalog-pixel-refine-final-stride 1

git diff --check
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests: `30 passed in 1.50s`
- Full test suite: `142 passed in 7.09s`
- `git diff --check`: passed; only CRLF normalization warnings from Git on Windows.

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: available

## Benchmark Result

astroalign:

- total: `9.568878 s`
- find transform: `6.708765 s`
- apply transform: `2.860113 s`

Best strict GLASS CUDA resident alignment (`catalog_similarity_top_k=32`):

- method: `glass_cuda_resident_catalog_similarity_pixel_refined`
- strict matrix + output agreement: passed
- total resident algorithm: `6.587991 s`
- device work: `6.492506 s`
- speedup vs astroalign total: `1.452x`
- upload-inclusive speedup vs astroalign total: `1.444x`
- translation delta vs astroalign: `0.204752 px`
- output RMS diff vs astroalign-applied output: `24.089787 ADU`
- selected seed rank: `20`
- selected seed inliers: `11`

Warp-only resident CUDA using astroalign's matrix:

- speedup vs astroalign apply transform: `414.858x`

## Known Limitations

- Top-k candidate count has a correctness/performance tradeoff:
  - `top_k=16` can be faster and output-consistent, but on this pair it may miss strict matrix agreement.
  - `top_k=32` passed strict matrix + output agreement while staying faster than astroalign overall.
  - `top_k=64` also passed but was slower than astroalign because candidate refinement scanned too many full-frame hypotheses.
- Candidate ranking still needs a stronger GPU-side geometric/photometric prior so the correct seed rises earlier without brute-force larger top-k.
- This is a two-frame alignment benchmark, not the final 200-light end-to-end WBPP/GLASS comparison.

## Next Step

- Move more candidate pruning into GPU-resident scoring so strict agreement can pass with a smaller top-k.
- Feed this alignment path into the multi-frame registration stage and then run a larger calibrated-cache alignment/integration benchmark.

## Clean-Room Compliance

Compliant. This checkpoint used GLASS code, astroalign as an open-source comparison library, and user-generated FITS data/artifacts. No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
