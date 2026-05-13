# Gate 08 Increment: Fused CUDA Pixel-Metric Translation Refine

Date: 2026-05-13

## Completed contents

- Added native CUDA candidate-grid scoring for
  `refine_matrix_translation_with_metrics_f32(...)`.
- The native path uploads the reference/moving images once, scores all coarse
  offsets in one CUDA launch, then scores all fine offsets in one CUDA launch.
- The Python compatibility wrapper keeps a CPU/per-candidate fallback when the
  native extension is unavailable.
- `glass.gpu.registration.refine_matrix_translation_with_metrics_f32(...)`
  now delegates to the top-level `glass_cuda` API, so tile-mode
  `cuda_catalog` registration uses the fused native primitive when CUDA is
  available.
- Updated CUDA and registration documentation.

## Commands run

- `cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py`
- `.\.venv\Scripts\python.exe -m glass.cli run --plan runs\cuda_catalog_cli_smoke_plan.json --out runs\cuda_catalog_cli_smoke_run_fused_refine --backend cuda --until-stage registration --tile-size 32 --registration-method cuda_catalog --registration-preview-max-dimension 128`
- `.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v23_fused_pixel_refine.json"`
- `.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-pixel-refine-coarse-stride 1 --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v24_fused_pixel_refine_stride1.json"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`

## Test results

- Native CUDA build completed successfully. CUDA Toolkit emitted codepage
  warnings from NVIDIA headers, but the extension linked.
- CUDA registration tests: `20 passed in 1.13s`
- CUDA registration/resident tests: `34 passed in 0.22s`
- Benchmark tests: `3 passed in 1.67s`
- Pipeline/CLI tests: `15 passed in 4.01s`
- Full suite: `135 passed in 7.05s`
- `git diff --check`: passed, with only Windows LF-to-CRLF warnings.

## CLI smoke result

- Run output: `runs\cuda_catalog_cli_smoke_run_fused_refine`
- `registration_results.json` summary:
  - `method`: `cuda_catalog`
  - statuses: `ok`, `reference`
  - `pixel_refine.model`: `cuda_matrix_metric_translation_refine_grid`
  - `pixel_refine.metrics.model`: `matrix_alignment_metrics_cuda_candidate_grid`

## Real pair benchmark

Artifacts:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v23_fused_pixel_refine.json`
- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v24_fused_pixel_refine_stride1.json`

Key v23 timing:

- astroalign total: `9.7234 s`
- pixel-refined catalog similarity plus CUDA warp: `0.3277 s`
- pixel-refine metric search only: `0.2354 s`
- pixel-refined CUDA warp: `0.0923 s`
- speedup of pixel-refined catalog path vs astroalign total: `29.67x`

Key v23 diagnostics:

- `pixel_refine.model`: `cuda_matrix_metric_translation_refine_grid`
- output median absolute difference vs astroalign apply: `8.45 ADU`
- output RMS difference vs astroalign apply: `35.28 ADU`
- strict matrix agreement did not pass: translation delta `0.619 px`, limit
  `0.5 px`

The fused primitive is therefore validated for speed and numerical operation,
but robust catalog seed selection still needs work before this path can be
treated as the production replacement for astroalign on the full real stack.

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97,886 MiB

## Known limitations

- Candidate-grid scoring is batched into CUDA launches, but best-candidate
  reduction is still finalized on CPU from compact per-candidate statistics.
- The real-pair speed benchmark did not pass the strict astroalign matrix
  agreement threshold in this run because the upstream catalog similarity seed
  selected a different near-solution. Image RMS difference improved, but the
  matrix delta criterion remains important for large-stack robustness.
- The resident high-VRAM path does not yet use this fused matrix-refine
  primitive directly between resident frames.

## Next step

- Stabilize catalog seed selection across real frames, likely by keeping several
  top catalog seeds and applying fused pixel-metric scoring before accepting a
  transform, then move the same primitive into resident-frame registration.

## Clean-room compliance

- This increment used GLASS code, CUDA kernels written in this repository, and
  open numerical image-alignment concepts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or used.
- Original image data were read only; generated artifacts were written under
  `runs\` and `C:\glass_runs\`.
