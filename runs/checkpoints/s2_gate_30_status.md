# S2-Gate 30 Status: Coverage And Rejection Map Consistency Verification

## Gate

S2-Gate 30 extends acceptance-audit verification from DQ bitfields to related
coverage and rejection count maps.

## Completed Content

- Extended `src/glass/report/dq_map_verify.py` with tiled scalar count-map
  summaries.
- Added optional benchmark-contract fields:
  - `verify_output_count_maps`
  - `count_map_verify_tile_size`
  - `count_map_positive_threshold`
  - `coverage_map_finite_pixels_match_provenance`
  - `coverage_zero_pixels_match_no_data`
  - `allow_missing_rejection_maps_if_skipped`
  - `rejection_map_sum_matches_provenance`
- Acceptance audit now records `output_count_map_verification` per DQ
  provenance record.
- Coverage map checks compare finite-pixel count against
  `dq_coverage_provenance.post_rejection_coverage.finite_pixels`.
- Coverage zero-or-less pixels are checked against DQ `NO_DATA` counts when the
  contract opts into that resident invariant.
- Low/high rejection maps are verified against DQ low/high flags when written.
  If a resident output-map policy skips those maps, audit records an explicit
  skipped-policy PASS instead of silently ignoring them.
- Updated the 200-light benchmark contract, Phase 2 gate document, and
  algorithm source log.
- Added synthetic fixture tests for written rejection maps and direct count-map
  summaries.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\dq_map_verify.py src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py tests\test_dq_map_verify.py tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_dq_map_verify.py tests\test_acceptance_audit.py`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --out C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_30.json --markdown C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_30.md --min-active-frames 190 --min-speedup 2.0`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results

- Targeted tests: `8 passed in 0.29s`.
- Full lint: `All checks passed!`.
- Full pytest: `246 passed in 11.93s`.
- Preserved 200-light acceptance audit: `passed`.
- New 200-light audit artifacts:
  - `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_30.json`
  - `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_30.md`

## 200-Light Map Consistency Results

- Coverage map verified records: `1`.
- Coverage finite pixels: `61651200`, matching provenance with delta `0`.
- Coverage zero-or-less pixels: `0`, matching DQ `NO_DATA` count with delta
  `0`.
- Low rejection map: skipped by resident `science` output-map policy.
- High rejection map: skipped by resident `science` output-map policy.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Real-Data Benchmark Note

This gate did not rerun the 200-light stack because it changes audit
verification only, not image math, resident kernels, resident routing, or
benchmark command parameters. It did read the preserved resident coverage and
DQ FITS maps from the latest S2-Gate 24 200-light run.

The preserved benchmark remains:

- Speedup: `35.30098690673237x`
- RMS vs reference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`

## Known Limitations

- The latest preserved 200-light run used resident `science` output-map policy,
  so low/high rejection FITS maps were intentionally skipped and only the
  policy skip was audited for real data.
- Rejection-map positive-pixel and rejected-sample sum checks are covered by
  synthetic acceptance-audit fixtures and will be real-data verified on an
  `audit` output-map run.
- Coverage zero-to-`NO_DATA` exact matching is a resident invariant for the
  current contract; future engines with additional no-data sources may need a
  subset-style check instead.

## Next Step

Run or reuse an audit-mode resident artifact set that writes low/high rejection
count maps, then promote real-data rejection-map positive-pixel and sample-sum
verification from synthetic coverage to real-data evidence.

## Clean-Room Compliance

Compliant. This gate reads GLASS-owned FITS artifacts and user-generated
benchmark outputs only. No external implementation source was read or used.
