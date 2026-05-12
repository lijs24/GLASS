# Gate 08 Increment: CUDA Matrix Alignment Metrics

Date: 2026-05-13

## Completed

- Added `matrix_alignment_metrics_f32(reference, moving, matrix, sample_stride=1)`.
- The native CUDA implementation scores a moving-to-reference transform without
  downloading a full warped image.
- Metrics returned:
  - valid pixel count;
  - sampled pixel count;
  - RMS difference;
  - mean absolute difference;
  - normalized cross-correlation.
- Added a CPU fallback in `src/gpwbpp_cuda.py` so CPU-only import paths remain
  functional.
- Exposed the primitive through `gpwbpp.gpu.registration`.
- Extended `benchmarks/compare_astroalign_gpu_alignment.py` to record GPU matrix
  metrics for both the astroalign matrix and the GPWBPP-owned catalog-similarity
  matrix.
- Added pytest coverage comparing the metric RMS to the existing CUDA matrix
  warp output and verifying that a bad transform scores worse than a good one.

## Commands Run

```powershell
cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release'
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_benchmarks.py
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits --moving C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits --out C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v15_matrix_metrics.json --max-shift 16 --catalog-stars 64 --catalog-grid-top-cols 24 --catalog-grid-top-rows 16 --catalog-grid-top-per-cell 4 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-min-inliers 6 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01
```

## Test Results

- Targeted registration/benchmark tests: 20 passed in 1.41 s.

## Real Pair Benchmark

Output artifact:

- `C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v15_matrix_metrics.json`

Key results:

- astroalign total: 9.761 s.
- astroalign apply: 2.930 s.
- CUDA standalone matrix warp using astroalign matrix: 0.143 s.
- CUDA resident matrix warp using astroalign matrix, device-only: 0.0071 s.
- CUDA matrix metrics for the astroalign matrix: 0.0416 s, RMS 76.35 ADU, NCC
  0.9767.
- GPWBPP-owned CUDA grid-top catalog similarity: 2.954 s.
- CUDA matrix metrics for the grid-top catalog-similarity matrix: 0.0928 s, RMS
  97.07 ADU, NCC 0.9623.
- The grid-top catalog-similarity path remained `accepted=false`, with the
  matrix metric providing a compact GPU-side reason to reject it.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97,886 MiB.

## Known Limitations

- The metric primitive validates one matrix at a time; it does not yet score
  many candidate matrices inside the catalog-similarity kernel.
- Standalone calls upload the two images. A future resident method should score
  frames already stored in `ResidentCalibratedStack`.

## Next Step

- Use `matrix_alignment_metrics_f32` as a validation stage for the top catalog
  candidates, then move the same scoring into a resident/high-VRAM path to avoid
  repeated uploads.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or used.
- astroalign was used only as an open-source external reference/backend.
- Input FITS files were read only; no source data directory was modified.
