# S2 Gate 384 Status

## Gate

S2-Gate 384: Release Promotion Decision Final Evidence Guard

## Completed

- Extended `glass release-promotion-decision` to consume Gate383 StackEngine publication-audit final release-quality evidence.
- Added release-decision checks for raw and Phase2 final evidence presence, readiness, and cross-artifact match.
- Preserved legacy compatibility when final evidence is absent on both raw and Phase2 publication-audit layers.
- Preserved compatible-missing semantics for layers that explicitly report `final_checks_ready=true`, `final_checks_match=true`, and missing raw/Phase2 final-check detail.
- Blocked release-candidate/default-change readiness when raw final evidence fails, Phase2 final evidence fails, or Phase2 loses final evidence carried by raw publication-audit.
- Surfaced final evidence readiness, match status, raw fields, and Phase2 fields in release-promotion JSON and Markdown.
- Added focused tests for green evidence surfacing, compatible-missing final evidence, legacy absent final evidence, failed raw evidence, failed Phase2 evidence, and Phase2 evidence loss.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and registered the clean-room artifact policy in `docs/algorithm_sources.md`.
- Generated reproducible Gate384 decision fixtures under `runs/checkpoints/s2_gate_384_fixtures/`.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\release_promotion_decision.py tests\test_release_promotion_decision.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_release_promotion_decision.py`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_384_cuda_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused release-promotion decision tests: `35 passed in 0.39s`
- Full suite: `901 passed in 36.01s`
- Ruff: passed

## CUDA

- CUDA available: yes
- Native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor artifact: `runs/checkpoints/s2_gate_384_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_384_fixtures/ready/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_384_fixtures/compatible_missing_final_evidence/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_384_fixtures/legacy_absent_final_evidence/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_384_fixtures/failed_raw_final_evidence/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_384_fixtures/failed_phase2_final_evidence/release_promotion_decision.json`
- `runs/checkpoints/s2_gate_384_fixtures/lost_phase2_final_evidence/release_promotion_decision.json`

## Known Limitations

- This gate is a release-decision artifact handoff guard only.
- It does not change calibration, star detection, registration, local normalization, integration, rejection, CUDA kernels, runtime defaults, package artifacts, or real-data benchmark results.
- It does not create a GitHub release or upload packages.

## Next Step

- S2-Gate 385 should carry Gate384 release-promotion final-evidence readiness into the default-promotion manifest, so the final default-promotion package/release chain cannot drop the evidence before Windows matrix/preflight publication.

## Clean-Room Compliance

- Compliant. This gate consumes only GLASS-owned JSON/Markdown artifacts and test fixtures.
- No PixInsight/WBPP/PJSR source code, proprietary implementation detail, external package contents, user image pixels, or benchmark reference outputs were read or used.
- Input image directories were not modified.
