# Optimization Gate 10: resident read/decode profiling split

## Gate

Optimization Gate 10.

## Completed

- Split resident light-frame read profiling into:
  - `fits_open`
  - `fits_materialize_decode`
  - existing `read_decode_worker` total
  - existing main-thread `read_decode` wait
- Added artifact fields:
  - `timing_s.light_fits_open`
  - `timing_s.light_fits_materialize_decode`
  - `timing_s.per_frame_fits_open_mean`
  - `timing_s.per_frame_fits_materialize_decode_mean`
  - `fine_timing.seconds.light_fits_open_total`
  - `fine_timing.seconds.light_fits_materialize_decode_total`
  - `fine_timing.per_frame_seconds.fits_open`
  - `fine_timing.per_frame_seconds.fits_materialize_decode`
- Kept the old `light_read_decode_worker` field as the total worker-side FITS open plus materialization/decode path.
- Added CLI smoke assertions for the new fields.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_cuda_resident_stack.py::test_resident_stack_pinned_async_calibration_matches_pageable_and_cpu
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m gpwbpp.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_readprofile_coarse4 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pageable --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_readprofile_coarse4\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4\integration\resident_master_H.fits --out C:\gpwbpp_runs\final_m38_h_200\readprofile_vs_pageable_timed_coarse4_compare.html --gpwbpp-label readprofile --reference-label pageable_timed --clip-low 0 --clip-high 65535
```

## Test Results

- Ruff targeted check: passed.
- Targeted pytest: `2 passed`.
- Full pytest: `182 passed`.

## M38 Benchmark Results

Run:

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_readprofile_coarse4`

Timing:

- Total run timing: `37.132812800002284 s`.
- Light read/upload/calibrate loop: `22.42552849999629 s`.
- Main-thread prefetch wait: `0.00191430002450943 s`.
- Worker read/decode total: `80.4956505006412 s`.
- FITS open/memmap/header setup total: `0.6490617007948458 s`.
- FITS materialize/decode/scale total: `74.12465520005208 s`.
- H2D host timing: `8.0884698 s`.
- Calibration/store timing: `0.1535256 s`.
- Combined H2D/calibrate/store timing: `9.14413370063994 s`.
- Resident registration/warp: `11.293794700060971 s`.

Correctness smoke against the prior pageable timed run:

- Direct compare report:
  - `C:\gpwbpp_runs\final_m38_h_200\readprofile_vs_pageable_timed_coarse4_compare.html`
  - `C:\gpwbpp_runs\final_m38_h_200\readprofile_vs_pageable_timed_coarse4_compare.json`
- Direct difference:
  - P50/P90/P99/P99.9 absolute diff: `0.0`.
  - RMS diff: `1.520365561548271`.
  - The non-zero RMS is from sparse extreme pixels; the profiling change did not alter the algorithmic path.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Native backend: yes.

## Known Limitations

- `fits_materialize_decode` includes memmap page-in, dtype conversion, BSCALE/BZERO handling, and BLANK masking. It is not a pure storage read timer.
- This confirms that the next I/O optimization target is materialization/decode into resident or pinned buffers, not FITS open/header parsing.
- The resident pipeline still needs a true pinned ring-buffer prefetcher and multi-stream H2D/calibration scheduling to satisfy the full optimization goal.

## Next Step

- Implement reusable pinned slots filled by prefetch workers, then submit async H2D from those slots without a main-thread host-to-pinned copy.
- After that, consider multiple raw-light device buffers and stream scheduling so H2D for frame N+1 can overlap calibration/store for frame N.

## Clean-Room Compliance

- Compliant.
- No PixInsight/WBPP/PJSR official source was read, copied, summarized, or used.
- Original input image directories were not modified.
