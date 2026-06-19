# S2-Gate 391 Status: Default-Promotion Final Evidence Detail Handoff

## Gate
- S2-Gate 391
- Status: green
- Date: 2026-06-19

## Completed
- Carried release-promotion `final_evidence_*` release-quality detail into `glass default-promotion-manifest`.
- Preserved legacy `final_checks_*` compatibility for older release-decision artifacts.
- Blocked default-promotion readiness when release-decision detail evidence fails.
- Blocked default-promotion readiness when Phase2-side detail fields are dropped while raw release-decision detail remains present.
- Surfaced final-evidence-detail readiness and representative raw/Phase2 matrix detail values in default-promotion JSON and Markdown.
- Added focused regression tests for ready detail, compatible-missing detail, legacy-only compatibility, failed raw detail, failed Phase2 detail, and Phase2 detail loss.
- Added checkpoint fixtures under `runs/checkpoints/s2_gate_391_fixtures/`.

## Commands Run
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\default_promotion_manifest.py tests\test_default_promotion_manifest.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_default_promotion_manifest.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_391_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results
- Ruff: passed.
- Focused default-promotion tests: `43 passed in 0.74s`.
- Full pytest: `932 passed in 37.38s`.

## CUDA
- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_391_cuda_doctor.json`.

## Artifacts
- `runs/checkpoints/s2_gate_391_fixtures/fixture_summary.json`
- `runs/checkpoints/s2_gate_391_fixtures/ready_final_evidence_detail/default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_391_fixtures/ready_final_evidence_detail/default_promotion_manifest.md`
- `runs/checkpoints/s2_gate_391_fixtures/legacy_only_final_checks/default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_391_fixtures/legacy_only_final_checks/default_promotion_manifest.md`
- `runs/checkpoints/s2_gate_391_fixtures/failed_raw_matrix_phase2_final_evidence_detail/default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_391_fixtures/failed_raw_matrix_phase2_final_evidence_detail/default_promotion_manifest.md`
- `runs/checkpoints/s2_gate_391_fixtures/phase2_final_evidence_detail_loss/default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_391_fixtures/phase2_final_evidence_detail_loss/default_promotion_manifest.md`

## Known Limitations
- This gate is a default-promotion evidence handoff only.
- It does not change image math, star detection, registration, integration, CUDA kernels, packaging, or benchmark outputs.
- Older release-decision artifacts without `final_evidence_*` detail remain accepted when their legacy final-evidence/final-check evidence is otherwise passing.

## Next Step
- S2-Gate 392 should carry default-promotion final-evidence detail into `glass windows-release-matrix` and guard against detail loss between direct release-decision evidence and the promoted manifest.

## Clean-Room Compliance
- This gate consumes only GLASS-owned release-decision, Phase2 status, doctor, and test fixture JSON artifacts.
- It does not read image pixels, user image directories, external implementation source, proprietary behavior, package contents, GitHub releases, or benchmark reference outputs.
