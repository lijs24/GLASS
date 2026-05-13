# Gate 08 Increment: Catalog Similarity Refit and Pixel-Metric Translation Refinement

Date: 2026-05-13

## Completed contents

- Added a guarded CUDA refit pass after `estimate_similarity_from_catalogs_f32` selects its best two-star similarity seed.
- The refit gathers nearest-neighbor star inliers for the selected seed on the GPU, fits a similarity matrix from those inlier sums, and applies it only when the star-catalog residual does not worsen.
- Added diagnostics: `refined_inliers`, `refit_status`, `refit_status_code`, and `refit_rms_px`.
- Added `glass.gpu.registration.refine_matrix_translation_with_metrics_f32(...)`, a CUDA pixel-metric translation refinement helper for an existing matrix.
- Extended `benchmarks/compare_astroalign_gpu_alignment.py` to record a pixel-refined catalog-similarity path separately from the raw catalog-similarity seed.
- Added focused tests for guarded catalog refit diagnostics and pixel-metric translation refinement.

## Commands run

- `cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v20_gridtop_pixel_refine.json"`
- `git diff --check`

## Test results

- Targeted CUDA registration/resident tests: `33 passed in 0.17s`
- Full suite: `134 passed in 7.10s`
- Native CUDA build completed successfully. CUDA Toolkit emitted codepage warnings from NVIDIA headers, but the extension linked.

## Real pair benchmark

Artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v20_gridtop_pixel_refine.json`

Input pair:

- Reference: `calibrated_S000061.fits`
- Moving: `calibrated_S000062.fits`
- Shape: `6422 x 9600`

Key timing:

- astroalign total: `9.5811 s`
- astroalign apply transform: `2.8675 s`
- raw GLASS CUDA grid-top catalog similarity: `2.9638 s`
- pixel-refined catalog similarity plus CUDA warp: `4.1595 s`
- pixel-refine metric search only: `4.0721 s`
- pixel-refined CUDA warp: `0.0874 s`

Key diagnostics:

- Raw catalog similarity still failed agreement.
- Pixel-refined catalog similarity also failed agreement, but improved the direct image RMS difference versus astroalign apply to `58.89 ADU`.
- Current agreement gate remains stricter than the result:
  - translation delta: `1.25 px`, limit `0.5 px`
  - output RMS diff: `58.89 ADU`, limit `55 ADU`
- Pixel-refined metric against reference: RMS `83.31 ADU`, NCC `0.9722`

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97,886 MiB

## Known limitations

- This is not yet an accepted pure-GPU replacement for astroalign's asterism matcher.
- The guarded refit helps controlled cases and prevents obvious catalog-residual regressions, but nearest-neighbor star inliers are still too weak on the M38 pair.
- Pixel-metric translation refinement improves the output image comparison but does not reliably recover the astroalign-close matrix; a fused GPU search over better asterism/descriptor candidates is still needed.
- The pixel-refine helper is CPU-orchestrated over CUDA metric kernels and should later become a fused CUDA search for production-scale throughput.

## Next step

- Implement a GPU asterism or descriptor matcher that proposes cleaner similarity candidates before pixel-metric scoring. The immediate target is passing the existing `catalog_similarity_pixel_refined_agreement_vs_astroalign` gate on the M38 pair without using astroalign control points.

## Clean-room compliance

- This increment used GLASS code and the open-source astroalign package only as an external comparison target.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation material.
- Original image data were read only; generated benchmark artifacts were written under `C:\glass_runs`.
