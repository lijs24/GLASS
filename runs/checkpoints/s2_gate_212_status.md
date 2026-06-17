# S2-Gate 212 Status: Runtime Sweep Uses Native Guardrails Bundle

- Gate: S2-Gate 212
- Status: green
- Date: 2026-06-18
- Scope: candidate runtime sweep planning now prefers native guardrails bundles and run-default resident result contracts

## Completed

- Updated generated candidate runtime sweep plans to use `glass guardrails` as the contract/report step for new resident CUDA variants.
- Removed separate generated resident calibration/result bridge-contract commands from new sweep plans.
- Changed generated acceptance-audit commands to consume the guardrails `acceptance_contract_bundle.json`.
- Recorded run-local native artifacts in each planned variant:
  - `RUN/calibration_artifacts.json`
  - `RUN/resident_result_contract.json`
  - guardrails summary/report
  - guardrails pipeline and StackEngine contracts
  - guardrails acceptance contract bundle
- Preserved executor compatibility with older plans that still contain separate resident calibration/result, StackEngine, and pipeline contract commands.
- Updated Phase 2 hardening documentation with S2-Gate 212.

## Commands Run

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\candidate_runtime_sweep_plan.py src\\glass\\report\\candidate_runtime_sweep_execute.py tests\\test_candidate_runtime_sweep_plan.py tests\\test_candidate_runtime_sweep_execute.py docs\\phase2_algorithm_hardening.md`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_candidate_runtime_sweep_plan.py tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py::test_cli_help_commands`
- `.\\.venv\\Scripts\\glass.exe candidate-runtime-sweep-plan --comparison "C:\\glass_runs\\phase2_s2_gate_160_preset_confirmation\\comparison\\throughput_v1_candidate_comparison.json" --root "C:\\glass_runs\\phase2_s2_gate_212_native_guardrails_sweep_plan" --base-run-command "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\run_command.txt" --baseline-run "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident" --baseline-compare-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_vs_reference.json" --reference "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --manifest "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\manifest.json" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json --out runs\\checkpoints\\s2_gate_212_runtime_sweep_plan.json --markdown runs\\checkpoints\\s2_gate_212_runtime_sweep_plan.md --variant retry_settings_control --prefetch-frame 12 --prefetch-worker 7 --min-speedup-vs-reference 20`
- `.\\.venv\\Scripts\\glass.exe candidate-runtime-sweep-execute --plan runs\\checkpoints\\s2_gate_212_runtime_sweep_plan.json --out runs\\checkpoints\\s2_gate_212_runtime_sweep_execute_dry_run.json --dry-run --variant retry_settings_control`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_vs_reference.json" --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json --contract-bundle "C:\\glass_runs\\phase2_s2_gate_211_native_result_contract\\guardrails\\acceptance_contract_bundle.json" --out runs\\checkpoints\\s2_gate_212_acceptance_real_native_guardrails_bundle.json --markdown runs\\checkpoints\\s2_gate_212_acceptance_real_native_guardrails_bundle.md --min-active-frames 190`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe doctor --allow-cpu-only --json runs\\checkpoints\\s2_gate_212_doctor.json`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_212_acceptance_real_native_guardrails_bundle.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_197_github_release_plan_publish_script.json --out runs\\checkpoints\\s2_gate_212_phase2_status.json --markdown runs\\checkpoints\\s2_gate_212_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_211_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_212_phase2_status.json --out runs\\checkpoints\\s2_gate_212_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_212_phase2_status_compare.md --fail-on-regression`

## Test Results

- Focused tests: 9 passed in 1.18 s.
- Full pytest: 499 passed in 26.68 s.
- Ruff: all checks passed.
- Doctor: passed with CUDA native extension available.
- Runtime sweep plan generation: passed over real 200-light candidate comparison inputs.
- Runtime sweep dry-run execution: passed.
- Real 200-light acceptance audit through guardrails bundle: passed.
- Phase 2 status: green, latest gate 212.
- Phase 2 status compare against Gate211: passed, no regression.

## Real Benchmark Evidence

- GLASS resident CUDA elapsed time: 18.804783 s.
- PixInsight/WBPP black-box elapsed time: 1092.541 s.
- Speedup vs WBPP: 58.0991x.
- Active weighted frames: 193.
- Generated sweep variant count: 2.
- New variant command keys: `run`, `compare_reference`, `compare_baseline`, `guardrails`, `acceptance_audit`, `candidate_comparison`.
- Legacy bridge commands generated by new plan: none.
- Planned resident result contract source: `run_default`.
- Dry-run execution order: `run`, `compare_reference`, `compare_baseline`, `guardrails`, `acceptance_audit`, `candidate_comparison`.

## Artifacts

- `runs/checkpoints/s2_gate_212_status.md`
- `runs/checkpoints/s2_gate_212_doctor.json`
- `runs/checkpoints/s2_gate_212_runtime_sweep_plan.json`
- `runs/checkpoints/s2_gate_212_runtime_sweep_plan.md`
- `runs/checkpoints/s2_gate_212_runtime_sweep_execute_dry_run.json`
- `runs/checkpoints/s2_gate_212_acceptance_real_native_guardrails_bundle.json`
- `runs/checkpoints/s2_gate_212_acceptance_real_native_guardrails_bundle.md`
- `runs/checkpoints/s2_gate_212_phase2_status.json`
- `runs/checkpoints/s2_gate_212_phase2_status.md`
- `runs/checkpoints/s2_gate_212_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_212_phase2_status_compare.md`
- `C:\\glass_runs\\phase2_s2_gate_212_native_guardrails_sweep_plan`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package recommendation: cuda13, with cuda12/cuda11/cpu fallback order.

## Known Limitations

- This gate changes planning/orchestration only; it does not change image math, CUDA kernels, or measured runtime.
- The new sweep plan is generated and dry-run audited, not executed end-to-end.
- Old sweep plans remain supported and may still contain separate bridge-contract commands.
- The real 200-light acceptance evidence reuses existing resident CUDA outputs and guardrails bundle; raw images were not reprocessed.

## Next Step

Proceed to the next Phase 2 gate by making release handoff/status reports call out native guardrails-bundle resident contract provenance and by retiring bridge-contract wording from generated release plans where native artifacts are present.

## Clean-Room Compliance

Compliant. This gate used GLASS source code and GLASS/user-generated artifacts only. It did not read or reuse official PixInsight/WBPP/PJSR source code.
