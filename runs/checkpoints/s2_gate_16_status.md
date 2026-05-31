# S2-Gate 16 Status: Resident I/O Overlap Timing Semantics

## Gate

S2-Gate 16: Resident I/O overlap timing semantics.

## Completed Content

- Added explicit resident I/O overlap diagnostics to `resident_artifacts.json`.
- Separated light-read consumer wait wall time from cumulative worker-thread
  FITS open/materialize/decode time.
- Added compatible timing aliases:
  - `light_read_wait_wall`
  - `light_read_worker_cumulative`
  - `light_fits_open_worker_cumulative`
  - `light_fits_materialize_decode_worker_cumulative`
  - `light_read_overlap_saved`
- Added `resident_io_overlap` with wall-clock stage time, consumer wait,
  worker cumulative time, overlap estimate, prefetch settings, and diagnostic
  ratios.
- Updated benchmark contract diagnostics so cumulative worker timings are
  informational and excluded from `regressed_count`.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_acceptance_audit.py tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_import.py tests\\test_cuda_device_info.py tests\\test_cuda_smoke.py tests\\test_gpu_calibration_vs_cpu.py tests\\test_gpu_master_frames_vs_cpu.py tests\\test_gpu_warp_vs_cpu.py tests\\test_gpu_integration_vs_cpu.py tests\\test_gpu_local_norm_vs_cpu.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\glass.exe run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate_15_200\\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\glass.exe compare --glass C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531\\integration\\resident_master_H.fits --reference "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531\\s2_gate_16_compare.html --glass-time-seconds 23.963165799854323 --reference-time-seconds 1092.541 --glass-label GLASS_S2_GATE_16 --reference-label WBPP_BLACKBOX --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531\\s2_gate_16_compare.json --out C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531\\phase2_contract_acceptance_audit_s2_gate_16.json --markdown C:\\glass_runs\\phase2_s2_gate_16_200\\io_overlap_hit_20260531\\phase2_contract_acceptance_audit_s2_gate_16.md --min-active-frames 190 --min-speedup 2.0 --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json`

## Test Results

- Focused tests: `24 passed in 2.27s`
- Ruff: `All checks passed`
- Full pytest: `232 passed in 14.45s`
- CUDA targeted tests: `55 passed in 1.84s`
- 200-light acceptance audit: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: available

## Real-Data Artifact

- Run directory:
  `C:\glass_runs\phase2_s2_gate_16_200\io_overlap_hit_20260531`
- Compare report:
  `C:\glass_runs\phase2_s2_gate_16_200\io_overlap_hit_20260531\s2_gate_16_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_16_200\io_overlap_hit_20260531\s2_gate_16_compare.json`
- Acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_16_200\io_overlap_hit_20260531\phase2_contract_acceptance_audit_s2_gate_16.json`
- Acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_16_200\io_overlap_hit_20260531\phase2_contract_acceptance_audit_s2_gate_16.md`

## Real-Data Result Summary

- Total GLASS elapsed: `23.963165799854323 s`
- External reference elapsed: `1092.541 s`
- Speedup vs external reference: `45.59251515952211x`
- Acceptance audit status: passed
- Performance diagnostics status: `regressed`, non-blocking
- Wall-clock regressed item: `output_write`
- Cumulative worker informational items:
  - `light_fits_open`
  - `light_fits_materialize_decode`
  - `light_read_decode_worker`

Resident I/O overlap summary from `resident_artifacts.json`:

- Stage wall-clock: `6.601806100225076 s`
- Consumer read wait wall time: `2.335968501633033 s`
- Worker read cumulative time: `48.549365900224075 s`
- Estimated overlap saved: `46.21339739859104 s`
- Overlap efficiency: `0.951884675354282`
- Worker cumulative to wall ratio: `7.353952109948954`

## Known Limitations

- The overlap-saved value is a diagnostic accounting estimate, not a hardware
  profiler trace.
- `output_write` remains above the release timing warning factor and is still
  the next wall-clock optimization target.
- Legacy timing keys `light_fits_materialize_decode` and
  `light_read_decode_worker` still store worker cumulative time for backward
  compatibility; new consumers should prefer the explicit `*_worker_cumulative`
  names.

## Next Step

Proceed to the next Phase 2 gate by either reducing the remaining output-write
wall-clock bottleneck or returning to the main StackEngine/DQ migration path,
while preserving the 200-light benchmark contract.

## Clean-Room Constraint

Compliant. This gate uses GLASS-owned timing artifacts, user-generated benchmark
outputs, and project-defined prefetch scheduling semantics only. It does not
read, copy, summarize, or rework proprietary implementation source.
