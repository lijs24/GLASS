# Gate 08 Multi-Seed CUDA Pixel Refine

- Gate: 08 registration
- Date: 2026-05-13
- Scope: moved catalog top-K pixel arbitration closer to the resident-GPU design by refining multiple seed matrices with one reference/moving image upload.

## Completed

- Added native `refine_matrix_translation_candidates_with_metrics_f32`.
- Added Python compatibility wrapper and `gpwbpp.gpu.registration` export.
- Updated the astroalign comparison benchmark to use the multi-seed CUDA refine API.
- Changed catalog top-K diagnostics to keep candidates from multiple inlier-score levels before filling with global top candidates. This prevents a single wrong inlier cluster from occupying every seed slot.
- Added CUDA test coverage for multi-seed selection.

## Commands

- `cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release"`
- `.venv\Scripts\python.exe -m compileall -q src\gpwbpp_cuda.py src\gpwbpp\gpu\registration.py benchmarks\compare_astroalign_gpu_alignment.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_benchmarks.py`
- `.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v28_diverse_topk_multiseed_refine.json" --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 8`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Targeted CUDA/benchmark tests: 24 passed.
- Full suite: 136 passed.
- Native CUDA build: succeeded.
- `git diff --check`: no whitespace errors.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Real Alignment Benchmark

- Reference: `calibrated_S000061.fits`
- Moving: `calibrated_S000062.fits`
- Shape: 6422 x 9600.
- Astroalign total: 9.6190 s.
- GPWBPP CUDA diverse top-K + multi-seed pixel refine + matrix warp: 1.9038 s.
- Multi-seed refine time: 1.8151 s.
- Final CUDA warp time: 0.0888 s.
- Speedup: 5.05x vs astroalign total.
- Agreement: passed current strict benchmark criteria.
- Translation delta vs astroalign: 0.373 px.
- Output RMS diff vs astroalign apply: 32.98 ADU.
- Selected seed rank: 1.
- Output file: `C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v28_diverse_topk_multiseed_refine.json`

## Known Limitations

- Top-K candidate diagnostics still download all catalog candidate buffers when enabled. The next production step is an on-device top-K reducer.
- Multi-seed refine uploads the reference and moving images only once, but each seed still launches coarse/fine candidate scoring separately. A later kernel can score all seed-offset combinations in one larger launch.
- The catalog seed generator remains sensitive to star-catalog ambiguity on this dense field. Pixel arbitration fixes the tested pair, but more real-pair coverage is needed before calling registration Gate 8 complete for all data.

## Next Step

- Move diverse top-K selection onto the GPU and add a resident-stack method that scores candidate seed matrices directly from frames already in VRAM.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source code was read or used.
- Only GPWBPP code, open Python dependencies, CUDA kernels, and user-generated calibrated FITS artifacts were used.
