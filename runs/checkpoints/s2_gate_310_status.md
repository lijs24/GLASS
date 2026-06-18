# S2-Gate 310 Status: Default Promotion Direct Publication Guard Handoff

## Gate

- S2-Gate 310
- Scope: default-promotion and Windows release-matrix direct publication guard
- Status: green
- Date: 2026-06-18

## Completed Work

- Carried the S2-Gate 309 release-decision direct runtime publication guard
  into `default-promotion-manifest`.
- Added a default-promotion blocking check:
  `release_decision_direct_runtime_publication_guard_passed`.
- Preserved direct runtime publication provenance in default-promotion JSON and
  Markdown: explicit resident-artifacts acceptance source, resident-artifacts
  calibration fallback source, raw/Phase2 source and count readiness, leaf-check
  readiness, and 200 resident calibrated lights.
- Extended `windows-release-matrix` with:
  - `release_decision_direct_runtime_publication_guard_passed`
  - `default_promotion_release_decision_direct_runtime_publication_guard_passed`
- Added focused tests for passing handoff, missing release-decision guard,
  missing default-promotion guard, stale source provenance, and insufficient
  resident light counts.
- Updated `docs/phase2_algorithm_hardening.md` with S2-Gate 310.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\default_promotion_manifest.py src\glass\report\windows_release_matrix.py tests\test_default_promotion_manifest.py tests\test_windows_release_matrix.py`
- `.venv\Scripts\python.exe -m pytest tests\test_default_promotion_manifest.py tests\test_windows_release_matrix.py -q`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_310_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --phase2-status runs\checkpoints\s2_gate_309_phase2_status_direct_runtime_publication_guard.json --doctor-json runs\checkpoints\s2_gate_310_doctor.json --require-doctor --min-runtime-runs 2 --out runs\checkpoints\s2_gate_310_default_promotion_direct_publication_guard.json --markdown runs\checkpoints\s2_gate_310_default_promotion_direct_publication_guard.md --fail-on-not-ready`
- `.venv\Scripts\python.exe -m glass.cli windows-release-matrix --doctor-json runs\checkpoints\s2_gate_310_doctor.json --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-promotion-manifest runs\checkpoints\s2_gate_310_default_promotion_direct_publication_guard.json --expected-primary-package cuda13 --out runs\checkpoints\s2_gate_310_windows_release_matrix_direct_publication_guard.json --markdown runs\checkpoints\s2_gate_310_windows_release_matrix_direct_publication_guard.md`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check src tests`
- `git diff --check`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.json --github-release-plan runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.json --publish-preflight runs\checkpoints\s2_gate_307_windows_publish_preflight_direct_runtime_evidence.json --stack-engine-publication-audit runs\checkpoints\s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --release-decision runs\checkpoints\s2_gate_309_release_decision_direct_runtime_publication_guard.json --out runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_handoff.json --markdown runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_handoff.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli phase2-status-compare --baseline-status runs\checkpoints\s2_gate_309_phase2_status_direct_runtime_publication_guard.json --candidate-status runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_handoff.json --out runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_compare.json --markdown runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_compare.md --fail-on-regression`

## Results

- Focused default-promotion/release-matrix tests: 46 passed.
- Full pytest: 726 passed.
- Ruff: passed.
- `git diff --check`: passed.
- Gate310 default-promotion manifest: `default_promotion_ready`, `passed=true`.
- Gate310 Windows release matrix: `release_matrix_ready`, `passed=true`,
  primary package `cuda13`.
- Gate310 Phase2 status: `green`, latest checkpoint `S2-Gate 310`, latest
  checkpoint status `green`.
- Gate310 Phase2 status compare: `passed`, baseline gate 309, candidate gate
  310.
- Release-decision direct guard in matrix:
  `release_decision_direct_runtime_publication_guard_passed=true`.
- Default-promotion preserved guard in matrix:
  `default_promotion_release_decision_direct_runtime_publication_guard_passed=true`.
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

- `runs/checkpoints/s2_gate_310_doctor.json`
- `runs/checkpoints/s2_gate_310_default_promotion_direct_publication_guard.json`
- `runs/checkpoints/s2_gate_310_default_promotion_direct_publication_guard.md`
- `runs/checkpoints/s2_gate_310_windows_release_matrix_direct_publication_guard.json`
- `runs/checkpoints/s2_gate_310_windows_release_matrix_direct_publication_guard.md`
- `runs/checkpoints/s2_gate_310_phase2_status_direct_publication_guard_handoff.json`
- `runs/checkpoints/s2_gate_310_phase2_status_direct_publication_guard_handoff.md`
- `runs/checkpoints/s2_gate_310_phase2_status_direct_publication_guard_compare.json`
- `runs/checkpoints/s2_gate_310_phase2_status_direct_publication_guard_compare.md`
- `runs/checkpoints/s2_gate_310_status.md`

## Known Limitations

- This gate is default-promotion/release-matrix/status evidence wiring only. It
  does not change image math, CUDA kernels, package contents, runtime defaults,
  GitHub release publication, or benchmark outputs.
- The real 200-light evidence is reused from the existing Gate304-Gate309
  artifact chain; no new long real-data benchmark was run in this gate.
- The new release-matrix checks remain tied to strict publication readiness
  paths; diagnostic old-artifact review can still use existing escape hatches
  where supported by the relevant command.

## Next Step

- Carry the Gate310 direct publication guard through the final
  windows-publish-preflight and GitHub handoff artifacts, so publication bundles
  cannot be assembled from a release matrix that lost the Gate309/Gate310
  evidence.

## Clean-Room Compliance

- This gate consumed only GLASS-owned release-decision, Phase2 status,
  default-promotion, Windows release-matrix, doctor, and generated checkpoint
  artifacts.
- No PixInsight/WBPP/PJSR implementation source, proprietary scripts, or
  external implementation code were read, summarized, copied, or modified.
