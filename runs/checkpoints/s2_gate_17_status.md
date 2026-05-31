# S2-Gate 17 Status: Resident CUDA DQ Map Parity

## Gate

S2-Gate 17: Resident CUDA DQ map parity.

## Completed Content

- Added a resident CUDA integration DQ map generated from resident master,
  weight, coverage, low-rejection, and high-rejection outputs.
- Encoded these integration flags:
  - `NO_DATA`
  - `LOW_REJECTED`
  - `HIGH_REJECTED`
- Wrote `resident_dq_map_<filter>.fits` as an `int16` FITS diagnostic map.
- Added `dq_map_path`, `dq_summary`, and `dq_flag_bits` to
  `resident_artifacts.json`.
- Mirrored `dq_map_path` and `dq_summary` into `integration_results.json`.
- Added a direct DQ helper test and resident CUDA smoke assertions.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_cuda_resident_stack.py tests\\test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_import.py tests\\test_cuda_device_info.py tests\\test_cuda_smoke.py tests\\test_gpu_calibration_vs_cpu.py tests\\test_gpu_master_frames_vs_cpu.py tests\\test_gpu_warp_vs_cpu.py tests\\test_gpu_integration_vs_cpu.py tests\\test_gpu_local_norm_vs_cpu.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\glass.exe run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate_15_200\\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\glass.exe compare --glass C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531\\integration\\resident_master_H.fits --reference "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531\\s2_gate_17_compare.html --glass-time-seconds 27.981953100068495 --reference-time-seconds 1092.541 --glass-label GLASS_S2_GATE_17 --reference-label WBPP_BLACKBOX --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531\\s2_gate_17_compare.json --out C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531\\phase2_contract_acceptance_audit_s2_gate_17.json --markdown C:\\glass_runs\\phase2_s2_gate_17_200\\resident_dq_hit_20260531\\phase2_contract_acceptance_audit_s2_gate_17.md --min-active-frames 190 --min-speedup 2.0 --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json`

## Test Results

- First focused run exposed one test assertion bug caused by a hard-coded
  fixture shape; the code path itself completed.
- Focused tests after fix: `51 passed in 9.78s`
- Ruff: `All checks passed`
- Full pytest: `233 passed in 13.89s`
- CUDA targeted tests: `56 passed in 1.50s`
- 200-light acceptance audit: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: available

## Real-Data Artifact

- Run directory:
  `C:\glass_runs\phase2_s2_gate_17_200\resident_dq_hit_20260531`
- Resident DQ map:
  `C:\glass_runs\phase2_s2_gate_17_200\resident_dq_hit_20260531\integration\resident_dq_map_H.fits`
- Compare report:
  `C:\glass_runs\phase2_s2_gate_17_200\resident_dq_hit_20260531\s2_gate_17_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_17_200\resident_dq_hit_20260531\s2_gate_17_compare.json`
- Acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_17_200\resident_dq_hit_20260531\phase2_contract_acceptance_audit_s2_gate_17.json`
- Acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_17_200\resident_dq_hit_20260531\phase2_contract_acceptance_audit_s2_gate_17.md`

## Real-Data Result Summary

- Total GLASS elapsed: `27.981953100068495 s`
- External reference elapsed: `1092.541 s`
- Speedup vs external reference: `39.04448685525549x`
- Acceptance audit status: passed
- Shape match: `true`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`

Resident DQ summary:

- `valid`: `22556055`
- `low_rejected`: `13074085`
- `high_rejected`: `32318219`
- DQ map dtype: `int16`
- Estimated DQ map data bytes: `123302400`

## Performance Note

The hard benchmark contract passed. Non-blocking performance diagnostics still
reported regressions:

- `output_write`: expected after adding one more 123 MB DQ FITS output.
- `resident_integration` and `gc`: small wall-clock variation in this run; the
  total runtime remains inside the contract envelope and below the Phase 1
  release baseline runtime.

## Known Limitations

- Resident DQ currently covers integration no-data and rejection flags.
- Calibration/cosmetic/warp-edge/LN-exclusion flags are not yet propagated
  through the resident CUDA stack.
- Writing the extra DQ map increases output I/O. Future gates should add a map
  output policy or faster output writer if the user wants maximum benchmark
  speed with fewer diagnostics.

## Next Step

Continue resident CUDA DQ parity by propagating calibration, warp-edge, and
local-normalization DQ semantics through the resident fast path, or add a
diagnostic-map output policy to choose between full audit mode and maximum
speed mode.

## Clean-Room Constraint

Compliant. The DQ bitfield is derived from GLASS-owned integration maps and the
project-defined `DQFlag` contract. No proprietary implementation source was
read, copied, summarized, or reworked.
