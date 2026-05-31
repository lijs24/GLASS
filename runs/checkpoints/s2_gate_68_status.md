# S2-Gate 68 Status: Resident Drift Contract Thresholds

## Gate

S2-Gate 68 - Resident Drift Contract Thresholds.

## Completed

- Added optional `resident_determinism` benchmark-contract checks.
- Default acceptance behavior is unchanged; resident drift checks run only when a benchmark contract declares the `resident_determinism` section.
- Supported contract checks:
  - resident determinism artifact presence;
  - optional strict determinism pass requirement;
  - maximum output numerical drift row count;
  - maximum relative output RMS drift;
  - maximum absolute output RMS drift;
  - maximum output mean absolute drift.
- Added a real M38 H-alpha 200-light resident drift contract:
  - `benchmarks/phase2_m38_h_200_resident_drift_contract.json`
- Updated Phase 2 plan and algorithm-source ledger for S2-Gate 68.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py::test_acceptance_audit_applies_resident_drift_contract tests\test_acceptance_audit.py::test_acceptance_audit_resident_drift_contract_catches_excessive_drift tests\test_acceptance_audit.py::test_acceptance_audit_cli_writes_outputs_and_returns_failure
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\manifest.json --glass-run C:\glass_runs\final_m38_h_200\glass_current_20260514_154556 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\compare_vs_reference_scaled_coverage190.json --benchmark-contract benchmarks\phase2_m38_h_200_resident_drift_contract.json --resident-determinism-json C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.json --out C:\glass_runs\phase2_s2_gate_68_200\acceptance_resident_drift_contract.json --markdown C:\glass_runs\phase2_s2_gate_68_200\acceptance_resident_drift_contract.md --min-active-frames 190
Select-String -Path C:\glass_runs\phase2_s2_gate_68_200\acceptance_resident_drift_contract.md -Pattern "contract_resident_determinism|contract_output_numerical_drift|Resident Determinism|Speedup"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor
```

## Test Results

- Focused resident drift contract tests: `3 passed in 0.15s`.
- Ruff: `All checks passed!`.
- Full pytest: `271 passed in 11.51s`.
- Real 200-light resident drift contract acceptance audit: `passed`.
  - Speedup vs WBPP: `34.665737721106105x`.
  - Failed checks: `0`.
  - `contract_resident_determinism_present`: pass.
  - `contract_output_numerical_drift_count`: pass, `1 <= 1`.
  - `contract_output_numerical_drift_relative_rms`: pass, `0.011915983618972378 <= 0.02`.
  - `contract_output_numerical_drift_rms`: pass, `3.7514002323150635 <= 4.0`.
  - `contract_output_numerical_drift_mean_abs`: pass, `0.6422600150108337 <= 1.0`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_68_200\acceptance_resident_drift_contract.json`
- `C:\glass_runs\phase2_s2_gate_68_200\acceptance_resident_drift_contract.md`
- `benchmarks/phase2_m38_h_200_resident_drift_contract.json`

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- Drift thresholds currently apply to the already computed resident determinism drift rows; they do not compute new image comparisons inside the contract checker.
- The first real contract is tuned for the measured Gate63-vs-Gate64 fast-coarse drift and should be revisited if fast-mode math changes.
- Strict hash determinism remains optional because fast performance modes may intentionally differ numerically from conservative baselines while staying within bounded drift.

## Next Step

S2-Gate 69 should return to runtime optimization now that drift is contractable. The highest-impact target remains resident registration/warp batching, especially reducing per-frame orchestration and host/device synchronization while keeping the new drift contract green.

## Clean-Room

Compliant. This gate only checks GLASS-generated resident-determinism statistics and user-generated benchmark/reference metadata. It does not read, copy, summarize, or rework PixInsight/WBPP implementation source.
