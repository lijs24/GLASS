# S2-Gate 309 Status: Release Decision Direct Runtime Publication Guard

## Gate

- S2-Gate 309
- Scope: release-promotion-decision direct runtime publication guard
- Status: green
- Date: 2026-06-18

## Completed Work

- Added a release-blocking
  `stack_engine_publication_direct_runtime_evidence_passed` check whenever
  `release-promotion-decision --stack-engine-publication-audit` is supplied.
- Preserved the existing StackEngine publication runtime-default guard as a
  separate check.
- Added direct runtime publication evidence parsing for raw publish-preflight
  and Phase2 publish-preflight layers from the Gate308
  `stack-engine-publication-audit` artifact.
- Required direct evidence to prove explicit resident-artifacts acceptance
  fastpath provenance, resident-artifacts calibration fallback provenance,
  passing matrix/default-promotion leaf checks, matching raw/Phase2 evidence,
  and at least 200 resident calibrated lights.
- Surfaced direct runtime readiness, source provenance, check counts, resident
  light counts, and stale source/count blockers in release-decision JSON and
  Markdown.
- Added focused tests for passing direct runtime evidence, missing direct
  evidence, stale direct acceptance source, and insufficient resident light
  counts.
- Updated `docs/phase2_algorithm_hardening.md` with the S2-Gate 309 plan.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py`
- `.venv\Scripts\python.exe -m pytest tests\test_release_promotion_decision.py -q`
- `.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --runtime-compare runs\checkpoints\s2_gate_218_runtime_compare.json --stack-engine-publication-audit runs\checkpoints\s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.json --out runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --markdown runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.md --fail-on-not-ready`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check src tests`
- `git diff --check`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_309_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.json --github-release-plan runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.json --publish-preflight runs\checkpoints\s2_gate_307_windows_publish_preflight_direct_runtime_evidence.json --stack-engine-publication-audit runs\checkpoints\s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --out runs\checkpoints\s2_gate_309_phase2_status_direct_runtime_publication_guard.json --markdown runs\checkpoints\s2_gate_309_phase2_status_direct_runtime_publication_guard.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli phase2-status-compare --baseline-status runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_handoff.json --candidate-status runs\checkpoints\s2_gate_309_phase2_status_direct_runtime_publication_guard.json --out runs\checkpoints\s2_gate_309_phase2_status_direct_runtime_publication_guard_compare.json --markdown runs\checkpoints\s2_gate_309_phase2_status_direct_runtime_publication_guard_compare.md --fail-on-regression`

## Results

- Focused release-decision tests: 17 passed.
- Full pytest: 720 passed.
- Ruff: passed.
- `git diff --check`: passed.
- Gate309 release decision: `default_change_ready`, `passed=true`,
  `default_change_ready=true`.
- Gate309 Phase2 status: `green`, latest checkpoint `S2-Gate 309`, latest
  checkpoint status `green`.
- Gate309 Phase2 status compare: `passed`, baseline gate 308, candidate gate
  309.
- Direct runtime publication guard:
  `stack_engine_publication_direct_runtime_evidence_passed=true`.
- Real 200-light direct evidence preserved:
  - acceptance source: `explicit_resident_artifacts_json`
  - calibration source: `resident_artifacts_json_fallback`
  - resident calibrated lights: 200
  - raw and Phase2 source/count checks: true

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_309_release_decision_direct_runtime_publication_guard.json`
- `runs/checkpoints/s2_gate_309_release_decision_direct_runtime_publication_guard.md`
- `runs/checkpoints/s2_gate_309_phase2_status_direct_runtime_publication_guard.json`
- `runs/checkpoints/s2_gate_309_phase2_status_direct_runtime_publication_guard.md`
- `runs/checkpoints/s2_gate_309_phase2_status_direct_runtime_publication_guard_compare.json`
- `runs/checkpoints/s2_gate_309_phase2_status_direct_runtime_publication_guard_compare.md`
- `runs/checkpoints/s2_gate_309_doctor.json`
- `runs/checkpoints/s2_gate_309_status.md`

## Known Limitations

- This gate is release-decision/status evidence wiring only. It does not change
  image math, CUDA kernels, package contents, runtime defaults, GitHub release
  publication, or benchmark outputs.
- The real 200-light evidence is reused from the existing Gate304-Gate308
  artifact chain; no new long real-data benchmark was run in this gate.
- The new check is enabled only when a StackEngine publication-audit artifact is
  supplied, preserving older release-decision workflows that do not yet opt into
  publication handoff validation.

## Next Step

- Carry the Gate309 release-decision direct runtime publication guard into
  default-promotion and Windows release matrix evidence, so publication
  artifacts can reject release decisions that omit the Gate308 direct runtime
  chain.

## Clean-Room Compliance

- This gate consumed only GLASS-owned status, acceptance, pipeline-contract,
  StackEngine contract, release-decision, and generated publication-audit
  artifacts.
- No PixInsight/WBPP/PJSR implementation source, proprietary scripts, or
  external implementation code were read, summarized, copied, or modified.
