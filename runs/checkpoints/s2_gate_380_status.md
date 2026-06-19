# S2-Gate 380 Status: Windows Release Matrix Release Quality Final Guard

## Gate

- Gate: S2-Gate 380
- Status: Passed
- Scope: Windows release-matrix guard only

## Completed

- Carried Gate379 default-promotion final release quality publication evidence
  into `glass windows-release-matrix`.
- Added release-matrix blocking logic for:
  - failed direct release-decision final release quality checks;
  - failed default-promotion final release quality checks;
  - default-promotion loss of final-check evidence when release decision carries
    it.
- Preserved compatibility for artifacts that explicitly omit raw and Phase2
  final-check evidence on both release-decision and default-promotion sides.
- Surfaced final-check ready, match, compatible-missing, raw, Phase2, and
  release-matrix/default-promotion values in JSON evidence and Markdown.
- Added checkpoint fixtures for ready, compatible-missing, failed direct,
  missing default-promotion, and failed default-promotion final-check scenarios.

## Commands

- `.venv\Scripts\python.exe -m ruff check src\glass\report\windows_release_matrix.py tests\test_windows_release_matrix.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_windows_release_matrix.py`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_380_cuda_doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Targeted Windows release matrix tests: 41 passed.
- Full test suite: 885 passed in 35.73 s.
- Ruff: passed for touched Python files.

## CUDA

- CUDA available: yes.
- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_380_cuda_doctor.json`
- `runs/checkpoints/s2_gate_380_fixtures/ready/`
- `runs/checkpoints/s2_gate_380_fixtures/compatible_missing_final_checks/`
- `runs/checkpoints/s2_gate_380_fixtures/failed_direct_final_checks/`
- `runs/checkpoints/s2_gate_380_fixtures/missing_default_promotion_final_checks/`
- `runs/checkpoints/s2_gate_380_fixtures/failed_default_promotion_final_checks/`

## Known Limitations

- This gate does not change image calibration, registration, local
  normalization, integration, quality metric math, CUDA kernels, runtime
  defaults, package build outputs, or GitHub releases.
- This gate does not rerun the 200-light real-data benchmark.
- The guard validates release artifact evidence handoff; it is not a scientific
  image-quality comparison.

## Next Step

- Continue the release publication chain by carrying this final release quality
  guard from Windows release-matrix into Windows publish-preflight.

## Clean-Room Compliance

- The gate consumes only GLASS-owned JSON artifacts and test fixtures.
- No user image directory was modified.
- No external implementation source was read, copied, summarized, or reworked.
- No proprietary behavior was used as implementation input.
