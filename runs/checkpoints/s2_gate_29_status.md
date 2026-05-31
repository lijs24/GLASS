# S2-Gate 29 Status: DQ FITS Map Pixel Verification

## Gate

S2-Gate 29 adds pixel-level verification for DQ FITS maps so acceptance audits
can prove selected artifact summary counts against the actual map pixels.

## Completed Content

- Added `src/glass/report/dq_map_verify.py`.
- Implemented tiled DQ FITS reading and bitfield counting for `valid`,
  `NO_DATA`, `WARP_EDGE`, `LOW_REJECTED`, `HIGH_REJECTED`, and any other known
  `DQFlag` name requested by a contract.
- Added optional benchmark-contract fields:
  - `verify_dq_map_pixels`
  - `dq_map_verify_tile_size`
  - `dq_map_summary_tolerance_pixels`
  - `dq_map_summary_match_flags`
- Extended acceptance-audit DQ records with `dq_map_pixel_verification`.
- Updated `benchmarks/phase2_m38_h_200_contract.json` so the 200-light resident
  benchmark verifies `valid`, `warp_edge`, `low_rejected`, and `high_rejected`
  counts from the actual resident DQ FITS map.
- Added direct DQ map verifier tests and extended acceptance-audit tests.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\dq_map_verify.py src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py tests\test_dq_map_verify.py tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_dq_map_verify.py tests\test_acceptance_audit.py`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --out C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_29.json --markdown C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_29.md --min-active-frames 190 --min-speedup 2.0`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results

- Targeted tests: `7 passed in 0.41s`.
- Full lint: `All checks passed!`.
- Full pytest: `245 passed in 18.87s`.
- Preserved 200-light acceptance audit: `passed`.
- New 200-light audit artifacts:
  - `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_29.json`
  - `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_29.md`

## 200-Light DQ Pixel Verification

The latest preserved 200-light resident artifact DQ FITS map was read in tiles
and matched the JSON summary with zero delta:

- `valid`: `20947307`
- `warp_edge`: `5396832`
- `low_rejected`: `13074085`
- `high_rejected`: `32318219`

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
benchmark command parameters. It did read the preserved resident DQ FITS map
for the latest S2-Gate 24 200-light run and verified the selected DQ counts.

The preserved benchmark remains:

- Speedup: `35.30098690673237x`
- RMS vs reference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`

## Known Limitations

- Pixel verification is opt-in because reading full-size DQ maps adds audit
  I/O.
- The current 200-light contract verifies selected DQ flags, not every possible
  `DQFlag` bit.
- The verifier checks map count consistency, not whether each flag was
  semantically set by the ideal upstream stage.

## Next Step

Continue the DQ hardening path by verifying coverage-map and rejection-map
consistency against DQ summaries on small synthetic runs, then promote selected
checks into the real-data contract when they are stable.

## Clean-Room Compliance

Compliant. This gate reads GLASS-owned FITS artifacts and user-generated
benchmark outputs only. No external implementation source was read or used.
