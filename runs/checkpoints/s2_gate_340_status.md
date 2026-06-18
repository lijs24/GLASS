# S2-Gate 340 Status

- Gate: 340
- Status: green
- Scope: Windows release matrix resident result-contract guard
- Date: 2026-06-19

## Completed

- Carried default-promotion resident result-contract evidence into
  `glass windows-release-matrix`.
- Added `default_promotion_resident_result_contract_handoff_passed` as a
  Windows release-matrix blocker.
- Required default-promotion resident result-contract evidence to be present,
  ready, passed, Phase2-checked, required by at least one output, and free of
  failed output rows or nested failed checks before Windows CUDA package
  readiness can pass.
- Surfaced resident result-contract readiness, status, Phase2 check, required
  count, failed count, and failed nested check names in release-matrix
  Markdown.
- Added focused tests for passing Blackwell/default-promotion artifacts and
  failed resident result-contract drift.
- Generated controlled Gate340 Windows release-matrix artifacts for passing and
  blocked resident result-contract scenarios.

## Commands

- `.venv\Scripts\ruff.exe check src\glass\report\windows_release_matrix.py tests\test_windows_release_matrix.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_windows_release_matrix.py -k "resident_result_contract or blackwell_default"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_windows_release_matrix.py`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_340_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m glass.cli windows-release-matrix --doctor-json runs\checkpoints\s2_gate_340_doctor.json --release-decision runs\checkpoints\s2_gate_339_fixture\release_decision.json --default-promotion-manifest runs\checkpoints\s2_gate_339_default_promotion_passed.json --out runs\checkpoints\s2_gate_340_windows_release_matrix_passed.json --markdown runs\checkpoints\s2_gate_340_windows_release_matrix_passed.md --expected-primary-package cuda13 --allow-missing-direct-runtime-evidence`
- `.venv\Scripts\python.exe -m glass.cli windows-release-matrix --doctor-json runs\checkpoints\s2_gate_340_doctor.json --release-decision runs\checkpoints\s2_gate_339_fixture\release_decision.json --default-promotion-manifest runs\checkpoints\s2_gate_339_default_promotion_failed_resident_result.json --out runs\checkpoints\s2_gate_340_windows_release_matrix_failed_resident_result.json --markdown runs\checkpoints\s2_gate_340_windows_release_matrix_failed_resident_result.md --expected-primary-package cuda13 --allow-missing-direct-runtime-evidence`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused release-matrix tests: `2 passed, 24 deselected in 0.19s`
- Release-matrix test file: `26 passed in 0.38s`
- Full suite: `778 passed in 38.12s`
- Ruff: passed

## CUDA

- CUDA available: yes
- CUDA native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/checkpoints/s2_gate_340_doctor.json`
- `runs/checkpoints/s2_gate_340_windows_release_matrix_passed.json`
- `runs/checkpoints/s2_gate_340_windows_release_matrix_passed.md`
- `runs/checkpoints/s2_gate_340_windows_release_matrix_failed_resident_result.json`
- `runs/checkpoints/s2_gate_340_windows_release_matrix_failed_resident_result.md`

## Known Limitations

- This gate is release-matrix scoped. It does not change resident CUDA
  integration math, registration math, runtime defaults, package artifacts, or
  benchmark results.
- The generated release-matrix artifacts use controlled default-promotion
  fixtures rather than a new 200-light real-data rerun.
- The release-matrix artifact generation used
  `--allow-missing-direct-runtime-evidence` so the pass/fail contrast isolates
  the resident result-contract handoff; direct runtime evidence remains covered
  by existing release-matrix tests and prior gates.

## Next Step

- Carry the release-matrix resident result-contract guard into the GitHub
  release-plan layer so publication scripts cannot advance when package-matrix
  resident result-contract evidence is missing or failed.

## Clean-Room

- Compliant. This gate consumes GLASS-owned doctor, release-decision, and
  default-promotion manifest artifacts only. It does not inspect
  PixInsight/WBPP/PJSR source, modify PixInsight, or read user image
  directories.
