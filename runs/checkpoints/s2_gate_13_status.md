# S2-Gate 13 Status: Resident Output Map Storage Recovery

## Gate

S2-Gate 13: Resident Output Map Storage Recovery

## Completed

- Added optional dtype preservation to `write_fits_data`.
- Changed resident CUDA count-map outputs to store coverage, low-rejection, and
  high-rejection maps as integer FITS images when the frame count fits `int16`.
- Kept resident master and weight maps as `float32`.
- Added per-output write timing and estimated data-byte diagnostics to
  `resident_artifacts.json`.
- Added automatic `run_command.txt` recording for `glass run` and `glass audit`
  so benchmark contract audits can prove required command tokens were used.
- Updated Phase 2 gate documentation and the algorithm source log.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py tests\test_cli_smoke.py tests\test_acceptance_audit.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\io\fits_io.py src\glass\engine\resident_cuda.py tests\test_fits_io.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\compare_vs_reference_scaled_coverage190.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\compare_vs_reference_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\phase2_contract_acceptance_audit_s2_gate_13.json --markdown C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\phase2_contract_acceptance_audit_s2_gate_13.md --min-active-frames 190 --min-speedup 20 --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_calibration_vs_cpu.py tests\test_gpu_master_frames_vs_cpu.py tests\test_gpu_warp_vs_cpu.py tests\test_gpu_integration_vs_cpu.py tests\test_cuda_resident_stack.py`

## Test Results

- Focused tests: `30 passed`.
- Ruff focused check: `All checks passed`.
- Full pytest suite: `230 passed`.
- CUDA targeted tests: `35 passed`.
- Real 200-light contract audit: passed.

## Real Benchmark Results

Artifacts:

- Run: `C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531`
- Compare JSON: `C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\compare_vs_reference_scaled_coverage190.json`
- Acceptance audit JSON: `C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\phase2_contract_acceptance_audit_s2_gate_13.json`
- Acceptance audit Markdown: `C:\glass_runs\phase2_s2_gate_13_200\int_count_maps_20260531\phase2_contract_acceptance_audit_s2_gate_13.md`

Accepted hot-cache runtime:

- GLASS elapsed: `23.214623299892992 s`.
- Speedup vs external reference: `47.06262022373785x`.
- RMS diff: `0.001558294284488301`.
- P99 absolute diff: `0.00043095467146486016`.
- Coverage fraction: `0.9574613308418977`.

Output map storage:

- `resident_master_H.fits`: `float32`, `246608640` bytes on disk.
- `resident_weight_map_H.fits`: `float32`, `246608640` bytes on disk.
- `resident_coverage_map_H.fits`: `int16`, `123307200` bytes on disk.
- `resident_low_rejection_map_H.fits`: `int16`, `123307200` bytes on disk.
- `resident_high_rejection_map_H.fits`: `int16`, `123307200` bytes on disk.

Timing notes:

- Current accepted `output_write`: `2.479025000007823 s`.
- S2-Gate 10 `output_write`: `3.3451026000548154 s`.
- The same output-write section is about 25.9 percent faster.
- A first post-change run before master-cache reuse was observed at
  `36.1471121001523 s`, with `output_write` around `2.533235500101 s`.
- The accepted hot-cache run reuses master-frame cache, so total runtime is not
  directly comparable to a cold master-build run.

## CUDA

- CUDA extension built: yes.
- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limits

- Count-map storage is optimized for output size, not yet parallelized.
- `output_write` remains the only stage-level diagnostic above the 1.15 warning
  factor in the hot-cache audit.
- Weight maps remain `float32` because weighted integrations are not guaranteed
  to be integer counts.

## Next Step

S2-Gate 14 should focus on the remaining `output_write` overhead, likely by
parallelizing independent FITS writes or adding an explicit map-output policy,
then run a clean cold-cache benchmark to separate master-cache reuse from
resident integration speed.

## Clean-Room

Compliant. This gate changes GLASS-owned FITS output storage and uses only GLASS
artifacts plus user-generated benchmark/reference outputs for validation.
