# S2-Gate 501 Status: Direct Simple FITS Output Writer

## Gate

S2-Gate 501

## Completed Content

- Continued the Phase 2 resident CUDA performance path after Gate500.
- Ran a deeper prefetch probe first and did not promote it because the best
  observed variant was too small/noisy:
  - `control_v3_default`: `7.234865 s`
  - `prefetch48_workers16_batch16`: `7.192066 s`
  - `prefetch40_workers14_batch16`: `7.215550 s`
  - `prefetch48_workers16_batch32`: `7.221418 s`
  - `prefetch48_workers12_batch16`: `7.422777 s`
  - `prefetch64_workers20_batch16`: `7.582610 s`
- Added a direct simple-primary FITS writer for 2D GLASS output arrays.
- Supported direct dtypes:
  - `uint8`
  - `int16`
  - `int32`
  - `float32`
  - `float64`
- Unsupported shapes/dtypes continue to use Astropy `PrimaryHDU`.
- Resident output storage now records `writer_backend`.

## Files Changed

- `src/glass/io/fits_io.py`
- `src/glass/engine/resident_cuda.py`
- `tests/test_fits_io.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`

## Real 200-Light Validation

Run root:

`C:\glass_runs\phase2_s2_gate501_direct_fits_writer_ab_real\runs\default_v3_direct_fits`

Run settings:

- default runtime preset: `throughput-v3-io`
- resident registration: `similarity_cuda_triangle`
- warp interpolation: `lanczos3`
- output maps: `minimal`
- rejection: `winsorized_sigma`
- weighting: `none`
- LN: `off`

Timing:

- GLASS run timing total: `7.147139 s`
- resident integration stage: `7.144419 s`
- shell wall: `7.505 s`
- output write total: `0.548847800004296 s`
- master write breakdown: `0.548796399962157 s`
- Gate500 default output write for comparison: `0.68125790002523 s`
- output write improvement: about `0.1324101 s`
- WBPP black-box time: `1092.541 s`
- speedup vs WBPP by GLASS run timing: `152.8641040841657x`

Artifact evidence:

- `output_write.storage.master.writer_backend`: `direct_simple_primary`
- `output_write.storage.master.dtype`: `float32`
- master FITS storage dtype: `>f4`

## Numerical Results

Gate501 master versus Gate500 master:

- bitwise equal: `true`
- NaN mask equal: `true`
- finite pixels: `61651200`
- RMS absolute difference: `0.0`
- p99 absolute difference: `0.0`
- max absolute difference: `0.0`

Gate501 versus WBPP black-box full-frame/no-coverage compare:

- RMS: `0.012336290253351909`
- p99 absolute difference: `0.0007338253874331693`
- max absolute difference: `0.5401448363554664`
- shape match: `true`

Artifacts:

- `C:\glass_runs\phase2_s2_gate501_direct_fits_writer_ab_real\compare\gate501_vs_gate500_master_diff.json`
- `C:\glass_runs\phase2_s2_gate501_direct_fits_writer_ab_real\compare\gate501_default_direct_vs_wbpp.json`
- `C:\glass_runs\phase2_s2_gate501_direct_fits_writer_ab_real\compare\gate501_default_direct_vs_wbpp.html`

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_fits_io.py::test_write_fits_data_direct_simple_primary_roundtrips_float32 tests/test_fits_io.py::test_write_fits_data_can_preserve_integer_count_maps tests/test_fits_io.py::test_write_fits_data_falls_back_for_non_2d_primary tests/test_fits_io.py::test_write_resident_outputs_parallel_records_storage_and_timings`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache --out C:\glass_runs\phase2_s2_gate501_direct_fits_writer_ab_real\runs\default_v3_direct_fits`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate501_direct_fits_writer_ab_real\runs\default_v3_direct_fits\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate501_direct_fits_writer_ab_real\compare\gate501_default_direct_vs_wbpp.html --glass-time-seconds 7.147139 --reference-time-seconds 1092.541 --glass-label GLASS-direct-fits --reference-label WBPP-blackbox --glass-scale 0.000015259021896696421`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests: `4 passed in 0.22s`.
- Full test suite: `1146 passed in 41.77s`.

## CUDA Status

- CUDA available: yes.
- Real run used resident CUDA on the local RTX PRO 6000 Blackwell workstation.

## Known Limits

- The direct writer intentionally supports only simple 2D primary images with FITS-native signed integer or floating dtypes. Unsupported cases fall back to Astropy.
- This gate reduces final output serialization overhead. It does not address the larger resident registration/warp orchestration cost.
- The writer does not add compression; it preserves the existing uncompressed FITS output contract.

## Next Step

Return to resident registration/warp orchestration: reduce per-frame launch/control overhead and keep batch descriptors/catalogs on device where practical while preserving the 200-light bitwise output contract.

## Clean-Room Compliance

Compliant. The gate implements GLASS-owned FITS serialization using public FITS layout rules and validates against GLASS-generated outputs plus user-generated WBPP black-box references. It does not inspect or reuse PixInsight/WBPP/PJSR source code and does not modify input image directories.
