# Gate 8 Incremental Checkpoint: Star-Core Guarded CUDA Alignment

## Gate

Gate 8: Registration

This is an incremental checkpoint inside Gate 8. Gate 8 remains open because the star-core guard is currently CPU control logic and still needs a pure CUDA implementation for the final resident pipeline.

## Completed Contents

- Added star-core candidate scoring to the astroalign-vs-GLASS benchmark path.
- The CUDA multi-seed pixel refinement still computes per-candidate refined matrices and image metrics.
- A new star-core metric samples bright reference pixels and re-scores refined candidate transforms against the moving image with bilinear sampling.
- Candidate selection now records:
  - original pixel-metric selected seed,
  - star-core selected seed,
  - inlier slack used for eligibility,
  - star-core sampled pixel count and elapsed time,
  - device-only and full algorithm timings.
- Added unit coverage for the guarded seed selector.

## Commands Run

```powershell
.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py

.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v38_star_core_top16.json" --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 16 --catalog-pixel-refine-radius 1.0 --catalog-pixel-refine-coarse-step 0.25 --catalog-pixel-refine-fine-radius 0.25 --catalog-pixel-refine-fine-step 0.0625 --catalog-pixel-refine-coarse-stride 4 --catalog-pixel-refine-final-stride 1

git diff --check
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- `tests\test_benchmarks.py`: `5 passed`
- Full suite: `141 passed in 7.14s`
- `git diff --check`: passed

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM reported by GLASS benchmark: 97886 MiB

## Real Pair Benchmark Summary

Artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v38_star_core_top16.json`

Input:

- Reference: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits`
- Moving: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits`
- Shape: `6422 x 9600`

Key timings:

- astroalign total: `9.604354 s`
- astroalign apply transform: `2.856713 s`
- GLASS resident CUDA autonomous alignment, device-only: `3.355058 s`
- GLASS resident CUDA autonomous alignment, full algorithm including CPU star-core guard: `6.023375 s`
- GLASS resident CUDA autonomous alignment, upload plus full algorithm: `6.062937 s`
- GLASS resident CUDA same-transform warp using astroalign matrix, device-only: `0.007274 s`

Observed speedups:

- Autonomous resident CUDA alignment vs astroalign total:
  - device-only: `2.863x`
  - full algorithm including CPU star-core guard: `1.595x`
  - upload plus full algorithm: `1.584x`
- Same-transform resident CUDA warp vs astroalign apply: `392.71x`

Agreement with astroalign:

- Autonomous resident CUDA agreement: passed
- Translation delta: `0.366166 px`
- Output RMS difference: `29.396845 ADU`
- Thresholds: translation `<= 0.5 px`, output RMS difference `<= 55.0 ADU`

## Known Limitations

- The star-core guard is intentionally honest but not final: it runs as CPU control logic over sampled bright pixels.
- `top_k=16` was needed on this pair to keep the correct transform basin available under current catalog candidate instability.
- The CUDA candidate search still has run-to-run variability in the top candidate set; this checkpoint records a passing benchmark but does not claim registration is fully production-stable.
- The next implementation step should move star-core metric evaluation to CUDA/resident memory and reduce candidate-selection nondeterminism.

## Next Step

- Implement a CUDA resident star-core candidate metric so the guarded transform selection no longer downloads or scores bright pixels on CPU.
- Stabilize catalog candidate ranking/top-K generation enough that `top_k=8` or similar remains reliable across repeated runs.
- Promote the guarded selection from benchmark diagnostics into the registration stage once the pure CUDA metric is available.

## Clean-room Compliance

Compliant. This checkpoint used GLASS source, astroalign as an open-source behavioral reference, generated benchmark artifacts, and user-provided FITS data. No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
