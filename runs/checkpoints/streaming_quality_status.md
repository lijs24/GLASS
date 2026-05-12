# Streaming Quality Metrics Checkpoint

- Date: 2026-05-12
- Scope: Replace full-frame calibrated-light reads in the quality stage with tile-based metric and star-detection passes.
- Related gates: strengthens Gate 7 and Gate 12 out-of-core behavior.

## Completed

- Added streaming quality measurement for calibrated FITS outputs.
- Added exact background median computation through a temporary `memmap` scratch file.
- Added tile mean/std accumulation in the same scan pass.
- Added second-pass star detection with a 1-pixel tile halo so local-maximum checks work across tile boundaries.
- Passed the CLI `--tile-size` value into the quality stage.
- Added metadata to `frame_quality.json`: `metric_source`, `tile_size`, `tile_count`, `pixel_count`, and `median_method`.
- Added tests comparing streaming quality metrics to the CPU in-memory baseline and checking pipeline quality artifacts.
- Updated memory-model and completion-audit docs.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/gpwbpp/engine/quality.py src/gpwbpp/cli.py tests/test_cpu_star_detect.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_cpu_star_detect.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\gpwbpp.exe run --plan runs/real_m5_lum_subset/processing_plan.json --out runs/real_m5_lum_subset/gpwbpp_cuda_streaming_quality --backend cuda --until-stage quality --tile-size 1024`

## Test Results

- Focused quality/pipeline tests: 14 passed in 5.06 s.
- Full pytest: 55 passed in 7.33 s.
- Real M5/Lum subset CUDA run completed through quality in about 36 s wall time.
- Real-data quality artifact:
  - `metric_source`: `streaming_tile_reader`
  - `median_method`: `median_scratch_memmap`
  - `tile_size`: 1024
  - `tile_count`: 70 per light frame
  - `pixel_count`: 61651200 per light frame
  - `reference_frame_id`: `R000004`
- Temporary `quality_scratch` directory was removed after completion.

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/real_m5_lum_subset/gpwbpp_cuda_streaming_quality/frame_quality.json`
- `runs/real_m5_lum_subset/gpwbpp_cuda_streaming_quality/calibration_artifacts.json`
- `runs/real_m5_lum_subset/gpwbpp_cuda_streaming_quality/run_state.json`

## Known Limitations

- The quality stage still uses a simple threshold/local-maximum detector and placeholder FWHM/eccentricity estimates.
- Star candidate retention is capped at `max_stars`, currently 500, matching the baseline detector behavior.
- Registration still uses full-frame FFT phase correlation and remains the next major full-frame path.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Reduce the registration full-frame path, likely by using cached streaming quality/star data or a bounded preview/FFT strategy.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The real-data run used only user-provided FITS inputs and GPWBPP-generated artifacts.
- The original data directory was not modified.
