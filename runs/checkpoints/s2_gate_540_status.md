# S2-Gate 540 Status: Plan-Carried Simple FITS Spec Cache

## Gate

- Gate: S2-Gate 540
- Scope: resident CUDA I/O preparation for the real 200-light path.
- Status: green

## Completed

- Added `GLASS_SIMPLE_FITS_SPEC` to FITS `header_summary` during metadata scan
  for simple primary FITS images.
- The cached spec records only header-derived values required for the resident
  raw-u16 GPU decode path: BITPIX, dimensions, data offset, BSCALE, BZERO, and
  BLANK.
- Resident guarded-auto FITS mode now consumes this plan-carried spec before
  falling back to the old per-run file-header probe.
- Added artifact fields under `resident_fits_auto_selection.raw_u16_gpu`:
  `spec_source_counts`, `plan_header_spec_count`, and
  `file_header_probe_count`.
- Added metadata and resident CUDA tests for the cache contract.
- Regenerated a real 200-light manifest/plan and validated the resident default
  route with the new plan.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_fits_metadata.py tests/test_fits_io.py::test_native_u16_gpu_fits_eligibility_is_header_only tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto`
- `.venv\Scripts\glass.exe scan --root C:\gpwbpp_runs\final_m38_h_200\input --out C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json`
- `.venv\Scripts\glass.exe plan --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --out C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\resident_default_plan_spec --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\resident_default_plan_spec\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\resident_default_plan_spec\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 5.3842802 --reference-time-seconds 1092.541 --glass-label "GLASS Gate540 resident CUDA plan spec cache" --reference-label "WBPP black-box fastIntegration" --glass-scale=1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\resident_default_plan_spec\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused tests: `4 passed in 1.05s`.
- Full suite: `1178 passed in 42.86s`.

## Real 200-Light Evidence

- Scan root: `C:\gpwbpp_runs\final_m38_h_200\input`.
- Run root: `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314`.
- Manifest frame count: `260`.
- Manifest simple-FITS spec count: `260`.
- Plan frame count: `260`.
- Plan simple-FITS spec count: `260`.
- Resident run:
  `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\resident_default_plan_spec`.
- Shell elapsed: `5.3842802 s`.
- Internal elapsed: `5.024695099971723 s`.
- FITS mode effective: `native_u16_gpu`.
- Resident checked light frames: `200`.
- Plan-header specs used: `200`.
- File-header probes during resident selection: `0`.
- FITS spec cache hits during light read: `200`.

## Stage Timing

- Light read/upload/calibrate: `2.574674999981653 s`.
- Light read wait wall: `1.0357539994292893 s`.
- Light read worker cumulative: `28.578594000136945 s`.
- Master build/load: `0.35669700003927574 s`.
- Resident registration/warp: `0.2546218999195844 s`.
- Resident integration: `0.30699700000695884 s`.
- Output write: `0.23627379996469244 s`.

## Numerical Results

- Gate540 master, weight map, coverage map, low/high rejection maps, and DQ map
  are bitwise identical to Gate539.
- WBPP black-box compare:
  - RMS diff: `0.0004279821839256963`.
  - p99 abs diff: `0.0001313822576776147`.
  - coverage fraction: `0.9892770479074376`.
  - compared pixels: `56997300`.
  - WBPP elapsed: `1092.541 s`.
  - Gate540 shell speedup versus WBPP: `202.9131024793249x`.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: yes.

## Known Limits

- This optimization applies after regenerating scan/plan with
  `GLASS_SIMPLE_FITS_SPEC` present.
- Legacy plans remain compatible but still use the old file-header probe
  fallback.
- This gate removes repeated resident-run header probes; the larger bottleneck
  remains raw file read plus H2D/calibration overlap.

## Next Step

- Continue with a material read/upload/calibrate pipeline optimization, likely
  native batch file-read orchestration or reduced Python Future overhead, while
  preserving bitwise 200-light outputs.

## Clean-Room Compliance

- Compliant.
- This gate used FITS headers from user input data, GLASS timing artifacts,
  GLASS output hashes, and user-generated WBPP black-box output/timing.
- No external implementation source was read, copied, summarized, or reworked.
