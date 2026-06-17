# S2-Gate 208 Status: Resident Calibration Release Contract Bridge

- Gate: S2-Gate 208
- Status: green
- Date: 2026-06-18
- Scope: resident CUDA calibration contract bridge for release guardrails

## Gate

S2-Gate 208: Resident Calibration Release Contract Bridge

## Status

Green.

## Completed

- Added `--resident-calibration-contract-json` to `glass pipeline-contract`.
- Plumbed resident calibration contracts from `glass guardrails` into the unified pipeline invariant audit.
- Added resident calibration surface rows and the `resident_calibration_surface_contract` check.
- Kept Gate207 local `calibration_artifacts.json` checks active for local calibrated-light DQ artifacts.
- Hardened `benchmarks/phase2_m38_h_200_contract.json` so the 200-light acceptance baseline requires:
  - `calibration_master_surface_contract`
  - `resident_calibration_surface_contract`
  - `integration_resident_result_contract`
- Regenerated real 200-light read-only guardrails and acceptance evidence from the existing resident CUDA run.

## Commands Run

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\pipeline_contract.py src\\glass\\cli.py tests\\test_pipeline_contract.py tests\\test_acceptance_audit.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_acceptance_audit.py::test_acceptance_audit_applies_benchmark_pipeline_contract tests/test_acceptance_audit.py::test_acceptance_audit_cli_writes_pipeline_contract_evidence tests/test_cli_smoke.py::test_cli_help_commands tests/test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report`
- `.\\.venv\\Scripts\\glass.exe guardrails --run "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident" --out-dir "C:\\glass_runs\\phase2_s2_gate_208_real_bridge\\guardrails" --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\resident_calibration_contract.json" --resident-result-contract-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\resident_result_contract.json" --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 2048`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_vs_reference.json" --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json --contract-bundle "C:\\glass_runs\\phase2_s2_gate_208_real_bridge\\guardrails\\acceptance_contract_bundle.json" --out runs\\checkpoints\\s2_gate_208_acceptance_real_bridge.json --markdown runs\\checkpoints\\s2_gate_208_acceptance_real_bridge.md --min-active-frames 190`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe doctor --allow-cpu-only --json runs\\checkpoints\\s2_gate_208_doctor.json`

## Test Results

- Focused contract tests: 14 passed.
- Full pytest: 492 passed in 26.67 s.
- Ruff: all checks passed.
- Real 200-light guardrails: passed.
- Real 200-light acceptance audit: passed.
- Phase 2 status: green.
- Phase 2 status compare against Gate207: passed, no regression.

## Real Benchmark Evidence

- GLASS resident CUDA elapsed time: 18.804783 s.
- PixInsight/WBPP black-box elapsed time: 1092.541 s.
- Speedup vs WBPP: 58.0991x.
- Active weighted frames: 193.
- Coverage fraction: 0.957792.
- RMS difference: 0.00149455.
- Absolute difference p99: 0.000435446.
- New pipeline contract status: passed.
- Resident calibration contract attached: true.
- Resident calibration master count: 1.

## Artifacts

- `runs/checkpoints/s2_gate_208_acceptance_real_bridge.json`
- `runs/checkpoints/s2_gate_208_acceptance_real_bridge.md`
- `runs/checkpoints/s2_gate_208_acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_208_guardrails_summary.json`
- `runs/checkpoints/s2_gate_208_pipeline_contract.json`
- `runs/checkpoints/s2_gate_208_pipeline_contract.md`
- `runs/checkpoints/s2_gate_208_stack_engine_contract.json`
- `runs/checkpoints/s2_gate_208_stack_engine_contract.md`
- `runs/checkpoints/s2_gate_208_doctor.json`
- `runs/checkpoints/s2_gate_208_phase2_status.json`
- `runs/checkpoints/s2_gate_208_phase2_status.md`
- `runs/checkpoints/s2_gate_208_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_208_phase2_status_compare.md`
- `C:\\glass_runs\\phase2_s2_gate_208_real_bridge\\guardrails\\report.html`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package recommendation: cuda13, with cuda12/cuda11/cpu fallback order.

## Known Limitations

- This gate is a release-contract bridge only; it does not change image processing algorithms.
- The resident CUDA run still does not emit a local `calibration_artifacts.json`; resident calibration evidence is attached through `resident_cuda_calibration_contract`.
- Registration, local normalization, and integration remain WBPP-like but not PixInsight-equivalent.
- No new raw data processing was performed in this gate; existing 200-light run outputs were audited read-only.

## Next Step

Proceed to the next Phase 2 gate by hardening the next missing scientific contract or by converting more resident CUDA evidence into first-class pipeline artifacts.

## Clean-Room Compliance

Compliant. This gate used GLASS source code, GLASS artifacts, user-generated PixInsight/WBPP black-box timing/output metadata, and existing resident CUDA contract JSON. It did not read or reuse official PixInsight/WBPP/PJSR source code.
