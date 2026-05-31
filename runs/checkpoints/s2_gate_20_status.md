# S2-Gate 20 Status: Resident Warp-Edge DQ Semantics

## Gate

S2-Gate 20: Resident warp-edge DQ semantics.

## Completed Content

- Extended the resident CUDA integration DQ map to set `WARP_EDGE` when the
  resident coverage map proves a pixel has no valid contributing warp
  footprint.
- Preserved existing `NO_DATA`, `LOW_REJECTED`, and `HIGH_REJECTED` behavior.
- Added `WARP_EDGE` to the resident DQ FITS `DQFLAGS` header.
- Added the `warp_edge` bit value to resident artifact `dq_flag_bits`.
- Kept the first resident implementation conservative: it only marks
  zero-coverage pixels as warp-edge/no-data and does not infer partial edge
  pixels from reduced coverage because rejection can also reduce coverage.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_phase2_contracts.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_import.py tests\\test_cuda_device_info.py tests\\test_cuda_smoke.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\glass.exe run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate_15_200\\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps science --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\glass.exe compare --glass C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531\\integration\\resident_master_H.fits --reference "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531\\s2_gate_20_compare.html --glass-time-seconds 25.380221899831668 --reference-time-seconds 1092.541 --glass-label GLASS_S2_GATE_20_WARP_EDGE_DQ --reference-label WBPP_BLACKBOX --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531\\s2_gate_20_compare.json --out C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531\\phase2_contract_acceptance_audit_s2_gate_20.json --markdown C:\\glass_runs\\phase2_s2_gate_20_200\\resident_warp_edge_dq_20260531\\phase2_contract_acceptance_audit_s2_gate_20.md --min-active-frames 190 --min-speedup 2.0 --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json`

## Test Results

- Focused DQ/resident tests: `29 passed in 1.29s`
- Ruff: `All checks passed`
- Full pytest: `235 passed in 11.37s`
- CUDA targeted sanity tests: `39 passed in 1.27s`
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
  `C:\glass_runs\phase2_s2_gate_20_200\resident_warp_edge_dq_20260531`
- DQ map:
  `C:\glass_runs\phase2_s2_gate_20_200\resident_warp_edge_dq_20260531\integration\resident_dq_map_H.fits`
- Compare report:
  `C:\glass_runs\phase2_s2_gate_20_200\resident_warp_edge_dq_20260531\s2_gate_20_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_20_200\resident_warp_edge_dq_20260531\s2_gate_20_compare.json`
- Acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_20_200\resident_warp_edge_dq_20260531\phase2_contract_acceptance_audit_s2_gate_20.json`
- Acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_20_200\resident_warp_edge_dq_20260531\phase2_contract_acceptance_audit_s2_gate_20.md`

Real DQ metadata:

- FITS `DQFLAGS`: `NO_DATA,WARP_EDGE,LOW_REJECTED,HIGH_REJECTED`
- `dq_flag_bits`: `no_data=1`, `warp_edge=64`, `low_rejected=256`,
  `high_rejected=512`
- DQ summary on the 200-light run:
  `valid=22556055`, `low_rejected=13074085`, `high_rejected=32318219`
- The selected real benchmark had no zero-coverage pixels, so it did not
  produce a nonzero `warp_edge` count. The focused synthetic helper test
  validates the zero-coverage marking path directly.

## Real-Data Result Summary

- Total GLASS elapsed: `25.380221899831668 s`
- External reference elapsed: `1092.541 s`
- Speedup vs external reference: `43.04694436131964x`
- Acceptance audit status: passed
- Shape match: `true`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`

## Performance Or Numerical Regression Note

The master-light computation is unchanged; this gate changes the DQ map bits and
metadata only. The 200-light benchmark remains inside the hard runtime and image
agreement contract.

The non-blocking performance diagnostics still report `output_write` as
regressed against the older release baseline (`2.0766 s` vs `0.9691 s`,
`2.14x`). This is the same diagnostic family introduced by the retained
science-mode weight, coverage, and DQ map writes, not a master computation
regression.

## Known Limitations

- Resident DQ marks only zero-coverage warp footprint as `WARP_EDGE`.
- Partial edge inference is intentionally deferred because reduced coverage can
  also be caused by rejection, not only by resampling footprint loss.
- Calibration/cosmetic and LN-exclusion flags are not yet propagated through
  the resident CUDA stack.

## Next Step

Continue Phase 2 DQ parity by separating pre-rejection warp coverage from
post-rejection integration coverage, then use that cleaner signal to mark
partial warp-edge pixels without confusing rejection with geometric footprint
loss.

## Clean-Room Constraint

Compliant. The `WARP_EDGE` behavior is derived from GLASS-owned coverage maps
and the project-defined `DQFlag` contract. No proprietary implementation source
was read, copied, summarized, or reworked.
