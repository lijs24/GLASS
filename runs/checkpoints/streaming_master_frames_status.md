# Streaming Master Frames Checkpoint

- Date: 2026-05-12
- Scope: Reworked the high-level calibration pipeline so master bias, dark, and flat frames are generated tile-by-tile with `FitsImageReader` and `FitsTileWriter` instead of keeping full master arrays in CPU memory.
- Related gates: strengthens Gate 5 and Gate 12 out-of-core behavior; this is a supplemental checkpoint, not a claim that the full WBPP-like target is complete.

## Completed

- Added streaming mean stacking for master bias, dark, and raw flat frames.
- Added optional tile-wise bias subtraction while building master darks and flats.
- Added streaming flat normalization and recorded the normalization scalar/method in `calibration_artifacts.json`.
- Changed light calibration to read master bias/dark/flat tiles from FITS paths instead of slicing full in-memory arrays.
- Added pipeline fixture assertions that all generated masters record `streaming: true` and the requested tile size.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_fixture.py tests/test_cpu_calibration.py tests/test_gpu_calibration_vs_cpu.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe run --plan runs/real_m5_lum_subset/processing_plan.json --out runs/real_m5_lum_subset/glass_cuda_streaming_masters --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 1024`
- `.\\.venv\\Scripts\\glass.exe compare --glass runs/real_m5_lum_subset/glass_cuda_streaming_masters/integration/master_Lum.fits --reference runs/real_m5_lum_subset/glass_cuda_tile_reader_manual/integration/master_Lum.fits --out runs/real_m5_lum_subset/glass_cuda_streaming_masters/compare_vs_tile_reader.html`

## Test Results

- Focused pytest: 14 passed in 4.31 s.
- Full pytest: 52 passed in 5.97 s.
- Real M5/Lum subset CUDA run completed through integration in about 48 s wall time.
- Compare against previous tile-reader GLASS output:
  - `shape_match`: true
  - `rms_diff`: 7.595273494720459
  - `mean_diff`: -1.4079874753952026
  - `max_abs_diff`: 20776.0

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/real_m5_lum_subset/glass_cuda_streaming_masters/calibration_artifacts.json`
- `runs/real_m5_lum_subset/glass_cuda_streaming_masters/integration/master_Lum.fits`
- `runs/real_m5_lum_subset/glass_cuda_streaming_masters/compare_vs_tile_reader.html`
- `runs/real_m5_lum_subset/glass_cuda_streaming_masters/compare_vs_tile_reader.json`

## Known Limitations

- Median flat normalization remains exact for small images up to 32M pixels. Larger images use a weighted tile-median approximation to avoid reading the full master flat into RAM. This can produce small output differences compared with the previous full-frame CPU path.
- Mean stacking is tile streaming, but a single tile stack still holds all frames for that tile. Very large frame counts will need a bounded batch accumulator.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Implement an exact out-of-core median/quantile path for large flat normalization, or make the normalization policy explicit per run when strict reproducibility against a CPU baseline is more important than peak memory.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The real-data run used only user-provided FITS inputs and GLASS-generated artifacts.
- The original data directory was not modified.
