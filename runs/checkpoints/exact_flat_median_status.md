# Exact Out-of-Core Flat Median Checkpoint

- Date: 2026-05-12
- Scope: Replace the large-image `tile_median_approx` flat normalization path with an exact out-of-core median computed through a temporary `memmap` scratch file.
- Related gates: strengthens Gate 5 and Gate 12 reproducibility for large flats.

## Completed

- Added `_exact_median_scratch` for finite-pixel median calculation without loading a full FITS image into process memory.
- Updated flat normalization so large median-normalized flats report `normalization_method: median_scratch_memmap`.
- Added a regression test that verifies the scratch median matches `numpy.nanmedian` and cleans up its temporary file.
- Updated memory-model and completion-audit docs to reflect the streamed master-frame path.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/gpwbpp/engine/pipeline.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\gpwbpp.exe run --plan runs/real_m5_lum_subset/processing_plan.json --out runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 1024`
- `.\\.venv\\Scripts\\gpwbpp.exe compare --gpwbpp runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median/integration/master_Lum.fits --reference runs/real_m5_lum_subset/gpwbpp_cuda_tile_reader_manual/integration/master_Lum.fits --out runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median/compare_vs_tile_reader.html`

## Test Results

- Pipeline fixture tests: 10 passed in 4.21 s.
- Full pytest: 53 passed in 5.69 s.
- Real M5/Lum subset CUDA run completed through integration in about 50 s wall time.
- Compare against the previous full-frame/tile-reader GPWBPP output:
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

- `runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median/calibration_artifacts.json`
- `runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median/integration/master_Lum.fits`
- `runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median/compare_vs_tile_reader.html`
- `runs/real_m5_lum_subset/gpwbpp_cuda_exact_flat_median/compare_vs_tile_reader.json`

## Known Limitations

- Mean stacking is tile streaming, but a single tile stack still holds all frames for that tile. Very large frame counts still need a bounded batch accumulator.
- The exact median scratch file is disk-backed and may be slower than the previous approximate method on very large flats, but it restores numerical agreement with the previous exact full-frame path.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Add bounded batch accumulation for very large calibration-frame groups, then resume the PixInsight/WBPP black-box timing comparison once reference output is available.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The real-data run used only user-provided FITS inputs and GPWBPP-generated artifacts.
- The original data directory was not modified.
