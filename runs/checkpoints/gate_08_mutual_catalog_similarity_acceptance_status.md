# Gate 08 Increment: Mutual Catalog Similarity Scoring Acceptance

Date: 2026-05-13

## Completed contents

- Changed CUDA catalog-similarity candidate scoring to count mutual nearest-neighbor star matches under each candidate transform instead of one-way nearest-reference hits.
- Kept the guarded CUDA inlier-refit pass from the previous increment.
- Changed the benchmark default pixel-refine fine step to `0.0625 px` after real-pair validation showed the previous `0.125 px` step was too coarse near the agreement threshold.
- Updated documentation with the accepted real-pair artifact and current limitations.

## Commands run

- `cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v22_mutual_score_pixel_refine_accept.json"`

## Test results

- Targeted CUDA registration/resident tests: `33 passed in 0.17s`
- Full suite: `134 passed in 7.13s`
- `git diff --check`: passed, with only Windows LF-to-CRLF warnings.
- Native CUDA build completed successfully. CUDA Toolkit emitted codepage warnings from NVIDIA headers, but the extension linked.

## Real pair benchmark

Artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v22_mutual_score_pixel_refine_accept.json`

Input pair:

- Reference: `calibrated_S000061.fits`
- Moving: `calibrated_S000062.fits`
- Shape: `6422 x 9600`

Key timing:

- astroalign total: `9.6961 s`
- astroalign apply transform: `2.9049 s`
- raw GLASS CUDA grid-top catalog similarity: `2.9564 s`
- pixel-refined catalog similarity plus CUDA warp: `6.4166 s`
- pixel-refine metric search only: `6.3286 s`
- pixel-refined CUDA warp: `0.0880 s`

Acceptance diagnostics:

- `catalog_similarity_pixel_refined_agreement_vs_astroalign.passed`: `true`
- translation delta: `0.4818 px` (limit `0.5 px`)
- scale delta: `0.000095` (limit `0.001`)
- rotation delta: `0.000070 rad` (limit `0.001 rad`)
- output median absolute difference vs astroalign apply: `8.32 ADU`
- output RMS difference vs astroalign apply: `38.53 ADU` (limit `55 ADU`)
- common valid pixels: `61,619,160`

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97,886 MiB

## Known limitations

- This validates one real M38 pair, not the full 200-frame stack.
- The accepted path still uses a CPU-orchestrated loop over CUDA matrix-metric kernels for pixel refinement; it should be fused into a CUDA search kernel for production.
- The result is clean-room and does not use astroalign control points, but astroalign remains the open-source reference for the agreement check.
- Full registration pipeline integration still needs to use this accepted path across all frames with failure handling and run-state artifacts.

## Next step

- Integrate the accepted mutual-catalog + pixel-metric refinement path into the actual registration stage, then run it across a larger real subset before the full 200-light benchmark.

## Clean-room compliance

- This increment used GLASS code and the open-source astroalign package only as an external comparison target.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation material.
- Original image data were read only; generated benchmark artifacts were written under `C:\glass_runs`.
