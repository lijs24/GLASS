# S2-Gate 390 Status: Release-Promotion Final Evidence Detail Handoff

## Gate
- S2-Gate 390
- Status: green
- Date: 2026-06-19

## Completed
- Carried StackEngine publication-audit `final_evidence_*` release-quality detail into `glass release-promotion-decision`.
- Preserved legacy `final_checks_*` compatibility for older publication-audit artifacts.
- Blocked failed raw/Phase2 final-evidence detail and Phase2 loss of detail fields.
- Surfaced raw and Phase2 final-evidence detail in release-promotion JSON evidence and Markdown output.
- Added focused regression tests for ready detail, legacy-only compatibility, failed raw detail, and Phase2 detail loss.
- Added checkpoint fixtures under `runs/checkpoints/s2_gate_390_fixtures/`.

## Commands Run
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_390_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results
- Ruff: passed.
- Focused release-promotion tests: `38 passed in 0.44s`.
- Full pytest: `929 passed in 37.01s`.

## CUDA
- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_390_cuda_doctor.json`.

## Artifacts
- `runs/checkpoints/s2_gate_390_fixtures/fixture_summary.json`
- `runs/checkpoints/s2_gate_390_fixtures/ready_final_evidence_detail/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_390_fixtures/ready_final_evidence_detail/release_promotion_decision.md`
- `runs/checkpoints/s2_gate_390_fixtures/legacy_only_final_checks/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_390_fixtures/legacy_only_final_checks/release_promotion_decision.md`
- `runs/checkpoints/s2_gate_390_fixtures/failed_raw_matrix_phase2_final_evidence_detail/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_390_fixtures/failed_raw_matrix_phase2_final_evidence_detail/release_promotion_decision.md`
- `runs/checkpoints/s2_gate_390_fixtures/phase2_final_evidence_detail_loss/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_390_fixtures/phase2_final_evidence_detail_loss/release_promotion_decision.md`

## Known Limitations
- This gate is a release-decision evidence handoff only.
- It does not change image math, star detection, registration, integration, CUDA kernels, packaging, or benchmark outputs.
- Legacy publication-audit artifacts without `final_evidence_*` detail remain accepted when their legacy `final_checks_*` evidence is complete and passing.

## Next Step
- S2-Gate 391 should continue tightening the publication/release evidence chain, preferably around default-promotion or packaged-release evidence loss that is still only indirectly guarded.

## Clean-Room Compliance
- This gate consumes only GLASS-owned JSON artifacts and test fixtures.
- It does not read image pixels, user image directories, external implementation source, proprietary behavior, package contents, GitHub releases, or benchmark reference outputs.
