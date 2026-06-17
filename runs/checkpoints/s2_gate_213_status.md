# S2-Gate 213 Status

- Status: green
- Date: 2026-06-18
- Scope: native guardrails bundle release provenance

## Completed

- Added `native_guardrails_bundle` provenance to acceptance-audit JSON and Markdown.
- Propagated resident result contract source/path, run-default discovery, native calibration artifact presence, master count, and resident calibrated-light count into Phase 2 status JSON and Markdown.
- Added the same native provenance to Windows GitHub release plan notes and preflight Markdown when Phase 2 status contains native bundle evidence.
- Updated Phase 2 hardening docs with S2-Gate 213.
- Added focused tests for acceptance audit, Phase 2 status, and Windows release-plan handoff output.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\acceptance_audit.py src\glass\report\phase2_status.py src\glass\report\windows_github_release_plan.py tests\test_acceptance_audit.py tests\test_phase2_status.py tests\test_windows_github_release_plan.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py tests/test_phase2_status.py tests/test_windows_github_release_plan.py`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\manifest.json" --glass-run "C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view" --wbpp-result "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json "C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.json" --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --contract-bundle "C:\glass_runs\phase2_s2_gate_211_native_result_contract\guardrails\acceptance_contract_bundle.json" --out runs\checkpoints\s2_gate_213_acceptance_real_native_release_provenance.json --markdown runs\checkpoints\s2_gate_213_acceptance_real_native_release_provenance.md --min-active-frames 190`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_213_doctor.json`
- `.\.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_213_acceptance_real_native_release_provenance.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_197_github_release_plan_publish_script.json --out runs\checkpoints\s2_gate_213_phase2_status.json --markdown runs\checkpoints\s2_gate_213_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_212_phase2_status.json --candidate-status runs\checkpoints\s2_gate_213_phase2_status.json --out runs\checkpoints\s2_gate_213_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_213_phase2_status_compare.md --fail-on-regression`
- `.\.venv\Scripts\glass.exe windows-github-release-plan --manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --tag v0.1.0-phase2-gate213 --title "GLASS Phase 2 Gate 213 Windows packages" --out runs\checkpoints\s2_gate_213_github_release_plan.json --markdown runs\checkpoints\s2_gate_213_github_release_plan.md --notes runs\checkpoints\s2_gate_213_release_notes.md --script runs\checkpoints\s2_gate_213_publish_release.ps1 --phase2-status runs\checkpoints\s2_gate_213_phase2_status.json --phase2-status-compare runs\checkpoints\s2_gate_213_phase2_status_compare.json --require-same-source-stamp --fail-on-failure`

## Test Results

- Focused pytest: 41 passed in 1.10 s.
- Full pytest: 500 passed in 26.94 s.
- Ruff: all checks passed.
- Real acceptance audit: passed, speedup vs WBPP 58.099101701945926x.
- Phase 2 status: green, latest gate 213.
- Phase 2 status compare: passed, baseline gate 212, candidate gate 213.
- Windows GitHub release plan: release_plan_ready, publication_ready true.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_213_acceptance_real_native_release_provenance.json`
- `runs/checkpoints/s2_gate_213_acceptance_real_native_release_provenance.md`
- `runs/checkpoints/s2_gate_213_doctor.json`
- `runs/checkpoints/s2_gate_213_phase2_status.json`
- `runs/checkpoints/s2_gate_213_phase2_status.md`
- `runs/checkpoints/s2_gate_213_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_213_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_213_github_release_plan.json`
- `runs/checkpoints/s2_gate_213_github_release_plan.md`
- `runs/checkpoints/s2_gate_213_release_notes.md`
- `runs/checkpoints/s2_gate_213_publish_release.ps1`

## Known Limitations

- This gate is reporting/release-handoff only. It does not change image processing algorithms or runtime performance.
- Windows release notes surface native provenance only when a Phase 2 status artifact includes native guardrails-bundle evidence.

## Next Step

- Continue Phase 2 hardening with the next gate that consumes release-ready native bundle provenance in broader handoff or publication automation.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-generated artifacts and user-generated black-box comparison metadata only; it does not read or derive implementation details from proprietary PixInsight/WBPP/PJSR source code.
