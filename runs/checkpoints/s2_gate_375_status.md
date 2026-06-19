# S2-Gate 375 Status: Windows Publish Preflight Release Quality Publication Guard

## Gate

S2-Gate 375 extends `glass windows-publish-preflight` so final local Windows
publication preflight preserves release quality publication guard evidence from
Windows release-matrix and default-promotion artifacts.

## Completed

- Added release-quality publication guard extraction helpers in
  `src/glass/report/windows_publish_preflight.py`.
- Added final preflight checks for matrix, matrix-default, and default-promotion
  release quality publication guard evidence.
- Added matrix/default-promotion matching checks for both top-level matrix
  guard evidence and embedded default-promotion guard evidence.
- Added publish-preflight JSON summary and Markdown lines for release-quality
  publication guard state.
- Added focused tests for ready, compatible missing, failed matrix guard,
  failed default-promotion guard, and matrix/default-promotion mismatch cases.
- Updated Phase 2 gate documentation and algorithm-source audit index.
- Generated deterministic checkpoint fixtures under
  `runs/checkpoints/s2_gate_375_fixtures/`.

## Commands

- `.venv\Scripts\python.exe -m ruff check src\glass\report\windows_publish_preflight.py tests\test_windows_publish_preflight.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_windows_publish_preflight.py`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_375_cuda_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused tests: `47 passed in 1.19s`.
- Full suite: `869 passed in 35.29s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`.
- Doctor artifact: `runs/checkpoints/s2_gate_375_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_375_status.md`
- `runs/checkpoints/s2_gate_375_cuda_doctor.json`
- `runs/checkpoints/s2_gate_375_fixtures/fixture_index.json`
- `runs/checkpoints/s2_gate_375_fixtures/*/windows_publish_preflight.json`

## Known Limitations

- This gate is publish-preflight policy plumbing only.
- It does not change image math, quality thresholds, registration, integration,
  CUDA kernels, runtime defaults, package contents, GitHub release creation, or
  real-data benchmark results.
- GitHub release-plan evidence remains unchanged in this gate; the new checks
  validate release-matrix and default-promotion handoff consistency at final
  local preflight.

## Next Step

S2-Gate 376 should carry the final publish-preflight release-quality guard
evidence back into Phase 2 status/compare, so status regression checks cannot
lose the publication-preflight layer.

## Clean-Room

Compliant. This gate consumes only GLASS-owned release manifest, GitHub release
plan, Windows release matrix, and default-promotion JSON artifacts. It does not
read image pixels, user image directories, external implementation source,
proprietary behavior, package contents, GitHub releases, or benchmark reference
outputs.
