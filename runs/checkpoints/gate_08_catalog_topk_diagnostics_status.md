# Gate 08 CUDA Catalog Top-K Alignment Diagnostic

- Gate: 08 registration
- Date: 2026-05-13
- Scope: added deterministic top-K catalog similarity seed export for the native CUDA registration backend, then used the benchmark harness to score multiple GPU catalog seeds with fused CUDA pixel metrics before a single final CUDA matrix warp.

## Completed

- `glass_cuda.estimate_similarity_from_catalogs_f32(..., top_k=N)` now returns `top_k` and `top_candidates` diagnostics.
- The native CUDA binding can optionally download candidate score/RMS buffers and select the best `N` candidates by inlier count then RMS.
- `benchmarks/compare_astroalign_gpu_alignment.py` has `--catalog-similarity-top-k`.
- The benchmark pixel-refine path evaluates the refit seed plus top-K catalog seeds with `refine_matrix_translation_with_metrics_f32`, records per-seed metrics, selects by final pixel RMS/NCC, and warps only the winning matrix.
- Added tests for top-K result shape and benchmark payload fields.

## Commands

- `cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_benchmarks.py`
- `.venv\Scripts\python.exe -m compileall -q benchmarks\compare_astroalign_gpu_alignment.py`
- `.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v25_topk_pixel_refine.json" --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01 --catalog-similarity-top-k 8`
- `.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits" --moving "C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits" --out "C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v26_single_seed_pixel_refine.json" --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Targeted CUDA/benchmark tests: 23 passed.
- Full suite: 135 passed.
- Native CUDA build: no work to do; existing build remained valid.
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
- Astroalign total: 9.6717 s in the top-K run.
- GLASS CUDA catalog top-K + pixel metric refine + matrix warp: 2.2133 s.
- Speedup: 4.37x vs astroalign total.
- Agreement: passed current strict benchmark criteria.
- Translation delta vs astroalign: 0.312 px.
- Output RMS diff vs astroalign apply: 30.88 ADU.
- Output file: `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v25_topk_pixel_refine.json`

The single-seed production-speed run remained much faster but selected an unstable catalog seed in this trial:

- GLASS CUDA single-seed pixel refine + matrix warp: 0.3231 s.
- Speedup: 30.12x vs astroalign total.
- Agreement: failed current strict criteria.
- Translation delta vs astroalign: 1.515 px.
- Output RMS diff vs astroalign apply: 78.83 ADU.
- Output file: `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v26_single_seed_pixel_refine.json`

## Known Limitations

- Top-K diagnostics currently download all catalog candidate score/RMS buffers when enabled. This is useful for audit and seed stabilization, but it is not the final production algorithm.
- The native best-candidate path can still choose a poor single seed on this real pair. Production registration should use either deterministic top candidate selection or an on-device top-K reducer before trusting the fit.
- Top-K pixel scoring repeats image uploads for each seed because the current refine wrapper is stateless. A resident-GPU version should keep the two frames in VRAM and score all seed grids without repeated host-device transfer.

## Next Step

- Convert top-K seed selection into a production CUDA path: deterministic on-device top-K reduction, resident-frame seed scoring, and one final warp from the selected matrix.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source code was read or used.
- Only GLASS code, open Python dependencies, synthetic/unit tests, and user-generated calibrated FITS artifacts were used.
