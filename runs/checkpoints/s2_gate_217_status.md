# S2-Gate 217 Status

- Gate: S2-Gate 217
- Scope: Release Promotion Requires Pipeline DQ Handoff
- Status: green
- Date: 2026-06-18

## Completed

- Tightened `glass release-promotion-decision` so a top-level passed pipeline
  contract is no longer sufficient for release-candidate readiness.
- Added release-blocking checks for pipeline invariant contract presence,
  integration DQ contract pass, StackEngine/resident result-contract pass,
  pixel verification enabled, and DQ/coverage/rejection pixel-match checks.
- Normalized pipeline handoff evidence from either an explicit
  `--pipeline-contract` artifact or the pipeline-contract block embedded in an
  acceptance audit.
- Added release-promotion JSON and Markdown output for the normalized pipeline
  DQ handoff evidence.
- Updated focused tests and Phase 2 hardening documentation.

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_release_promotion_decision.py`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_217_doctor.json`
- `.\.venv\Scripts\glass.exe release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_211_pipeline_contract.json --out runs\checkpoints\s2_gate_217_release_promotion_decision.json --markdown runs\checkpoints\s2_gate_217_release_promotion_decision.md --min-speedup 2.0`
- `.\.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --pipeline-contract runs\checkpoints\s2_gate_211_pipeline_contract.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_216_github_release_plan.json --out runs\checkpoints\s2_gate_217_phase2_status.json --markdown runs\checkpoints\s2_gate_217_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_216_phase2_status.json --candidate-status runs\checkpoints\s2_gate_217_phase2_status.json --out runs\checkpoints\s2_gate_217_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_217_phase2_status_compare.md --fail-on-regression`
- `.\.venv\Scripts\glass.exe windows-github-release-plan --manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --tag v0.1.0-phase2-gate217 --title "GLASS Phase 2 Gate 217 Windows packages" --out runs\checkpoints\s2_gate_217_github_release_plan.json --markdown runs\checkpoints\s2_gate_217_github_release_plan.md --notes runs\checkpoints\s2_gate_217_release_notes.md --script runs\checkpoints\s2_gate_217_publish_release.ps1 --phase2-status runs\checkpoints\s2_gate_217_phase2_status.json --phase2-status-compare runs\checkpoints\s2_gate_217_phase2_status_compare.json --require-same-source-stamp --fail-on-failure`

## Test Results

- Focused ruff: passed.
- Focused pytest: 6 passed in 0.20s.
- Full ruff: passed.
- Full pytest: 503 passed in 27.15s.
- Real release-promotion decision: release_candidate_ready.
- Default change ready: false, because stable repeat runtime evidence is still required.
- Phase 2 status: green, latest gate 217.
- Phase 2 status compare: passed, baseline gate 216, candidate gate 217.
- Windows GitHub release plan: release_plan_ready, publication_ready true, 4 assets.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native extension loaded: yes.

## Real Benchmark / Contract Evidence

- Real acceptance evidence source: `runs/checkpoints/s2_gate_214_acceptance_real_fastpath_contract.json`.
- Real stack contract source: `runs/checkpoints/s2_gate_211_stack_engine_contract.json`.
- Real pipeline contract source: `runs/checkpoints/s2_gate_211_pipeline_contract.json`.
- Pipeline DQ handoff source: explicit pipeline contract.
- Pipeline DQ contract: passed.
- Pipeline pixel verification: enabled and passed for DQ, coverage, and rejection maps.

## Artifacts

- `runs/checkpoints/s2_gate_217_doctor.json`
- `runs/checkpoints/s2_gate_217_release_promotion_decision.json`
- `runs/checkpoints/s2_gate_217_release_promotion_decision.md`
- `runs/checkpoints/s2_gate_217_phase2_status.json`
- `runs/checkpoints/s2_gate_217_phase2_status.md`
- `runs/checkpoints/s2_gate_217_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_217_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_217_github_release_plan.json`
- `runs/checkpoints/s2_gate_217_github_release_plan.md`
- `runs/checkpoints/s2_gate_217_release_notes.md`
- `runs/checkpoints/s2_gate_217_publish_release.ps1`

## Known Limitations

- This gate is contract/reporting hardening only; it does not change
  calibration, registration, integration, DQ generation, or CUDA kernels.
- The real 200-light run was not reprocessed in this gate; the gate consumes
  existing green acceptance, StackEngine, and pipeline-contract artifacts.
- Default-change readiness remains false until a stable repeat runtime compare
  artifact is supplied.

## Next Step

- Produce or consume stable repeated runtime evidence so default-promotion
  gates can move from release-candidate-ready to default-change-ready.

## Clean-Room

- Compliant. No PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
