# S2-Gate 308 Status: Phase2 Direct Runtime Publication Handoff

## Gate

- S2-Gate 308
- Scope: Phase2 status and StackEngine publication-audit evidence wiring
- Status: green
- Date: 2026-06-18

## Completed Work

- Carried Gate307 Windows publish-preflight direct runtime evidence into
  `glass phase2-status`.
- Added a strict Phase2 status check requiring direct publish-preflight evidence
  from both the Windows release matrix and default-promotion manifest:
  explicit resident-artifacts acceptance fastpath source, resident-artifacts
  pipeline calibration fallback, at least 200 resident calibrated lights, and
  matching matrix/default-promotion summaries.
- Extended `phase2-status-compare` so publish-preflight direct runtime evidence
  and statuses are preserved across handoff comparisons.
- Extended `stack-engine-publication-audit` so it compares raw publish-preflight
  direct runtime evidence with the Phase2 status summary.
- Surfaced the direct runtime publication chain in JSON and Markdown status
  reports.
- Added focused regression tests for missing direct runtime evidence, stale
  fastpath sources, Phase2 compare regression, and publication-audit mismatch
  cases.

## Commands

- `.venv\Scripts\python.exe -m pytest tests\test_phase2_status.py::test_phase2_status_blocks_missing_publish_preflight_direct_runtime_evidence tests\test_phase2_status.py::test_phase2_status_blocks_stale_publish_preflight_direct_fastpath_source tests\test_phase2_status.py::test_phase2_status_compare_flags_publish_preflight_direct_runtime_regression tests\test_stack_engine_publication_audit.py::test_stack_engine_publication_audit_blocks_missing_publish_preflight_direct_runtime tests\test_stack_engine_publication_audit.py::test_stack_engine_publication_audit_blocks_phase2_direct_runtime_mismatch tests\test_stack_engine_publication_audit.py::test_stack_engine_publication_audit_blocks_missing_phase2_direct_runtime -q`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.json --github-release-plan runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.json --publish-preflight runs\checkpoints\s2_gate_307_windows_publish_preflight_direct_runtime_evidence.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --release-decision runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.json --out runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_handoff_initial.json --markdown runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_handoff_initial.md`
- `.venv\Scripts\python.exe -m glass.cli stack-engine-publication-audit --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --phase2-status runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_handoff_initial.json --default-promotion-manifest runs\checkpoints\s2_gate_306_default_promotion_direct_runtime_evidence.json --windows-release-matrix runs\checkpoints\s2_gate_306_windows_release_matrix_direct_runtime_evidence.json --github-release-plan runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.json --publish-preflight runs\checkpoints\s2_gate_307_windows_publish_preflight_direct_runtime_evidence.json --out runs\checkpoints\s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.json --markdown runs\checkpoints\s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.md --fail-on-failure`
- `.venv\Scripts\ruff.exe check src\glass\report\phase2_status.py src\glass\report\stack_engine_publication_audit.py tests\test_phase2_status.py tests\test_stack_engine_publication_audit.py`
- `.venv\Scripts\python.exe -m pytest tests\test_phase2_status.py tests\test_stack_engine_publication_audit.py -q`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\ruff.exe check src tests`
- `git diff --check`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_308_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_305_acceptance_direct_fastpath_runtime_default.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\checkpoints\s2_gate_307_windows_release_manifest_direct_runtime_evidence.json --github-release-plan runs\checkpoints\s2_gate_307_github_release_plan_direct_runtime_evidence.json --publish-preflight runs\checkpoints\s2_gate_307_windows_publish_preflight_direct_runtime_evidence.json --stack-engine-publication-audit runs\checkpoints\s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --release-decision runs\checkpoints\s2_gate_305_release_decision_direct_acceptance_fastpath.json --out runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_handoff.json --markdown runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_handoff.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli phase2-status-compare --baseline-status runs\checkpoints\s2_gate_305_phase2_status_direct_acceptance_fastpath.json --candidate-status runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_handoff.json --out runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_compare.json --markdown runs\checkpoints\s2_gate_308_phase2_status_direct_runtime_publication_compare.md --fail-on-regression`

## Results

- Focused direct-runtime regression tests: 6 passed.
- Phase2 status/report focused tests: 71 passed.
- Full pytest: 717 passed.
- Ruff: passed.
- `git diff --check`: passed.
- StackEngine publication audit: `passed`, `failed_checks=[]`.
- Final Phase2 status: `green`, latest checkpoint `S2-Gate 308`, latest
  checkpoint status `green`.
- Phase2 status compare: `passed`, baseline gate 304, candidate gate 308.
- Initial Phase2 status: `attention_required` only because Gate307's older
  checkpoint file did not expose a parseable `Status: green` line. Gate308
  status provides that line before final status regeneration.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_308_phase2_status_direct_runtime_publication_handoff_initial.json`
- `runs/checkpoints/s2_gate_308_phase2_status_direct_runtime_publication_handoff_initial.md`
- `runs/checkpoints/s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.json`
- `runs/checkpoints/s2_gate_308_stack_engine_publication_audit_direct_runtime_handoff.md`
- `runs/checkpoints/s2_gate_308_phase2_status_direct_runtime_publication_handoff.json`
- `runs/checkpoints/s2_gate_308_phase2_status_direct_runtime_publication_handoff.md`
- `runs/checkpoints/s2_gate_308_phase2_status_direct_runtime_publication_compare.json`
- `runs/checkpoints/s2_gate_308_phase2_status_direct_runtime_publication_compare.md`
- `runs/checkpoints/s2_gate_308_doctor.json`
- `runs/checkpoints/s2_gate_308_status.md`

## Known Limitations

- This gate is evidence/audit/report wiring only. It does not change image math,
  CUDA kernels, package contents, runtime defaults, GitHub release publication,
  or benchmark outputs.
- The real 200-light evidence is reused from the existing Gate305-Gate307
  artifact chain; no new long real-data benchmark was run in this gate.
- The initial Phase2 status is retained as a diagnostic artifact because it
  demonstrates that the new publish-preflight direct runtime checks passed
  before this Gate308 status file existed.

## Next Step

- Carry the direct runtime publication chain into the next
  default-promotion/release handoff layer if needed, or proceed to the next
  Phase2 hardening gate focused on real runtime/default behavior rather than
  artifact wiring.

## Clean-Room Compliance

- This gate consumed only GLASS-owned status, acceptance, pipeline-contract,
  StackEngine contract, release, package, and generated audit artifacts.
- No PixInsight/WBPP/PJSR implementation source, proprietary scripts, or
  external implementation code were read, summarized, copied, or modified.
