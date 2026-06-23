# S2-Gate 577 Status: LN-On Coverage Contract Semantics

## Gate

- Gate: S2-Gate 577
- Objective: turn Gate576's LN-on coverage finding into a formal benchmark contract and acceptance-audit semantic check, so the default 200-light route no longer depends on a one-off `--min-coverage-fraction 0.90` override.
- Status: green
- Clean-room status: compliant. This gate uses GLASS compare JSON, GLASS resident DQ provenance, GLASS contracts, and user-generated WBPP black-box timing/reference output only. It does not inspect external implementation source or modify input image directories.

## Completed

- Added benchmark-contract support for `coverage_fraction_semantics`.
- Added semantic verification for `post_rejection_coverage_map_fraction`:
  - the compare JSON must identify the coverage map;
  - the coverage map must match a GLASS DQ provenance record;
  - that record must expose `post_rejection_coverage` provenance.
- Let benchmark contracts provide the effective top-level acceptance thresholds for:
  - `min_coverage_fraction`;
  - `max_rms_diff`;
  - `max_abs_diff_p99`.
- Added `benchmarks/phase2_m38_h_200_ln_on_default_contract.json`.
- Added a focused unit test proving the LN-on contract threshold drives acceptance without passing a CLI `--min-coverage-fraction` override.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

- `.venv\Scripts\python.exe -m py_compile src\glass\report\acceptance_audit.py src\glass\report\benchmark_contract.py tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py::test_acceptance_audit_contract_can_pin_ln_on_post_rejection_coverage tests\test_acceptance_audit.py::test_acceptance_audit_applies_benchmark_contract tests\test_acceptance_audit.py::test_acceptance_audit_contract_catches_missing_parameters`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\manifest.json --glass-run C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate577_ln_on_contract\acceptance_audit_ln_on_contract.json --markdown C:\glass_runs\phase2_s2_gate577_ln_on_contract\acceptance_audit_ln_on_contract.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\stack_engine_contract.json`
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py`

## Test Results

- Focused acceptance/contract tests: `3 passed in 0.32s`
- Acceptance-audit test file: `46 passed in 1.16s`
- Full pytest: `1239 passed in 47.08s`

## Real 200-Light Validation

- Source run reused: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass`
- Acceptance artifact: `C:\glass_runs\phase2_s2_gate577_ln_on_contract\acceptance_audit_ln_on_contract.json`
- Markdown artifact: `C:\glass_runs\phase2_s2_gate577_ln_on_contract\acceptance_audit_ln_on_contract.md`
- Benchmark contract: `benchmarks\phase2_m38_h_200_ln_on_default_contract.json`
- Acceptance status: `passed`
- Acceptance checks: `108`, failed `0`
- Speedup vs WBPP: `136.9864061455573x`
- Coverage threshold source: `benchmark_contract`
- Coverage semantics: `post_rejection_coverage_map_fraction`
- Coverage190 actual/required: `0.905523489118409 / 0.90`
- Matched DQ provenance records for compare coverage map: `2`
- Required DQ source terms passed:
  - `post_rejection_coverage`
  - `geometric_warp_coverage`
  - `low_rejection`
  - `high_rejection`
- Pipeline contract: `passed`
- StackEngine default-promotion contract: `passed`

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Known Limitations

- This gate formalizes the current LN-on post-rejection coverage semantics; it does not change image math or improve coverage.
- The old LN-off and audit-map contracts remain separate and keep their own stricter coverage assumptions.
- If future LN, rejection, or coverage-map semantics change, the benchmark contract must be updated with fresh real-data evidence.

## Next Step

Continue Phase 2 core engineering with either StackEngine native/default surface closure or DQ/mask pipeline completeness work that changes runtime behavior or formal contracts, then rerun the real 200-light acceptance chain.
