# Streaming Integration Accumulator Checkpoint

- Date: 2026-05-12
- Scope: Bound integration tile memory for the common `rejection=none` weighted-mean path.
- Related gates: strengthens Gate 11 and Gate 12 out-of-core behavior.

## Completed

- Reworked integration so `rejection=none` uses streaming sum, weight-sum, and coverage accumulators.
- Kept tile stacks for sigma/winsorized rejection because those modes require per-pixel frame distributions.
- Added `tile_stack_mode` to integration outputs:
  - `streaming_accumulator` for no-rejection weighted mean.
  - `stack_for_rejection` for rejection modes.
- Added pipeline fixture assertions for both paths.
- Updated memory-model and completion-audit docs.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/glass/engine/integration.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_fixture.py tests/test_cpu_integration.py tests/test_gpu_integration_vs_cpu.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe run --plan runs/real_m5_lum_subset/processing_plan.json --out runs/real_m5_lum_subset/glass_cuda_streaming_integration --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 1024`
- `.\\.venv\\Scripts\\glass.exe compare --glass runs/real_m5_lum_subset/glass_cuda_streaming_integration/integration/master_Lum.fits --reference runs/real_m5_lum_subset/glass_cuda_bounded_master_accumulator/integration/master_Lum.fits --out runs/real_m5_lum_subset/glass_cuda_streaming_integration/compare_vs_bounded_master_accumulator.html`

## Test Results

- Focused integration tests: 16 passed in 4.18 s.
- Full pytest: 54 passed in 5.79 s.
- Real M5/Lum subset CUDA run completed through integration in about 51 s wall time.
- Compare against previous bounded-master-accumulator GLASS output:
  - `shape_match`: true
  - `rms_diff`: 0.0
  - `mean_diff`: 0.0
  - `max_abs_diff`: 0.0

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/real_m5_lum_subset/glass_cuda_streaming_integration/integration_results.json`
- `runs/real_m5_lum_subset/glass_cuda_streaming_integration/integration/master_Lum.fits`
- `runs/real_m5_lum_subset/glass_cuda_streaming_integration/compare_vs_bounded_master_accumulator.html`
- `runs/real_m5_lum_subset/glass_cuda_streaming_integration/compare_vs_bounded_master_accumulator.json`

## Known Limitations

- Rejection modes still build a per-tile frame stack. A future out-of-core rejection implementation should use multi-pass bounded statistics or disk-backed tile buffers.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Reduce remaining full-frame quality/registration paths, or resume the PixInsight/WBPP black-box timing comparison once reference output is available.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The real-data run used only user-provided FITS inputs and GLASS-generated artifacts.
- The original data directory was not modified.
