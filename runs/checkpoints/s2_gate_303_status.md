# S2-Gate 303 Status: Release/Default Promotion Resident Winsorized Visibility

## Gate

- Gate: S2-Gate 303
- Status: Green
- Scope: release/default-promotion visibility for resident winsorized semantics
- Date: 2026-06-18

## Completed

- Added release-promotion evidence for resident winsorized result-contract
  semantics from the pipeline contract.
- Added release blocker
  `pipeline_resident_winsorized_semantics_handoff` for failed required
  resident winsorized semantics.
- Preserved descriptor source, resident-artifact backfill visibility, legacy
  completion count, resident mode, algorithm, scale estimator, parity status,
  and approximation fields in release JSON/Markdown.
- Copied the release resident winsorized summary into the default-promotion
  manifest JSON/Markdown.
- Documented S2-Gate 303 in `docs/phase2_algorithm_hardening.md`.
- Generated Gate303 handoff artifacts from existing checkpoint evidence:
  - `runs/checkpoints/s2_gate_303_acceptance_runtime_default_fastpath_handoff.json`
  - `runs/checkpoints/s2_gate_303_pipeline_contract_resident_winsorized_visibility_handoff.json`
  - `runs/checkpoints/s2_gate_303_release_decision_resident_winsorized_visibility.json`
  - `runs/checkpoints/s2_gate_303_release_decision_resident_winsorized_visibility.md`
  - `runs/checkpoints/s2_gate_303_phase2_status_resident_winsorized_visibility.json`
  - `runs/checkpoints/s2_gate_303_phase2_status_resident_winsorized_visibility.md`
  - `runs/checkpoints/s2_gate_303_default_promotion_resident_winsorized_visibility.json`
  - `runs/checkpoints/s2_gate_303_default_promotion_resident_winsorized_visibility.md`
  - `runs/checkpoints/s2_gate_303_doctor.json`

## Handoff Sources

- Acceptance handoff uses Gate294 runtime-default acceptance evidence plus the
  Gate214 resident registration fastpath raw contract checks.
- Pipeline handoff uses Gate302 resident winsorized semantics plus resident
  calibration visibility fields from Gate295 default-promotion evidence.
- These handoff files are checkpoint-evidence merge artifacts only; they do not
  modify image outputs or algorithm results.

## Commands

- `.venv\Scripts\python.exe -m glass.cli release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_294_acceptance_runtime_default_ready.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_303_pipeline_contract_resident_winsorized_visibility_handoff.json --runtime-compare runs\checkpoints\s2_gate_218_runtime_compare.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --out runs\checkpoints\s2_gate_303_release_decision_resident_winsorized_visibility.json --markdown runs\checkpoints\s2_gate_303_release_decision_resident_winsorized_visibility.md --fail-on-not-ready`
- `.venv\Scripts\python.exe -m glass.cli phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_303_acceptance_runtime_default_fastpath_handoff.json --default-route-acceptance-audit runs\checkpoints\s2_gate_222_default_route_acceptance_audit.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_303_pipeline_contract_resident_winsorized_visibility_handoff.json --resident-winsorized-sweep-audit runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --stack-engine-publication-audit runs\checkpoints\s2_gate_299_stack_engine_publication_runtime_default.json --release-decision runs\checkpoints\s2_gate_303_release_decision_resident_winsorized_visibility.json --out runs\checkpoints\s2_gate_303_phase2_status_resident_winsorized_visibility.json --markdown runs\checkpoints\s2_gate_303_phase2_status_resident_winsorized_visibility.md --fail-on-not-green`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_303_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli default-promotion-manifest --release-decision runs\checkpoints\s2_gate_303_release_decision_resident_winsorized_visibility.json --phase2-status runs\checkpoints\s2_gate_303_phase2_status_resident_winsorized_visibility.json --doctor-json runs\checkpoints\s2_gate_303_doctor.json --require-doctor --out runs\checkpoints\s2_gate_303_default_promotion_resident_winsorized_visibility.json --markdown runs\checkpoints\s2_gate_303_default_promotion_resident_winsorized_visibility.md --fail-on-not-ready`
- `.venv\Scripts\ruff.exe check src\glass\report\release_promotion_decision.py src\glass\report\default_promotion_manifest.py tests\test_release_promotion_decision.py tests\test_default_promotion_manifest.py`
- `.venv\Scripts\python.exe -m pytest tests\test_release_promotion_decision.py tests\test_default_promotion_manifest.py -q`
- `git diff --check`
- `.venv\Scripts\python.exe -m pytest -q`

## Results

- Release decision: `default_change_ready`
- Phase2 status: `green`
- Default-promotion manifest: `default_promotion_ready`
- Targeted tests: 32 passed in 0.40 s
- Full tests: 704 passed in 29.88 s
- `git diff --check`: passed, with expected Windows line-ending warnings only

## CUDA

- CUDA wrapper importable: true
- CUDA native extension loaded: true
- CUDA available: true
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Windows package try order: cuda13, cuda12, cuda11, cpu

## Known Limitations

- This gate is audit/report visibility only; it does not change image math,
  CUDA kernels, runtime defaults, package builds, or GitHub releases.
- Sparse historical pipeline fixtures with no resident winsorized semantics are
  treated as `not_available` and remain compatible. Required resident
  winsorized semantics still block release if they fail.
- The Gate303 handoff artifacts merge previously green checkpoint evidence for
  publication visibility. They are not a fresh real-data benchmark rerun.

## Next Step

- Continue Phase 2 with the next gate that reduces reliance on handoff bundles
  by making the latest full pipeline contract emit all release/default-promotion
  evidence directly.

## Clean-Room Compliance

- No PixInsight or WBPP source code was read, copied, summarized, or modified.
- No input image directories were modified.
- No closed-source executable or hidden algorithm path was introduced.
