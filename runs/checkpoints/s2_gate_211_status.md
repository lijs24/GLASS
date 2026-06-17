# S2-Gate 211 Status: Native Resident Result Contract Artifact

- Gate: S2-Gate 211
- Status: green
- Date: 2026-06-18
- Scope: native resident CUDA result-contract artifact and guardrails auto-discovery

## Completed

- Resident CUDA runs now write `resident_result_contract.json` after `integration_results.json`.
- The native resident result contract is registered in `run_state.json` artifacts as `resident_result_contract`.
- `build_stack_engine_contract_audit` now auto-discovers `RUN/resident_result_contract.json` when no explicit resident result contract payload is supplied.
- `glass guardrails` now auto-discovers and bundles `RUN/resident_result_contract.json` when `--resident-result-contract-json` is omitted.
- Explicit `--resident-result-contract-json` remains the override path for older scripts and sweep plans.
- Resident result-contract checks now respect output-map policy when coverage/rejection maps are intentionally not written.
- Updated Phase 2 hardening documentation with S2-Gate 211.

## Commands Run

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\resident_result_contract.py src\\glass\\engine\\resident_cuda.py src\\glass\\cli.py src\\glass\\report\\stack_engine_contract.py tests\\test_resident_result_contract.py tests\\test_resident_cuda_run.py tests\\test_stack_engine_contract.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_resident_result_contract.py tests/test_stack_engine_contract.py::test_stack_engine_contract_auto_discovers_native_resident_result_contract tests/test_cli_smoke.py::test_cli_guardrails_auto_discovers_run_resident_result_contract tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `.\\.venv\\Scripts\\glass.exe resident-result-contract --run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --out "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view\\resident_result_contract.json" --markdown "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view\\resident_result_contract.md" --pixel-verify --pixel-verify-tile-size 2048 --fail-on-failed`
- `.\\.venv\\Scripts\\glass.exe guardrails --run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --out-dir "C:\\glass_runs\\phase2_s2_gate_211_native_result_contract\\guardrails" --expected-integration-engine cuda_resident_stack --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 2048`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_vs_reference.json" --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json --contract-bundle "C:\\glass_runs\\phase2_s2_gate_211_native_result_contract\\guardrails\\acceptance_contract_bundle.json" --out runs\\checkpoints\\s2_gate_211_acceptance_real_native_result_contract.json --markdown runs\\checkpoints\\s2_gate_211_acceptance_real_native_result_contract.md --min-active-frames 190`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe doctor --allow-cpu-only --json runs\\checkpoints\\s2_gate_211_doctor.json`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_211_acceptance_real_native_result_contract.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_197_github_release_plan_publish_script.json --out runs\\checkpoints\\s2_gate_211_phase2_status.json --markdown runs\\checkpoints\\s2_gate_211_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_210_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_211_phase2_status.json --out runs\\checkpoints\\s2_gate_211_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_211_phase2_status_compare.md --fail-on-regression`

## Test Results

- Focused tests: 7 passed in 0.59 s.
- Full pytest: 499 passed in 26.94 s.
- Ruff: all checks passed.
- Doctor: passed with CUDA native extension available.
- Real 200-light resident result contract: passed with pixel verification enabled.
- Real 200-light guardrails: passed without `--resident-result-contract-json`.
- Real 200-light acceptance audit: passed.
- Phase 2 status: green, latest gate 211.
- Phase 2 status compare against Gate210: passed, no regression.

## Real Benchmark Evidence

- GLASS resident CUDA elapsed time: 18.804783 s.
- PixInsight/WBPP black-box elapsed time: 1092.541 s.
- Speedup vs WBPP: 58.0991x.
- Active weighted frames: 193.
- Native resident result contract path: `C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view\\resident_result_contract.json`.
- Native resident result contract source in guardrails: `run_default`.
- Native resident result contract attached in guardrails: true.
- Native resident result contract pixel verification: true.
- Native resident calibration artifact: true.
- Native resident calibrated-light ledger rows: 200.

## Artifacts

- `runs/checkpoints/s2_gate_211_status.md`
- `runs/checkpoints/s2_gate_211_doctor.json`
- `runs/checkpoints/s2_gate_211_resident_result_contract.json`
- `runs/checkpoints/s2_gate_211_resident_result_contract.md`
- `runs/checkpoints/s2_gate_211_frame_accounting.json`
- `runs/checkpoints/s2_gate_211_guardrails_summary.json`
- `runs/checkpoints/s2_gate_211_pipeline_contract.json`
- `runs/checkpoints/s2_gate_211_pipeline_contract.md`
- `runs/checkpoints/s2_gate_211_stack_engine_contract.json`
- `runs/checkpoints/s2_gate_211_stack_engine_contract.md`
- `runs/checkpoints/s2_gate_211_acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_211_acceptance_real_native_result_contract.json`
- `runs/checkpoints/s2_gate_211_acceptance_real_native_result_contract.md`
- `runs/checkpoints/s2_gate_211_phase2_status.json`
- `runs/checkpoints/s2_gate_211_phase2_status.md`
- `runs/checkpoints/s2_gate_211_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_211_phase2_status_compare.md`
- `C:\\glass_runs\\phase2_s2_gate_211_native_result_contract\\guardrails\\report.html`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package recommendation: cuda13, with cuda12/cuda11/cpu fallback order.

## Known Limitations

- This gate changes artifact generation and contract discovery only; it does not change integration math or CUDA kernels.
- The 200-light evidence refreshed the contract/report view of the existing resident CUDA run; raw images were not reprocessed.
- Older resident runs still need `glass resident-result-contract --run RUN --out RUN/resident_result_contract.json` once before they can use run-default auto-discovery.
- Guardrails still accepts explicit resident result contract paths for older sweep plans.

## Next Step

Proceed to the next Phase 2 gate by making acceptance and release handoff tooling prefer native run-default resident result contracts and by reducing legacy external bridge references in generated sweep plans.

## Clean-Room Compliance

Compliant. This gate used GLASS source code and GLASS/user-generated artifacts only. It did not read or reuse official PixInsight/WBPP/PJSR source code.
