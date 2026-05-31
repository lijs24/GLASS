# S2-Gate 28 Status: DQ Provenance Acceptance Contract

## Gate

S2-Gate 28 extends the benchmark acceptance contract so GLASS can audit DQ
provenance as a formal real-data benchmark requirement.

## Completed Content

- Added DQ provenance collection to `acceptance-audit`.
- Added normalized audit records from `integration_results.json` and
  `resident_artifacts.json`.
- Preserved compatibility with older resident artifacts by converting legacy
  `dq_coverage_provenance` plus `dq_summary` into the compact S2-Gate 27
  `dq_provenance_summary` shape during audit.
- Extended `benchmarks/phase2_m38_h_200_contract.json` with DQ provenance
  requirements for resident source schema, engine, active-frame count, DQ map
  presence, source terms, and output DQ flags.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.
- Added positive and negative acceptance-audit tests for the DQ contract.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\s2_gate_24_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --out C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_28.json --markdown C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_28.md --min-active-frames 190 --min-speedup 2.0`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results

- Targeted acceptance tests: `6 passed in 0.22s`.
- Full lint: `All checks passed!`.
- Full pytest: `244 passed in 12.21s`.
- 200-light preserved-artifact acceptance audit: `passed`.
- New 200-light audit artifacts:
  - `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_28.json`
  - `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531\phase2_contract_acceptance_audit_s2_gate_28.md`

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Real-Data Benchmark Note

This gate did not rerun the 200-light stack because it changes audit/report
contract code only, not image math, resident kernels, resident routing, or
benchmark command parameters. It did rerun the acceptance audit against the
latest preserved S2-Gate 24 200-light resident artifacts. The audit passed with
speedup `35.30098690673237x`, RMS `0.001558294284488301`, P99 absolute
difference `0.00043095467146486016`, and DQ provenance record count `2`.

## Known Limitations

- The DQ contract verifies artifact presence and summary consistency. It does
  not read FITS DQ map pixels during acceptance audit.
- Legacy resident normalization is intentionally limited to GLASS resident
  artifacts that already contain `dq_coverage_provenance` and `dq_summary`.
- Calibration-stage CPU StackEngine DQ artifacts are collected by report paths,
  but this benchmark contract currently focuses on resident integration DQ
  provenance because the 200-light baseline is a resident CUDA run.

## Next Step

Continue hardening the formal DQ pipeline contract. The next useful gate is to
add a machine-readable DQ map pixel verifier for small synthetic runs so
acceptance can prove selected DQ flag counts from FITS pixels, not only JSON
summaries.

## Clean-Room Compliance

Compliant. This gate consumes only GLASS-owned artifacts and user-generated
benchmark outputs. No external implementation source was read or used.
