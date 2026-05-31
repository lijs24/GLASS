# S2-Gate 31 Status: Real-Data Audit-Map Rejection Verification

## Gate

S2-Gate 31 adds real-data evidence for low/high rejection count maps by running
the 200-light resident CUDA benchmark with `--resident-output-maps audit`.

## Completed Content

- Added strict audit-map benchmark contract:
  `benchmarks/phase2_m38_h_200_audit_maps_contract.json`.
- The strict contract requires `--resident-output-maps audit`.
- The strict contract forbids policy-skipped rejection maps and verifies:
  - DQ FITS map pixel counts.
  - Coverage map finite and zero/no-data invariants.
  - Low rejection map positive pixels against DQ `LOW_REJECTED`.
  - High rejection map positive pixels against DQ `HIGH_REJECTED`.
  - Low+high rejection map rounded sample sum against
    `dq_coverage_provenance.rejected_sample_count`.
- Added an explicit `rejection_map_sum_tolerance_samples` contract field.
- Added a unit test covering the explicit rejected-sample tolerance path.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Real-Data Run

Command:

```powershell
.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
```

Result:

- Run directory:
  `C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531`
- Runtime: `27.24825630011037 s`
- Output maps written:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_dq_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`

## Comparison

Compare command used the Phase 1 scale/offset and coverage threshold:

```powershell
.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531\integration\resident_master_H.fits --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531\s2_gate_31_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 27.24825630011037 --reference-time-seconds 1092.541 --glass-label GLASS-S2G31-audit-maps --reference-label WBPP-blackbox
```

Results:

- Speedup vs reference: `40.09581339689522x`
- RMS diff: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`
- Shape match: `true`

## Acceptance Audit

Command:

```powershell
.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531\s2_gate_31_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531\phase2_contract_acceptance_audit_s2_gate_31.json --markdown C:\glass_runs\phase2_s2_gate_31_200\resident_audit_maps_20260531\phase2_contract_acceptance_audit_s2_gate_31.md --min-active-frames 190 --min-speedup 2.0
```

Result: `passed`.

Key rejection-map checks:

- Low rejection positive pixels: `13074085`, matching DQ low-rejected pixels
  with delta `0`.
- High rejection positive pixels: `32318219`, matching DQ high-rejected pixels
  with delta `0`.
- Low rejection rounded sample sum: `18860098`.
- High rejection rounded sample sum: `43624888`.
- Combined rejection sample sum: `62484986`.
- Provenance `rejected_sample_count`: `62484984`.
- Sample-sum delta: `2`, accepted by explicit tolerance `4`.

## Commands Run

- real-data resident audit-map run
- compare against the external reference master
- strict audit-map acceptance audit
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py tests\test_dq_map_verify.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\benchmark_contract.py tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe

## Test Results

- Targeted tests: `9 passed in 0.46s`.
- Full lint: `All checks passed!`.
- Full pytest: `247 passed in 18.62s`.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Known Limitations

- `resident_artifacts.json` does not yet mirror coverage/low/high rejection map
  paths; the strict audit verifies the maps through `integration_results.json`.
- Rejection sample-sum tolerance is necessary because persisted integer count
  maps can differ by a few samples from the floating in-memory provenance sum.
- This gate strengthens real-data evidence for resident CUDA audit output maps;
  it does not change the science-mode release benchmark contract.

## Next Step

Mirror all resident output map paths into `resident_artifacts.json` so
integration and resident artifact records are equally self-contained for audit
consumers.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned outputs and user-generated reference
timing/output data only. No external implementation source was read or used.
