# Streaming Registration Preview Checkpoint

- Date: 2026-05-12
- Scope: Replace full-frame calibrated-light reads in the registration stage with bounded tile-built previews for CPU phase correlation.
- Related gates: strengthens Gate 8 and Gate 12 out-of-core behavior.

## Completed

- Added `_registration_preview`, which reads calibrated FITS images by tile and computes block-mean previews when the source image exceeds the preview budget.
- Updated registration to run phase correlation on the bounded preview and scale the resulting translation back to source pixels.
- Recorded `registration_image_source`, `preview_scale`, `preview_shape`, `tile_size`, and `tile_count` in `registration_results.json`.
- Passed CLI `--tile-size` into registration.
- Added tests for preview block means and pipeline registration metadata.
- Updated memory-model, completion-audit, and registration-model docs.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/glass/engine/registration.py src/glass/cli.py tests/test_cpu_registration.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_cpu_registration.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe run --plan runs/real_m5_lum_subset/processing_plan.json --out runs/real_m5_lum_subset/glass_cuda_streaming_registration --backend cuda --until-stage registration --tile-size 1024`

## Test Results

- Focused registration/pipeline tests: 14 passed in 4.66 s.
- Full pytest: 56 passed in 6.33 s.
- Real M5/Lum subset CUDA run completed through registration in about 52 s wall time.
- Real-data registration artifact:
  - `method`: `phase_correlation_streaming_preview`
  - `registration_image_source`: `streaming_preview`
  - `preview_scale`: 10
  - `preview_shape`: `[643, 960]`
  - `tile_size`: 1024
  - `tile_count`: 70 per frame

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/real_m5_lum_subset/glass_cuda_streaming_registration/registration_results.json`
- `runs/real_m5_lum_subset/glass_cuda_streaming_registration/frame_quality.json`
- `runs/real_m5_lum_subset/glass_cuda_streaming_registration/calibration_artifacts.json`
- `runs/real_m5_lum_subset/glass_cuda_streaming_registration/run_state.json`

## Known Limitations

- Registration is still translation-only in the executable pipeline path.
- The bounded preview sacrifices fine subpixel/full-resolution phase detail on large images; it is an out-of-core baseline, not a final high-precision registration model.
- Similarity, affine, homography, and robust star-match RANSAC remain future gates.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Improve registration precision with star-match transforms or multi-resolution refinement, then continue toward the PixInsight/WBPP timing comparison when reference output is available.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The real-data run used only user-provided FITS inputs and GLASS-generated artifacts.
- The original data directory was not modified.
