# S2-Gate 387 Status: Windows Publish Preflight Final Evidence Guard

## Gate

- S2-Gate 387
- Scope: carry Gate386 Windows release-matrix final release-quality evidence into `glass windows-publish-preflight`.

## Completed

- Added publish-preflight extraction for release-quality final-evidence fields from the Windows release matrix and standalone default-promotion manifest.
- Added optional-ready logic for final-evidence readiness, including legacy-compatible absence when both raw and Phase2 evidence are absent.
- Extended matrix/default-promotion match checks so final-evidence loss or divergence blocks publication preflight.
- Surfaced final-evidence readiness, match, raw, and Phase2 values in preflight check evidence, summary, and Markdown.
- Added focused tests for ready evidence, compatible-missing evidence, legacy absence, matrix evidence failure, matrix Phase2 evidence loss, default-promotion evidence failure, and standalone manifest evidence loss.
- Generated controlled Gate387 fixture artifacts for all covered paths.
- Updated Phase 2 planning docs and algorithm-source audit notes.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\windows_publish_preflight.py tests\test_windows_publish_preflight.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_windows_publish_preflight.py`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_387_cuda_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused publish-preflight tests: `58 passed in 1.61s`
- Full test suite: `920 passed in 36.74s`
- Ruff: `All checks passed`

## CUDA

- CUDA available: yes
- Native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Doctor artifact: `runs/checkpoints/s2_gate_387_cuda_doctor.json`

## Artifacts

- Fixture summary: `runs/checkpoints/s2_gate_387_fixtures/s2_gate_387_fixture_summary.json`
- Fixture preflight artifacts under `runs/checkpoints/s2_gate_387_fixtures/`
- Checkpoint: `runs/checkpoints/s2_gate_387_status.md`

## Known Limitations

- This gate is a local Windows publication-preflight guard only. It does not change image math, registration, local normalization, integration, CUDA kernels, runtime defaults, package builds, GitHub release creation, or real-data benchmark output.
- Final-evidence fields remain optional for legacy artifacts only when both raw and Phase2 evidence are absent; once present, raw and Phase2 evidence must be ready and matching across the matrix and standalone default-promotion manifest.

## Next Step

- S2-Gate 388 should carry the final-evidence publication-preflight result into the next Phase 2 status or publication-audit layer, so later handoff artifacts cannot lose the Gate387 local preflight result.

## Clean-Room Compliance

- Compliant. This gate consumes GLASS-owned release manifest, GitHub release plan, Windows release matrix, and default-promotion JSON artifacts only. It does not read external implementation source, proprietary code, PixInsight/WBPP source, or user image directories.
