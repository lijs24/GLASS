# Optimization Gate 11: resident pinned host ring upload path

## Gate

Optimization Gate 11.

## Completed

- Added a reusable pinned-host ring for resident light prefetch.
- Added `FitsImageReader.read_full_into(output)` so prefetch workers can decode/materialize FITS image data directly into caller-owned `float32` buffers.
- Added native CUDA `host_pinned_empty_f32(height, width)` with `cudaHostAlloc`.
- Added resident native `calibrate_frame_host_async_timed(...)` for async H2D from a supplied host buffer without the previous pageable-to-pinned staging copy.
- Added CLI support for `--resident-h2d-mode pinned_ring` on `run` and `audit`.
- Added artifact fields:
  - `resident_io_pipeline.h2d_mode`
  - `resident_io_pipeline.host_pinned_bytes`
  - `resident_io_pipeline.prefetch_host_pinned_bytes`
  - `resident_io_pipeline.stack_host_pinned_bytes`
  - existing fine timing fields now show `light_host_copy_to_pinned = 0.0` for `pinned_ring`.
- Added CUDA/unit coverage for the host-async calibration path and resident CLI smoke coverage for pinned-ring artifacts.

## Commands Run

```powershell
cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 >nul && ""C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe"" --build build\native-cuda --config Release --target _gpwbpp_cuda_native"
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\io\fits_io.py src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py src\gpwbpp_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_host_async_calibration_accepts_pinned_host_array tests\test_cuda_resident_stack.py::test_resident_stack_pinned_async_calibration_matches_pageable_and_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m gpwbpp.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4\compare_vs_wbpp_fastintegration_scaled_coverage190.html --gpwbpp-time-seconds 31.245748999994248 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP pinned_ring coarse4" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 8.764434957115609e-06 --gpwbpp-offset 0.0006274500691899127 --gpwbpp-coverage-map C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pageable_readprofile_coarse4\integration\resident_master_H.fits --out C:\gpwbpp_runs\final_m38_h_200\pinnedring_vs_pageable_readprofile_coarse4_compare.html --gpwbpp-label pinned_ring --reference-label pageable_readprofile --clip-low 0 --clip-high 65535
.\.venv\Scripts\python.exe -m gpwbpp.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4\manifest.json --gpwbpp-run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_acceptance_audit_pinnedring_coarse4.json --markdown runs\benchmarks\m38_acceptance_audit_pinnedring_coarse4.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
git diff --check
```

## Test Results

- Native CUDA build: passed.
- Ruff targeted check: passed.
- Targeted pytest: `3 passed`.
- Full pytest: `183 passed`.
- `git diff --check`: passed, with only expected Windows LF-to-CRLF warnings.

## M38 Benchmark Results

Pinned-ring run:

- Run directory: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4`
- Frame set: 200 lights, 20 bias, 20 dark, 20 flat.
- Active integrated frames: 193.
- Total run timing: `31.245748999994248 s`.
- Previous initial resident optimization baseline: about `111.95 s`.
- Previous pageable readprofile run: `37.132812800002284 s`.
- PixInsight/WBPP FastIntegration black-box timing: `1092.541 s`.
- Speedup vs pageable readprofile: about `1.1884x`.
- Speedup vs WBPP FastIntegration: `34.9660685042372x`.

Fine timing:

- Light read/upload/calibrate loop: `16.431756100035273 s`.
- Main-thread prefetch wait: `2.1812842993531376 s`.
- Worker read/decode total: `45.62251679995097 s`.
- FITS open/memmap/header setup total: `0.25094049924518913 s`.
- FITS materialize/decode/scale total: `40.825801101280376 s`.
- H2D device timing total: `2.613508836746216 s`.
- Calibration/store device timing total: `0.14888355255126956 s`.
- Combined H2D/calibrate/store timing: `2.8165741993580014 s`.
- Host pageable-to-pinned copy timing: `0.0 s`.
- Resident registration/warp: `11.310889499611221 s`.
- Resident integration: `0.28695549990516156 s`.

Pinned memory:

- H2D mode: `pinned_ring`.
- Prefetch slots: 16.
- Prefetch workers: 8.
- Prefetch pinned host bytes: `3945676800`.
- Stack pinned host bytes: `0`.

## Correctness and Compare Results

Against WBPP FastIntegration:

- Compare report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- RMS diff: `0.001558294284488301`.
- P99 absolute diff: `0.00043095467146486016`.
- P99.9 absolute diff: `0.004013502578251386`.
- Shape match: true.
- Coverage fraction with minimum coverage 190: `0.9574613308418977`.

Against the previous pageable readprofile GPWBPP run:

- Compare report: `C:\gpwbpp_runs\final_m38_h_200\pinnedring_vs_pageable_readprofile_coarse4_compare.html`
- Master SHA-256 matched exactly:
  - `F9F7E173B5BA7EC582DB7460B7F051E0B75B2E2A48C0ADF035940A071CD79CC2`
- Coverage-map SHA-256 matched exactly:
  - `B4C4F26984157B012624008EFC8D3618BB320E91B773F12F8107A875FFFB6168`

Acceptance audit:

- Markdown: `runs\benchmarks\m38_acceptance_audit_pinnedring_coarse4.md`
- JSON: `runs\benchmarks\m38_acceptance_audit_pinnedring_coarse4.json`
- Status: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Known Limitations

- The pinned ring removes the extra pageable-to-pinned host copy, but FITS materialization/decode still copies astropy memmap data into `float32` output buffers.
- The calibration/upload path still uses one resident raw-light device buffer and one calibration stream; H2D for frame N+1 is not yet overlapped with calibration/store for frame N through multiple device staging buffers.
- The pinned ring currently consumes about 3.95 GB of pinned host RAM for 16 full-resolution M38 slots; the next iteration should enforce this from the configured RAM budget.
- Registration/warp was not further optimized in this gate; the current dominant device-side registration components are still moving catalog generation, triangle pixel refine, and warp.

## Next Step

- Add multiple raw-light device staging buffers and stream/event scheduling so read/decode, H2D, calibration/store, and resident stack writes overlap more aggressively.
- Bound pinned ring depth by RAM budget and image size instead of requiring manual tuning.
- Continue resident registration/warp batching, especially CUDA Graph or stream scheduling around catalog/descriptor/scoring/refine/warp.

## Clean-Room Compliance

- Compliant.
- No PixInsight/WBPP/PJSR official source was read, copied, summarized, or used.
- PixInsight/WBPP was used only as a black-box timing/output reference through user-generated artifacts.
- Original input image directories were not modified.
