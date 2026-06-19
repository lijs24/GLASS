# S2-Gate 386 Status: Windows Release Matrix Final Evidence Guard

## Gate

- S2-Gate 386
- Scope: carry Gate385 final release-quality evidence into `glass windows-release-matrix`.

## Completed

- Added Windows release-matrix support for release-quality final-evidence fields.
- Preserved legacy-compatible behavior when both release-decision and default-promotion artifacts omit final-evidence fields.
- Added hard blocking for direct final-evidence failure/loss and default-promotion final-evidence failure/loss.
- Surfaced final-evidence readiness/match/raw/Phase2 values in JSON evidence and Markdown summaries.
- Added controlled checkpoint fixtures for ready, compatible-missing, legacy-absent, direct-failure, direct-loss, default-promotion-failure, and default-promotion-loss cases.
- Updated Phase 2 planning docs and algorithm-source audit notes.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\windows_release_matrix.py tests\test_windows_release_matrix.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_windows_release_matrix.py`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_386_cuda_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused release-matrix tests: `48 passed in 0.68s`
- Full test suite: `913 passed in 36.37s`
- Ruff: `All checks passed`

## CUDA

- CUDA available: yes
- Native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor artifact: `runs/checkpoints/s2_gate_386_cuda_doctor.json`

## Artifacts

- Fixture summary: `runs/checkpoints/s2_gate_386_fixtures/s2_gate_386_fixture_summary.json`
- Fixture matrix artifacts under `runs/checkpoints/s2_gate_386_fixtures/`
- Checkpoint: `runs/checkpoints/s2_gate_386_status.md`

## Known Limitations

- This gate is a release-matrix guard only. It does not change image math, registration, local normalization, integration, CUDA kernels, runtime defaults, package builds, GitHub release creation, or real-data benchmark output.
- Final-evidence fields remain optional for legacy artifacts only when both sides omit them; once present, raw and Phase2 evidence must be ready and matching.

## Next Step

- S2-Gate 387 should carry this Windows release-matrix final-evidence guard into the next publication handoff layer, likely Windows publish preflight, so final local release checks cannot lose it.

## Clean-Room Compliance

- Compliant. This gate consumes GLASS-owned JSON artifacts only and does not read external implementation source, proprietary code, PixInsight/WBPP source, or user image directories.
