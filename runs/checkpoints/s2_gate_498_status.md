# S2-Gate 498 Status: Resident Minimal Warp Coverage Accumulator Skip

## Gate

S2-Gate 498

## Summary

Implemented a resident CUDA speed-path optimization for
`--resident-output-maps minimal`: batch matrix warp now accepts
`track_coverage=false`, so the speed path skips updates to the resident
geometric warp coverage accumulator that is not downloaded or reported in
minimal mode.

The per-frame batch coverage scratch remains allocated and written for warp
kernel/scatter correctness. Audit/science modes and legacy calls keep the
default `track_coverage=true`.

## Completed Work

- Added native `track_coverage` controls to:
  - `ResidentCalibratedStack.apply_matrix_bilinear_frames`
  - `ResidentCalibratedStack.apply_matrix_bilinear_frames_loop`
  - `ResidentCalibratedStack.apply_matrix_lanczos3_frames`
  - `ResidentCalibratedStack.apply_matrix_lanczos3_frames_loop`
- Added Python wrapper `track_coverage` parameters in `src/glass_cuda.py`.
- Routed resident minimal mode through `track_coverage=false`.
- Recorded:
  - `triangle_warp_batch_track_coverage`
  - `triangle_warp_batch_coverage_accumulator_policy`
  - native `postprocess_mode=scatter_only_no_coverage_accumulator`
- Added focused test coverage for `track_coverage=false` propagation.
- Documented Gate498 in:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`
- Reclaimed generated C: run space:
  - deleted 177 generated `C:\glass_runs\phase2_s2_gate*` directories with
    Gate number `<480`;
  - reclaimed `153.468 GiB`;
  - preserved current 200-light plans, WBPP black-box outputs, Gate480+ runs,
    and the Gate486 shared master cache.

## Commands Run

```powershell
# cleanup inspection and deletion
Get-PSDrive -Name C
# deleted only generated C:\glass_runs\phase2_s2_gate* directories with Gate < 480

# native build
cmd /c "VsDevCmd.bat -arch=x64 && cmake --build build --config Release --target _glass_cuda_native"

# focused tests
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_keeps_translation_matrices_batched tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_honors_chunk_capacity tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_can_skip_warp_coverage_tracking
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_import.py tests/test_cuda_device_info.py tests/test_cuda_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py

# real 200-light run
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\runs\stack_minimal_skip_warpcoverage --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache

# compare report
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\runs\stack_minimal_skip_warpcoverage\integration\resident_master_H.fits --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\compare\gate498_vs_wbpp_scaled_no_coverage.json --glass-time-seconds 7.653901700046845 --reference-time-seconds 1092.541 --glass-label "GLASS Gate498 resident CUDA minimal" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 1.5259021896696422e-05 --clip-low 0 --clip-high 1

# full suite
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident matrix-batch tests: `3 passed`.
- CUDA import/device/smoke tests: `3 passed`.
- Resident CUDA run tests: `77 passed`.
- Full pytest: `1143 passed in 42.00s`.

## CUDA Status

- CUDA available: yes.
- GPU:
  - name: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
  - compute capability: `12.0`
  - total memory: `97886 MiB`
  - multiprocessors: `188`
  - driver: `596.21`

## Real 200-Light A/B

- Run root:
  `C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\runs\stack_minimal_skip_warpcoverage`
- Total elapsed:
  `7.653901700046845 s`
- WBPP black-box elapsed:
  `1092.541 s`
- Speedup versus WBPP:
  `142.74301432344149x`
- Active frames:
  `193 / 200`
- Output policy:
  - `download_mode=master_only`
  - `weight_map_downloaded=false`
  - `diagnostic_maps_downloaded=false`
  - public integration output: final master only
- Warp path:
  - `triangle_warp_batch_track_coverage=false`
  - `triangle_warp_batch_coverage_accumulator_policy=skipped_by_minimal_output_policy`
  - `triangle_warp_batch_native_postprocess_mode=scatter_only_no_coverage_accumulator`
  - Gate497 native triangle warp sync/total: `0.4771082 / 0.4972761 s`
  - Gate498 native triangle warp sync/total: `0.465614 / 0.4856435 s`

## Numerical Validation

- Gate498 master vs Gate497 master:
  - finite pixels: `61,651,200`
  - shape: `(6422, 9600)`
  - RMS: `0.0`
  - p99 abs: `0.0`
  - max abs: `0.0`
  - bitwise equal including NaN mask: yes
- Gate498 no-coverage-mask compare vs WBPP:
  - report: `C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\compare\gate498_vs_wbpp_scaled_no_coverage.json`
  - RMS: `0.012331019662283473`
  - p99 abs: `0.0007338226120918931`
  - shape match: yes
- Because Gate498 and Gate497 masters are bitwise identical, the established
  WBPP scaled coverage-190 comparison remains unchanged:
  - RMS: `0.0017794216505176163`
  - p99 abs: `0.00042621337808668863`
  - coverage fraction: `0.960532609259836`

## Artifacts

- Real run:
  `C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\runs\stack_minimal_skip_warpcoverage`
- Master:
  `C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\runs\stack_minimal_skip_warpcoverage\integration\resident_master_H.fits`
- Compare:
  `C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\compare\gate498_vs_wbpp_scaled_no_coverage.json`
- Compare HTML:
  `C:\glass_runs\phase2_s2_gate498_skip_warpcoverage_ab_real\compare\gate498_vs_wbpp_scaled_no_coverage.html`

## Known Limitations

- Minimal mode intentionally does not write coverage, rejection, weight, or DQ
  diagnostic maps. Use audit/science output modes for evidence-rich artifacts.
- This gate skips the global geometric warp coverage accumulator only in
  minimal mode; the batch warp kernel still writes per-frame coverage scratch.
  A future gate can remove that scratch write if a null-coverage warp kernel is
  added and proven bitwise equivalent.
- End-to-end runtime is neutral within I/O variance (`7.60 s` Gate497 versus
  `7.65 s` Gate498), although native warp sync/total timing improved slightly.

## Next Step

Continue Phase 2 substantive work on the two dominant cost centers:

1. I/O + upload + calibration pipeline overlap.
2. Resident registration/catalog/warp orchestration and host/device round-trip
   reduction.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or
  reworked.
- PixInsight/WBPP was used only through existing user-generated black-box
  outputs and timing artifacts.
- Input image directories were treated as read-only.
- The optimization is GLASS-owned CUDA scheduling/output-policy code and does
  not use proprietary implementation details.
