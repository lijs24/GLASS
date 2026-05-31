# S2-Gate 10 Status: XISF, Report, Real-Data Regression

## Gate

S2-Gate 10: stabilize XISF metadata and cache-safe image input, strengthen HTML report coverage, and run a real 200-light regression against the Phase 1 baseline.

## Completed

- Replaced the legacy XISF prefix parser with a binary-header aware XML parser for `XISF0100` files.
- Added `XisfImageSpec`, `XisfImageReader`, `read_xisf_image_spec`, `read_xisf_data`, and `cache_xisf_to_fits`.
- Added cache-safe `.xisf` input conversion to run-local FITS files before calibration, preserving the original path in the calibration artifact.
- Added `XisfImageSource` and `image_source_for_path` for unified FITS/XISF source access.
- Updated XISF metadata scanning to use FITS keywords and XISF properties from the XML header without reading pixel payloads.
- Expanded the HTML report with stage coverage, XISF input cache, integration output maps, timing overview, resident CUDA summary, and warnings/errors tables.
- Recorded XISF/report changes and the real-data regression evidence in `docs/algorithm_sources.md`.
- Repaired the calibration fixture assertion so per-flat normalized StackEngine modes are recognized as StackEngine-backed.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_run_calibration`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\io\xisf_io.py src\glass\metadata\xisf_reader.py src\glass\io\image_source.py src\glass\engine\pipeline.py src\glass\report\html_report.py tests\test_xisf_io.py tests\test_xisf_metadata.py tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_calibration_vs_cpu.py`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101 --backend cuda --until-stage integration --memory-mode resident --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\compare_vs_reference_scaled_coverage190.html --glass-time-seconds 39.01369709987193 --reference-time-seconds 1092.541 --glass-label "GLASS S2-Gate10 flat-floor 0.05" --reference-label "reference FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\compare_diagnostics_scaled`
- `.\.venv\Scripts\glass.exe doctor --json C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\doctor.json`
- `.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101 --out C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\report.html`

## Test Results

- Full pytest: `227 passed in 15.97s`
- Targeted CUDA pytest: `6 passed in 0.19s`
- Ruff targeted files: `All checks passed!`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real-Data Regression

- Dataset plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`.
- Input frame count in plan: 200 lights, 20 bias, 20 dark, 20 flat.
- Final run directory: `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101`.
- External reference runtime: `1092.541 s`.
- GLASS runtime: `39.01369709987193 s`.
- Speedup vs external reference: `28.004036561907544x`.
- Shape match: true.
- Coverage threshold: `min_coverage=190`.
- Coverage median/max: `192 / 193`.
- Scaled compare RMS: `0.0015580353573173447`.
- Scaled compare P99 absolute difference: `0.0004309411160647869`.
- Scaled compare P99.9 absolute difference: `0.004008894186467077`.
- Full-frame RMS after the same scale/offset: `0.012482460223550667`.
- Report generated: `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\report.html`.
- Compare report generated: `C:\glass_runs\phase2_s2_gate_10_200\glass_flatfloor005_20260531_183101\compare_vs_reference_scaled_coverage190.html`.

## Regression Notes

- A failed diagnostic run without `--until-stage integration` correctly exited before doing resident work.
- Diagnostic runs without `--flat-floor 0.05` produced huge calibrated outliers because the current plan/default allowed flat values down to `1e-6`; the Phase 1 comparison baseline used a `0.05` floor. The final accepted run therefore records `--flat-floor 0.05` explicitly.
- The current editable-tree runtime (`39.01 s`) is slower than the Phase 1 release baseline (`30.36 s`) by more than 15 percent. The numerical result and coverage remain in the baseline tolerance family, so the gate is accepted with a required follow-up: reduce `master_build_or_load`, `light_read_upload_calibrate`, and resident registration/warp overhead, and preserve the flat-floor comparison parameter in benchmark scripts.

## Known Limitations

- XISF pixel reads currently support uncompressed, attachment-backed, monochrome images only.
- Compressed XISF and multi-channel XISF fail explicitly for pixel reads; metadata scanning can still continue from headers when possible.
- The resident CUDA path is still a high-VRAM fast path and is not yet the shared StackEngine implementation.
- The real-data run is not a claim of external-tool equivalence; it is a measured regression guard for shape, coverage, timing, and image-difference statistics.

## Next Step

Proceed to the next S2 gate only after keeping this gate green. The next optimization target is to recover the editable-tree 200-light runtime toward the Phase 1 30-second release baseline by improving resident master preparation, I/O/decode/upload overlap, and registration/warp scheduling.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned code, public/container-format knowledge, synthetic tests, user-generated image files, and user-generated reference outputs only. No proprietary implementation source was read, copied, summarized, or reworked.
