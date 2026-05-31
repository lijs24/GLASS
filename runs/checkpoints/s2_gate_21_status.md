# S2-Gate 21 Status: Resident DQ Coverage Provenance

## Gate

S2-Gate 21: Resident DQ coverage provenance.

## Completed Content

- Added resident DQ coverage provenance to `resident_artifacts.json` and
  `integration_results.json`.
- Separated post-rejection integration coverage from finite pre-rejection
  sample coverage using `coverage + low_rejection + high_rejection` when
  rejection maps are available.
- Recorded:
  - active frame count
  - post-rejection coverage stats
  - finite pre-rejection coverage stats
  - zero pre-rejection pixels
  - partial pre-rejection pixels
  - rejection-reduced pixels
  - rejected sample count
  - explicit `partial_edge_inference=deferred`
- Kept partial `WARP_EDGE` inference deferred because the derived finite
  pre-rejection coverage is not yet a pure geometric warp-footprint map.
- Added the provenance payload to the HTML DQ/mask summary table.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py tests\\test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_import.py tests\\test_cuda_device_info.py tests\\test_cuda_smoke.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py`
- First 200-light timing probe:
  `.\\.venv\\Scripts\\glass.exe run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate_15_200\\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps science --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- Optimized 200-light run:
  `.\\.venv\\Scripts\\glass.exe run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\\glass_runs\\phase2_s2_gate_15_200\\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps science --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\glass.exe compare --glass C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531\\integration\\resident_master_H.fits --reference "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531\\s2_gate_21_compare.html --glass-time-seconds 29.286973000038415 --reference-time-seconds 1092.541 --glass-label GLASS_S2_GATE_21_COVERAGE_PROVENANCE --reference-label WBPP_BLACKBOX --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531\\integration\\resident_coverage_map_H.fits --min-coverage 190`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json --glass-run C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531 --wbpp-result C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json --compare-json C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531\\s2_gate_21_compare.json --out C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531\\phase2_contract_acceptance_audit_s2_gate_21.json --markdown C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531\\phase2_contract_acceptance_audit_s2_gate_21.md --min-active-frames 190 --min-speedup 2.0 --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json`
- `.\\.venv\\Scripts\\glass.exe report --run C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531 --out C:\\glass_runs\\phase2_s2_gate_21_200\\resident_coverage_provenance_fast_20260531\\s2_gate_21_report.html`

## Test Results

- Focused resident/report/pipeline tests: `41 passed in 10.43s`
- Ruff: `All checks passed`
- Full pytest: `236 passed in 15.80s`
- CUDA targeted sanity tests: `40 passed in 2.05s`
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

- First timing probe:
  `C:\glass_runs\phase2_s2_gate_21_200\resident_coverage_provenance_20260531`
- Accepted optimized run:
  `C:\glass_runs\phase2_s2_gate_21_200\resident_coverage_provenance_fast_20260531`
- Compare report:
  `C:\glass_runs\phase2_s2_gate_21_200\resident_coverage_provenance_fast_20260531\s2_gate_21_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_21_200\resident_coverage_provenance_fast_20260531\s2_gate_21_compare.json`
- Acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_21_200\resident_coverage_provenance_fast_20260531\phase2_contract_acceptance_audit_s2_gate_21.json`
- Acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_21_200\resident_coverage_provenance_fast_20260531\phase2_contract_acceptance_audit_s2_gate_21.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_21_200\resident_coverage_provenance_fast_20260531\s2_gate_21_report.html`

The generated HTML report contains `coverage_provenance`,
`finite_pre_rejection_coverage`, and `partial_pre_rejection_pixels`.

## Real-Data Coverage Provenance Summary

- Active frame count: `193`
- Finite pre-rejection coverage:
  - min: `1.0`
  - max: `193.0`
  - mean: `191.37103271484375`
- Post-rejection coverage:
  - min: `1.0`
  - max: `193.0`
  - mean: `190.35751342773438`
- Zero pre-rejection pixels: `0`
- Partial pre-rejection pixels: `5396832`
- Post-rejection zero pixels: `0`
- Rejection-reduced pixels: `39095145`
- Rejected sample count: `62484984.0`
- Partial edge inference: `deferred`

## Real-Data Result Summary

- Total GLASS elapsed after optimized provenance stats: `29.286973000038415 s`
- First unoptimized provenance timing probe: `31.36915859999135 s`
- External reference elapsed: `1092.541 s`
- Speedup vs external reference: `37.30467467561659x`
- Phase 1 release `cuda11` baseline: `30.361440100008622 s`
- Acceptance audit status: passed
- Shape match: `true`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`

## Performance Or Numerical Regression Note

The first implementation used full-image percentile/median statistics over the
coverage arrays and increased runtime to `31.369 s`. That was corrected before
the gate was accepted: provenance stats now use count/min/max/mean and key
boolean counts. The accepted run completed in `29.287 s`, which remains faster
than the Phase 1 release `cuda11` baseline and passes the benchmark contract.

The non-blocking performance diagnostics still report three warning-level
regressions:

- `output_write`: retained science-mode weight, coverage, and DQ map writes.
- `gc`: small wall-clock variation.
- `light_h2d_calibrate_store`: small transfer/calibration variation in this
  run, with high worker cumulative I/O indicating storage/cache variability.

The master-light computation is unchanged. Image agreement is identical to the
previous accepted resident runs within recorded precision.

## Known Limitations

- `finite_pre_rejection_coverage` is a finite sample count before rejection,
  not a pure geometric warp coverage map.
- Partial `WARP_EDGE` marking remains deferred until resident CUDA stores or
  emits geometric pre-rejection warp coverage independently of rejection.
- Calibration/cosmetic and LN-exclusion flags are not yet propagated through
  the resident CUDA stack.

## Next Step

Add a pure resident geometric warp coverage signal, either as an accumulated
per-pixel map or as a lightweight resident-side summary, so partial warp-edge
DQ can be marked without confusing rejection with resampling footprint loss.

## Clean-Room Constraint

Compliant. The provenance is derived from GLASS-owned resident integration maps
and the project-defined DQ contract. No proprietary implementation source was
read, copied, summarized, or reworked.
