# Bounded Master Accumulator Checkpoint

- Date: 2026-05-12
- Scope: Bound master-frame tile memory by replacing per-tile 3D frame stacks with a fixed-size float64 accumulator.
- Related gates: strengthens Gate 5 and Gate 12 out-of-core behavior for large calibration-frame groups.

## Completed

- Reworked `_mean_stack_tile` to read one frame tile at a time and accumulate into a single tile-sized buffer.
- Added shape validation for each tile before accumulation.
- Added `tile_stack_mode: streaming_accumulator` to master bias/dark/flat metadata.
- Added a regression test that monkeypatches `numpy.stack` to fail, proving the master tile path no longer depends on building an in-memory tile stack.
- Updated memory-model and completion-audit docs.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/gpwbpp/engine/pipeline.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\gpwbpp.exe run --plan runs/real_m5_lum_subset/processing_plan.json --out runs/real_m5_lum_subset/gpwbpp_cuda_bounded_master_accumulator --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 1024`
- `.\\.venv\\Scripts\\gpwbpp.exe compare --gpwbpp runs/real_m5_lum_subset/gpwbpp_cuda_bounded_master_accumulator/integration/master_Lum.fits --reference runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median/integration/master_Lum.fits --out runs/real_m5_lum_subset/gpwbpp_cuda_bounded_master_accumulator/compare_vs_exact_flat_median.html`

## Test Results

- Pipeline fixture tests: 11 passed in 4.34 s.
- Full pytest: 54 passed in 5.77 s.
- Real M5/Lum subset CUDA run completed through integration in about 49 s wall time.
- Compare against the previous exact-flat-median GPWBPP output:
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

- `runs/real_m5_lum_subset/gpwbpp_cuda_bounded_master_accumulator/calibration_artifacts.json`
- `runs/real_m5_lum_subset/gpwbpp_cuda_bounded_master_accumulator/integration/master_Lum.fits`
- `runs/real_m5_lum_subset/gpwbpp_cuda_bounded_master_accumulator/compare_vs_exact_flat_median.html`
- `runs/real_m5_lum_subset/gpwbpp_cuda_bounded_master_accumulator/compare_vs_exact_flat_median.json`

## Known Limitations

- Master-frame combination is still mean-only in this pipeline path. Robust rejection for master calibration groups remains a future capability.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Continue reducing remaining full-frame stages and resume the PixInsight/WBPP black-box timing comparison once reference output is available.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The real-data run used only user-provided FITS inputs and GPWBPP-generated artifacts.
- The original data directory was not modified.
