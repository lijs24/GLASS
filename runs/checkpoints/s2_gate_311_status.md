# S2-Gate 311 Status: Windows Publish Preflight Direct Publication Guard

## Gate

- S2-Gate 311
- Scope: Windows GitHub handoff and publish-preflight direct publication guard
- Status: green
- Date: 2026-06-18

## Completed Work

- Carried the Gate310 release-decision direct runtime publication guard into
  `windows-github-release-plan`.
- Added GitHub handoff blocking checks:
  - `windows_release_matrix_release_decision_direct_runtime_publication_guard_passed`
  - `windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed`
- Carried the same guard into `windows-publish-preflight`.
- Added publish-preflight checks for the GitHub plan, Windows release matrix,
  matrix-embedded default promotion summary, and standalone default-promotion
  manifest.
- Added drift checks so release plan, release matrix, and default-promotion
  artifacts cannot disagree while still reporting ready status.
- Extended GitHub release Markdown, release notes, publish-preflight Markdown,
  and the generated PowerShell dry-run script with direct publication guard
  evidence.
- Updated `docs/phase2_algorithm_hardening.md` with S2-Gate 311.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_windows_github_release_plan.py tests\test_windows_publish_preflight.py`
- `.venv\Scripts\ruff.exe check src\glass\report\windows_github_release_plan.py src\glass\report\windows_publish_preflight.py tests\test_windows_github_release_plan.py tests\test_windows_publish_preflight.py`
- `.venv\Scripts\python.exe -m glass.cli windows-release-manifest --suite runs\checkpoints\s2_gate_194_strict_windows_package_suite.json --windows-release-matrix runs\checkpoints\s2_gate_310_windows_release_matrix_direct_publication_guard.json --require-same-source-stamp --out runs\checkpoints\s2_gate_311_windows_release_manifest_direct_publication_guard.json --markdown runs\checkpoints\s2_gate_311_windows_release_manifest_direct_publication_guard.md --fail-on-failure`
- `.venv\Scripts\python.exe -m glass.cli windows-github-release-plan --manifest runs\checkpoints\s2_gate_311_windows_release_manifest_direct_publication_guard.json --tag v0.1.0-gate311-preflight --title "GLASS Windows Gate311 Preflight" --out runs\checkpoints\s2_gate_311_github_release_plan_direct_publication_guard.json --markdown runs\checkpoints\s2_gate_311_github_release_plan_direct_publication_guard.md --notes runs\checkpoints\s2_gate_311_github_release_notes_direct_publication_guard.md --script runs\checkpoints\s2_gate_311_publish_release_direct_publication_guard.ps1 --phase2-status runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_handoff.json --phase2-status-compare runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_compare.json --windows-release-matrix runs\checkpoints\s2_gate_310_windows_release_matrix_direct_publication_guard.json --require-same-source-stamp --fail-on-failure`
- `.venv\Scripts\python.exe -m glass.cli windows-publish-preflight --release-manifest runs\checkpoints\s2_gate_311_windows_release_manifest_direct_publication_guard.json --github-release-plan runs\checkpoints\s2_gate_311_github_release_plan_direct_publication_guard.json --windows-release-matrix runs\checkpoints\s2_gate_310_windows_release_matrix_direct_publication_guard.json --default-promotion-manifest runs\checkpoints\s2_gate_310_default_promotion_direct_publication_guard.json --out runs\checkpoints\s2_gate_311_windows_publish_preflight_direct_publication_guard.json --markdown runs\checkpoints\s2_gate_311_windows_publish_preflight_direct_publication_guard.md --fail-on-failure`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check src tests`
- `git diff --check`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_311_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\checkpoints\s2_gate_311_windows_release_manifest_direct_publication_guard.json --github-release-plan runs\checkpoints\s2_gate_311_github_release_plan_direct_publication_guard.json --publish-preflight runs\checkpoints\s2_gate_311_windows_publish_preflight_direct_publication_guard.json --stack-engine-publication-audit runs\checkpoints\s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --out runs\checkpoints\s2_gate_311_phase2_status_direct_publication_guard_handoff.json --markdown runs\checkpoints\s2_gate_311_phase2_status_direct_publication_guard_handoff.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli phase2-status-compare --baseline-status runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_handoff.json --candidate-status runs\checkpoints\s2_gate_311_phase2_status_direct_publication_guard_handoff.json --out runs\checkpoints\s2_gate_311_phase2_status_direct_publication_guard_compare.json --markdown runs\checkpoints\s2_gate_311_phase2_status_direct_publication_guard_compare.md --fail-on-regression`

## Results

- Focused GitHub release-plan/publish-preflight tests: 47 passed.
- Full pytest: 731 passed.
- Ruff: passed.
- `git diff --check`: passed.
- Gate311 Windows release manifest: `release_manifest_ready`, `passed=true`,
  package count 4.
- Gate311 GitHub release plan: `release_plan_ready`, `publication_ready=true`,
  package count 4.
- Gate311 publish preflight: `publish_preflight_ready`, `passed=true`.
- Gate311 Phase2 status: `green`, latest checkpoint `S2-Gate 311`, latest
  checkpoint status `green`.
- Gate311 Phase2 status compare: `passed`, baseline gate 310, candidate gate
  311.
- Direct publication guard checks in publish preflight:
  - GitHub plan matrix guard: true.
  - GitHub plan matrix default-promotion guard: true.
  - Matrix release-decision guard: true.
  - Matrix embedded default-promotion guard: true.
  - Standalone default-promotion guard: true.
  - Matrix/default-promotion drift checks: true.
- Real 200-light direct evidence preserved:
  - acceptance source: `explicit_resident_artifacts_json`
  - calibration source: `resident_artifacts_json_fallback`
  - resident calibrated lights: 200

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_311_doctor.json`
- `runs/checkpoints/s2_gate_311_windows_release_manifest_direct_publication_guard.json`
- `runs/checkpoints/s2_gate_311_windows_release_manifest_direct_publication_guard.md`
- `runs/checkpoints/s2_gate_311_github_release_plan_direct_publication_guard.json`
- `runs/checkpoints/s2_gate_311_github_release_plan_direct_publication_guard.md`
- `runs/checkpoints/s2_gate_311_github_release_notes_direct_publication_guard.md`
- `runs/checkpoints/s2_gate_311_publish_release_direct_publication_guard.ps1`
- `runs/checkpoints/s2_gate_311_windows_publish_preflight_direct_publication_guard.json`
- `runs/checkpoints/s2_gate_311_windows_publish_preflight_direct_publication_guard.md`
- `runs/checkpoints/s2_gate_311_phase2_status_direct_publication_guard_handoff.json`
- `runs/checkpoints/s2_gate_311_phase2_status_direct_publication_guard_handoff.md`
- `runs/checkpoints/s2_gate_311_phase2_status_direct_publication_guard_compare.json`
- `runs/checkpoints/s2_gate_311_phase2_status_direct_publication_guard_compare.md`
- `runs/checkpoints/s2_gate_311_status.md`

## Known Limitations

- This gate is final publication handoff evidence wiring only.
- It does not change image math, CUDA kernels, runtime defaults, package
  contents, package build/upload, GitHub release creation, or benchmark outputs.
- The real 200-light evidence is reused from the existing Gate304-Gate310
  artifact chain; no new long real-data benchmark was run in this gate.

## Next Step

- Feed Gate311 publish-preflight evidence back into Phase2 status and compare
  against Gate310, then continue with the next algorithm hardening gate.

## Clean-Room Compliance

- This gate consumed only GLASS-owned release manifest, GitHub handoff,
  publish-preflight, release matrix, default-promotion, doctor, and generated
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR implementation source, proprietary scripts, or
  external implementation code were read, summarized, copied, or modified.
