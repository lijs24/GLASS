# Optimization Gate 09: resident H2D timing and pinned async probe

## Gate

Optimization Gate 09.

## Completed

- Added a stream-capable CUDA calibration launcher:
  - `gpwbpp_calibrate_tile_f32_launch_stream(...)`.
- Added resident calibration timing APIs to the native backend:
  - `ResidentCalibratedStack.calibrate_frame_timed(...)`
  - `ResidentCalibratedStack.calibrate_frame_pinned_async(...)`
  - `ResidentCalibratedStack.calibrate_frame_pinned_async_timed(...)`
  - `ResidentCalibratedStack.host_pinned_bytes`
- Added a persistent pinned host staging buffer for resident light upload.
- Released the Python GIL while resident CUDA upload/calibration work is in flight.
- Added CLI switch:
  - `--resident-h2d-mode pageable|pinned_async`
- Added resident artifact timing fields:
  - `light_host_copy_to_pinned`
  - `light_h2d`
  - `light_calibrate_store`
  - `light_h2d_calibrate_store`
  - per-frame summaries for each field
  - `resident_io_pipeline.h2d_mode`
  - `resident_io_pipeline.host_pinned_bytes`
- Added tests for pinned async calibration correctness and CLI artifact reporting.

## Commands Run

```powershell
cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 >nul && ""C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe"" --build build\native-cuda --config Release --target _gpwbpp_cuda_native"
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py src\gpwbpp_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m gpwbpp.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pageable --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\python.exe -m gpwbpp.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_async --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4\compare_vs_wbpp_fastintegration_scaled_coverage190.html --gpwbpp-time-seconds 36.18390980002005 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP pageable timed coarse4" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 8.764434957115609e-06 --gpwbpp-offset 0.0006274500691899127 --gpwbpp-coverage-map C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4\compare_vs_wbpp_fastintegration_scaled_coverage190.html --gpwbpp-time-seconds 36.90693649998866 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP pinned_async coarse4" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 8.764434957115609e-06 --gpwbpp-offset 0.0006274500691899127 --gpwbpp-coverage-map C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\python.exe -m gpwbpp.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4\manifest.json --gpwbpp-run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_acceptance_audit_pageable_timed_coarse4.json --markdown runs\benchmarks\m38_acceptance_audit_pageable_timed_coarse4.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\python.exe -m gpwbpp.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4\manifest.json --gpwbpp-run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_acceptance_audit_pinnedasync_coarse4.json --markdown runs\benchmarks\m38_acceptance_audit_pinnedasync_coarse4.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
git diff --check
```

## Test Results

- Native CUDA build: passed.
- Ruff targeted check: passed.
- Targeted pytest: `18 passed`.
- Full pytest: `182 passed`.
- Acceptance audit:
  - pageable timed coarse4: passed, `30.194111306329717x` vs WBPP.
  - pinned_async coarse4: passed, `29.602592455766022x` vs WBPP.

## M38 Benchmark Results

Common M38 settings:

- 200 H light frames in the run.
- 193 active high-coverage integration support after explicit WBPP-failed-frame exclusions.
- Registration: `similarity_cuda_triangle`.
- Reference selector input: `LIGHT_H_0136`.
- Excluded frame tokens: `LIGHT_H_0100`, `LIGHT_H_0153` through `LIGHT_H_0158`.
- Star threshold: `350`.
- Candidate cap: `48`.
- Grid: `24 x 16`.
- Pixel refine coarse stride: `4`.
- Pixel refine final stride: `8`.
- Warp: `lanczos3`, clamp threshold `0.30`.
- Rejection: `winsorized_sigma`.

Prior best:

- Run: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort`
- Total run timing: `39.175000299932435 s`.
- Light read/upload/calibrate loop: `24.71270719997119 s`.
- Resident registration/warp: `11.312835899647325 s`.
- WBPP speedup: `27.888729843912323x`.

Current pageable timed:

- Run: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_timed_coarse4`
- Total run timing: `36.18390980002005 s`.
- Light read/upload/calibrate loop: `21.45984599995427 s`.
- Light read/decode wait: `0.0020489002345129848 s`.
- Worker read/decode total: `77.99267109972425 s`.
- H2D host timing: `7.612917700000001 s`.
- Calibration/store timing: `0.1548118 s`.
- Combined native H2D/calibrate/store timing: `8.701377599383704 s`.
- Resident registration/warp: `11.324737299699336 s`.
- WBPP compare:
  - RMS diff: `0.001558294284488301`.
  - P99 abs diff: `0.00043095467146486016`.
  - Coverage fraction at min coverage 190: `0.9574613308418977`.
  - Shape match: `true`.
  - Speedup vs WBPP FastIntegration: `30.194111306329717x`.

Current pinned async:

- Run: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedasync_coarse4`
- Total run timing: `36.90693649998866 s`.
- Light read/upload/calibrate loop: `22.192292000050656 s`.
- Light read/decode wait: `0.0020458000944927335 s`.
- Worker read/decode total: `78.14045599894598 s`.
- Host copy to pinned staging: `5.9013148 s`.
- Async H2D CUDA-event timing: `2.034694550514221 s`.
- Calibration/store CUDA-event timing: `0.14219862389564514 s`.
- Combined native H2D/calibrate/store timing: `8.943673300091177 s`.
- Resident registration/warp: `11.3142429998843 s`.
- Pinned host staging size: `246604800 bytes`.
- WBPP compare:
  - RMS diff: `0.001558294284488301`.
  - P99 abs diff: `0.00043095467146486016`.
  - Coverage fraction at min coverage 190: `0.9574613308418977`.
  - Shape match: `true`.
  - Speedup vs WBPP FastIntegration: `29.602592455766022x`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- VRAM: about `97887 MiB`.
- Native backend: yes.

## Known Limitations

- `pinned_async` currently stages NumPy FITS data into a persistent pinned buffer with a CPU memcpy before async H2D.
- This proves and instruments the pinned/async path, but it is not yet the final I/O pipeline. The extra host copy costs about `5.9 s` on the M38 run, so pageable remains the faster default for now.
- The next real optimization should decode/read directly into reusable pinned buffers or a pinned ring buffer, then overlap CPU decode, H2D, and calibration through multiple CUDA streams.
- The detailed pageable split uses host-side timing around synchronous `cudaMemcpy`; pinned async uses CUDA-event H2D/kernel timings.

## Next Step

- Implement a true pinned ring-buffer prefetcher:
  - reusable pinned slabs per in-flight frame,
  - direct or one-copy FITS decode into the pinned slot where feasible,
  - async H2D on one or more streams,
  - calibration/store stream scheduling,
  - explicit ready/completed events,
  - back-pressure by RAM/VRAM budgets.
- After that, re-benchmark M38 and keep pageable as the fallback if direct pinned decode cannot beat it.

## Clean-Room Compliance

- Compliant.
- No PixInsight/WBPP/PJSR official source was read, copied, summarized, or used.
- The WBPP comparison used user-generated black-box output artifacts only.
- Original input image directories were not modified.
