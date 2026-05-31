# S2-Gate 18 Status: Resident Output Map Policy

## Gate

S2-Gate 18: Resident output map policy.

## Completed Content

- Added `--resident-output-maps` to `glass run` and `glass audit`.
- Added three resident output policies:
  - `audit`: write all available resident diagnostic maps.
  - `science`: write master, weight, coverage, and DQ maps while skipping
    low/high rejection count FITS files.
  - `minimal`: write only the master FITS.
- Recorded available, written, and skipped maps in both
  `resident_artifacts.json` and `integration_results.json`.
- Kept `audit` as the default to preserve the full diagnostic/audit path.
- Added unit and CUDA fixture coverage for policy selection and science-mode
  output behavior.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_cuda_resident_stack.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_import.py tests\\test_cuda_device_info.py tests\\test_cuda_smoke.py tests\\test_gpu_calibration_vs_cpu.py tests\\test_gpu_master_frames_vs_cpu.py tests\\test_gpu_warp_vs_cpu.py tests\\test_gpu_integration_vs_cpu.py tests\\test_gpu_local_norm_vs_cpu.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\glass.exe run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate_15_200\\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps science --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\glass.exe compare --glass C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531\\integration\\resident_master_H.fits --reference "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531\\s2_gate_18_compare.html --glass-time-seconds 25.189113800181076 --reference-time-seconds 1092.541 --glass-label GLASS_S2_GATE_18_SCIENCE --reference-label WBPP_BLACKBOX --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531\\s2_gate_18_compare.json --out C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531\\phase2_contract_acceptance_audit_s2_gate_18.json --markdown C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531\\phase2_contract_acceptance_audit_s2_gate_18.md --min-active-frames 190 --min-speedup 2.0 --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json`

## Test Results

- Focused resident/CLI tests: `41 passed in 2.31s`
- Ruff: `All checks passed`
- Full pytest: `235 passed in 14.63s`
- CUDA targeted tests: `58 passed in 2.08s`
- 200-light acceptance audit: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Artifact

- Run directory:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531`
- Master:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\integration\resident_master_H.fits`
- Weight map:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\integration\resident_weight_map_H.fits`
- Coverage map:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\integration\resident_coverage_map_H.fits`
- DQ map:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\integration\resident_dq_map_H.fits`
- Compare report:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\s2_gate_18_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\s2_gate_18_compare.json`
- Acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\phase2_contract_acceptance_audit_s2_gate_18.json`
- Acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\phase2_contract_acceptance_audit_s2_gate_18.md`

## Real-Data Result Summary

- Total GLASS elapsed: `25.189113800181076 s`
- External reference elapsed: `1092.541 s`
- Speedup vs external reference: `43.37353861143563x`
- Phase 1 release baseline envelope: passed; release `cuda11` baseline was
  `30.361440100008622 s`
- S2-Gate 17 elapsed: `27.981953100068495 s`
- Acceptance audit status: passed
- Shape match: `true`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`
- Active frame floor: `193 >= 190`

Science-mode output policy:

- Available maps: `master`, `weight`, `dq`, `coverage`, `low_rejection`,
  `high_rejection`
- Written maps: `master`, `weight`, `dq`, `coverage`
- Skipped maps: `low_rejection`, `high_rejection`
- No low/high rejection FITS count files were written in the integration
  directory.

Resident DQ summary:

- `valid`: `22556055`
- `low_rejected`: `13074085`
- `high_rejected`: `32318219`
- DQ map dtype: `int16`
- Estimated DQ map data bytes: `123302400`

## Performance Note

The hard benchmark contract passed. Total runtime is faster than the Phase 1
release baseline and faster than S2-Gate 17 because `science` mode skips the
low/high rejection count FITS outputs.

The non-blocking performance diagnostics still report `output_write` as
regressed against the older release baseline. This is expected because
science-mode output still intentionally writes weight, coverage, and DQ maps for
validated comparison and audit. Use `minimal` only for exploratory speed runs
that do not need coverage-masked compare artifacts.

## Known Limitations

- `minimal` mode omits coverage, weight, DQ, and rejection maps, so it is not
  suitable for acceptance-audit comparisons that require coverage masks.
- Resident DQ currently covers integration no-data and rejection states.
- Calibration/cosmetic/warp-edge/LN-exclusion flags are not yet propagated
  through the resident CUDA stack.
- Output policy affects diagnostic artifact selection only; it does not change
  master-light computation.

## Next Step

Continue Phase 2 toward deeper resident DQ propagation and unified StackEngine
parity: propagate calibration, warp-edge, and local-normalization DQ semantics
through the resident fast path, then align master-frame and light-integration
stacking behavior through the shared StackEngine contract.

## Clean-Room Constraint

Compliant. The output-map policy is a GLASS-owned scheduling and artifact
contract over GLASS-generated maps. No proprietary implementation source was
read, copied, summarized, or reworked.
