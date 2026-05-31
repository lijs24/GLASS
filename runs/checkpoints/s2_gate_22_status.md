# S2-Gate 22 Status: Resident Geometric Warp Coverage

## Gate

S2-Gate 22: Resident geometric warp coverage.

## Completed Content

- Added native CUDA coverage accumulation kernels for resident warp footprints.
- Added `ResidentCalibratedStack` support for:
  - `reset_warp_coverage`
  - `accumulate_full_warp_coverage_frame`
  - `warp_coverage_map`
  - `warp_coverage_frame_count`
- Resident translation, bilinear matrix warp, and Lanczos3 matrix warp now add
  their per-frame coverage into the resident geometric footprint accumulator.
- Active frames that do not require a warp, including reference frames and
  registration-off frames, add full-frame coverage before integration.
- `integration_results.json` and `resident_artifacts.json` now record geometric
  warp coverage provenance and frame-count agreement.
- The resident DQ map now marks partial `WARP_EDGE` pixels when native
  geometric coverage is available, while keeping rejection losses separate.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\cmake.exe --build build/native-cuda --config Release`
  - Did not rebuild the Python native module because that build directory has
    `GLASS_BUILD_PYTHON_CUDA=OFF`.
- `cmd.exe /c 'call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "%CD%\\.venv\\Scripts\\cmake.exe" --build build\\native-cuda-glass --config Release'`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_accumulates_geometric_warp_coverage tests/test_resident_cuda_run.py::test_resident_dq_map_marks_geometric_warp_edges_without_no_data tests/test_resident_cuda_run.py::test_resident_dq_coverage_provenance_includes_geometric_warp_coverage`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_science_output_maps_skip_rejection_count_files tests/test_cuda_resident_stack.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_resident_cuda_run.py tests/test_cuda_resident_stack.py tests/test_cli_smoke.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_cuda_import.py tests/test_cuda_device_info.py tests/test_cuda_smoke.py tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\glass.exe run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate_15_200\\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps science --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\glass.exe compare --glass C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\integration\\resident_master_H.fits --reference "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\s2_gate_22_compare.html --glass-time-seconds 31.465294800000265 --reference-time-seconds 1092.541 --glass-label GLASS_S2_GATE_22_GEOMETRIC_WARP_COVERAGE --reference-label WBPP_BLACKBOX --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\s2_gate_22_compare.json --out C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\phase2_contract_acceptance_audit_s2_gate_22.json --markdown C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\phase2_contract_acceptance_audit_s2_gate_22.md --min-active-frames 190 --min-speedup 2.0 --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json`
- `.\\.venv\\Scripts\\glass.exe report --run C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531 --out C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\s2_gate_22_report.html`

## Test Results

- New focused tests: `3 passed in 0.33s`
- Resident CUDA stack/output-map focused tests: `20 passed in 0.32s`
- Ruff: `All checks passed`
- Resident/report/pipeline focused tests: `62 passed in 10.98s`
- Full pytest: `239 passed in 17.44s`
- CUDA targeted sanity tests: `43 passed in 1.81s`
- 200-light acceptance audit: passed
- Real HTML report generation: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Artifact

- Accepted run:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531`
- Compare report:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531\s2_gate_22_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531\s2_gate_22_compare.json`
- Acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_22.json`
- Acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_22.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531\s2_gate_22_report.html`

## Real-Data Geometric Coverage Summary

- Active frame count: `193`
- Geometric warp coverage frame count: `193`
- Geometric frame count matches active: `true`
- Warped frame count: `192`
- Full-frame coverage count: `1`
- Geometric coverage min/max/mean: `1.0` / `193.0` /
  `191.37103271484375`
- Geometric zero pixels: `0`
- Geometric partial pixels: `5396832`
- Geometric full pixels: `56254368`
- DQ `WARP_EDGE` pixels: `5396832`
- DQ `NO_DATA` pixels: `0`
- Partial edge inference:
  `available_from_geometric_warp_coverage`

## Real-Data Result Summary

- Total GLASS elapsed: `31.465294800000265 s`
- External reference elapsed: `1092.541 s`
- Speedup vs external reference: `34.72209642224584x`
- Phase 1 release `cuda11` baseline: `30.361440100008622 s`
- Runtime change vs Phase 1 release `cuda11`: about `+3.6%`
- Acceptance audit status: passed
- Shape match: `true`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`

## Performance Or Numerical Regression Note

The geometric coverage accumulator adds one resident frame-sized device buffer
and a small accumulation kernel after each resident warp. The accepted 200-light
run took `31.465 s`, slower than the fastest S2-Gate 21 run (`29.287 s`) and
about `3.6%` slower than the Phase 1 `cuda11` package baseline (`30.361 s`),
but still within the Phase 2 15 percent regression envelope and with identical
reference-level RMS/P99 agreement. The next optimization should fuse or defer
coverage accumulation if this overhead becomes material.

## Known Limitations

- The resident geometric coverage accumulator is per run, not per frame.
- If a warped frame is later zero-weighted by a downstream weighting or local
  normalization decision, artifacts report frame-count divergence but do not
  subtract that frame's already accumulated footprint.
- The geometric coverage map is currently summarized in JSON and used for DQ;
  it is not written as a separate FITS map.
- Calibration/cosmetic/LN DQ propagation into the resident stack remains future
  work.

## Next Step

Proceed to the next S2 gate by using the native geometric coverage signal to
improve resident DQ/report ergonomics or to reduce the new coverage
accumulation overhead before broader StackEngine default-path migration.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned CUDA kernels, GLASS artifacts, synthetic
tests, and user-generated benchmark/reference outputs only. No proprietary
source code was read, copied, summarized, or reworked.
