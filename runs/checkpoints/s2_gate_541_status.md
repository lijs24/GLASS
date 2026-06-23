# S2-Gate 541 Status: Explicit Native-U16 Plan Spec Cache

## Gate

- Gate: S2-Gate 541
- Scope: resident CUDA I/O preparation for explicit raw-u16 FITS mode.
- Status: green

## Completed

- Refactored resident raw-u16 FITS selection so guarded-auto and explicit
  `--resident-fits-read-mode native_u16_gpu` share the same plan-carried spec
  cache collection.
- Explicit native-u16 mode now records `checked`, `eligible`,
  `spec_cache_frame_count`, `spec_source_counts`, `plan_header_spec_count`, and
  `file_header_probe_count`.
- Explicit native-u16 mode now passes cached `SimpleFitsImageSpec` records into
  the resident prefetcher, avoiding repeated read-time header parsing for
  regenerated compatible plans.
- Non-native explicit modes and legacy fallback behavior remain unchanged.
- Added focused resident CUDA assertions for explicit native-u16 cache hits.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_records_native_u16_gpu_decode_backend tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto tests/test_fits_metadata.py tests/test_fits_io.py::test_native_u16_gpu_fits_eligibility_is_header_only`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate541_explicit_native_spec_cache\runs_20260623_140840\explicit_native_u16_plan_spec --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --resident-fits-read-mode native_u16_gpu`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate541_explicit_native_spec_cache\runs_20260623_140840\explicit_native_u16_plan_spec\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate541_explicit_native_spec_cache\runs_20260623_140840\explicit_native_u16_plan_spec\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 5.3129932 --reference-time-seconds 1092.541 --glass-label "GLASS Gate541 explicit native-u16 plan spec cache" --reference-label "WBPP black-box fastIntegration" --glass-scale=1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate541_explicit_native_spec_cache\runs_20260623_140840\explicit_native_u16_plan_spec\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests: `5 passed in 1.19s`.
- Full suite: `1178 passed in 42.90s`.

## Real 200-Light Evidence

- Plan:
  `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json`.
- Resident run:
  `C:\glass_runs\phase2_s2_gate541_explicit_native_spec_cache\runs_20260623_140840\explicit_native_u16_plan_spec`.
- Shell elapsed: `5.3129932 s`.
- Internal elapsed: `4.939994199958164 s`.
- Requested FITS mode: `native_u16_gpu`.
- Effective FITS mode: `native_u16_gpu`.
- Resident checked light frames: `200`.
- Plan-header specs used: `200`.
- File-header probes during resident selection: `0`.
- FITS spec cache hits during light read: `200`.

## Stage Timing

- Light read/upload/calibrate: `2.59187970001949 s`.
- Light read wait wall: `1.0550508994492702 s`.
- Light read worker cumulative: `28.803584099630825 s`.
- Master build/load: `0.36329040001146495 s`.
- Resident registration/warp: `0.26038510049693286 s`.
- Resident integration: `0.3075091000064276 s`.
- Output write: `0.24750769999809563 s`.

## Numerical Results

- Gate541 master, weight map, coverage map, low/high rejection maps, and DQ map
  are bitwise identical to Gate540.
- WBPP black-box compare:
  - RMS diff: `0.0004279821839256963`.
  - p99 abs diff: `0.0001313822576776147`.
  - coverage fraction: `0.9892770479074376`.
  - compared pixels: `56997300`.
  - WBPP elapsed: `1092.541 s`.
  - Gate541 shell speedup versus WBPP: `205.63568573737302x`.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: yes.

## Known Limits

- The benefit applies when explicit native-u16 runs use regenerated plans with
  `GLASS_SIMPLE_FITS_SPEC`.
- Explicit native-u16 still requires compatible FITS inputs and the native
  raw-u16 CUDA method.
- The larger remaining bottleneck is raw file read plus H2D/calibration overlap,
  not selection-time header parsing.

## Next Step

- Reduce Python Future/thread orchestration or move batch raw FITS reads deeper
  into native code while preserving bitwise 200-light outputs.

## Clean-Room Compliance

- Compliant.
- This gate used GLASS plan metadata, GLASS timing artifacts, GLASS output
  hashes, and user-generated WBPP black-box output/timing.
- No external implementation source was read, copied, summarized, or reworked.
