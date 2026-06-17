# S2-Gate 210 Status: Native Resident Calibration Reporting

- Gate: S2-Gate 210
- Status: green
- Date: 2026-06-18
- Scope: native resident calibration artifact reporting, frame accounting, and guardrails visibility

## Completed

- Added native resident calibration artifact evidence to `frame_accounting.json`:
  - top-level `resident_native_calibration_artifact`
  - top-level `calibration_artifact_type`
  - summary `calibration_master_count`
  - summary `resident_calibrated_light_ledger_rows`
  - per-frame calibration backend, source stage, resident stack index, resident output index, and resident master path
- Added an HTML report section for resident calibration artifacts:
  - artifact summary
  - resident master bias/dark/flat surfaces
  - per-light in-VRAM calibration ledger rows
- Extended pipeline contract report tables with resident-native calibration summary and resident calibrated-light contract fields.
- Added native resident calibration evidence to `glass guardrails` summaries and acceptance bundles.
- Updated Phase 2 hardening documentation with S2-Gate 210.
- Kept this gate reporting/accounting only. No image processing algorithm or CUDA kernel math changed.

## Commands Run

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\frame_accounting.py src\\glass\\report\\html_report.py src\\glass\\cli.py tests\\test_frame_accounting.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_frame_accounting.py tests/test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests/test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report`
- `.\\.venv\\Scripts\\python.exe -c "from glass.engine.frame_accounting import build_frame_accounting; build_frame_accounting(r'C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view')"`
- `.\\.venv\\Scripts\\glass.exe guardrails --run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --out-dir "C:\\glass_runs\\phase2_s2_gate_210_native_reporting\\guardrails" --expected-integration-engine cuda_resident_stack --resident-result-contract-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\resident_result_contract.json" --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 2048`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_vs_reference.json" --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json --contract-bundle "C:\\glass_runs\\phase2_s2_gate_210_native_reporting\\guardrails\\acceptance_contract_bundle.json" --out runs\\checkpoints\\s2_gate_210_acceptance_real_native_reporting.json --markdown runs\\checkpoints\\s2_gate_210_acceptance_real_native_reporting.md --min-active-frames 190`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe doctor --allow-cpu-only --json runs\\checkpoints\\s2_gate_210_doctor.json`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_210_acceptance_real_native_reporting.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_197_github_release_plan_publish_script.json --out runs\\checkpoints\\s2_gate_210_phase2_status.json --markdown runs\\checkpoints\\s2_gate_210_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_209_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_210_phase2_status.json --out runs\\checkpoints\\s2_gate_210_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_210_phase2_status_compare.md --fail-on-regression`

## Test Results

- Focused tests: 5 passed in 0.54 s.
- Full pytest: 496 passed in 26.55 s.
- Ruff: all checks passed.
- Doctor: passed with CUDA native extension available.
- Real 200-light guardrails: passed.
- Real 200-light acceptance audit: passed.
- Native resident calibration artifact present in guardrails summary.
- Native resident calibrated-light ledger rows: 200.
- Native resident calibration master rows: 3.
- Phase 2 status: green, latest gate 210.
- Phase 2 status compare against Gate209: passed, no regression.

## Real Benchmark Evidence

- GLASS resident CUDA elapsed time: 18.804783 s.
- PixInsight/WBPP black-box elapsed time: 1092.541 s.
- Speedup vs WBPP: 58.0991x.
- Active weighted frames: 193.
- Native resident calibration artifact: true.
- Native resident calibrated-light ledger rows: 200.
- Native resident master surface rows: 3.
- Resident result contract attached: true.
- Resident calibration bridge contract attached: false.

## Artifacts

- `runs/checkpoints/s2_gate_210_status.md`
- `runs/checkpoints/s2_gate_210_doctor.json`
- `runs/checkpoints/s2_gate_210_frame_accounting.json`
- `runs/checkpoints/s2_gate_210_guardrails_summary.json`
- `runs/checkpoints/s2_gate_210_pipeline_contract.json`
- `runs/checkpoints/s2_gate_210_pipeline_contract.md`
- `runs/checkpoints/s2_gate_210_stack_engine_contract.json`
- `runs/checkpoints/s2_gate_210_stack_engine_contract.md`
- `runs/checkpoints/s2_gate_210_acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_210_acceptance_real_native_reporting.json`
- `runs/checkpoints/s2_gate_210_acceptance_real_native_reporting.md`
- `runs/checkpoints/s2_gate_210_phase2_status.json`
- `runs/checkpoints/s2_gate_210_phase2_status.md`
- `runs/checkpoints/s2_gate_210_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_210_phase2_status_compare.md`
- `C:\\glass_runs\\phase2_s2_gate_210_native_reporting\\guardrails\\report.html`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package recommendation: cuda13, with cuda12/cuda11/cpu fallback order.

## Known Limitations

- This gate makes resident calibration evidence visible in accounting, reports, and guardrails; it does not change calibration math or image processing kernels.
- Resident calibrated-light rows are in-VRAM ledger records, not disk-backed calibrated FITS files.
- The 200-light evidence reused the existing resident CUDA run and refreshed the contract/report view; raw images were not reprocessed.
- Guardrails still attach the resident result contract for integration evidence.

## Next Step

Proceed to the next Phase 2 gate by reducing dependence on separately generated resident result bridge artifacts and pushing more resident integration evidence into first-class native run artifacts.

## Clean-Room Compliance

Compliant. This gate used GLASS source code and GLASS/user-generated artifacts only. It did not read or reuse official PixInsight/WBPP/PJSR source code.
