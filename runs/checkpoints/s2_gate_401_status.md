# S2-Gate 401 Status

- Gate: S2-Gate 401
- Scope: Resident DQ Provenance Contract Profile
- Status: green
- Date: 2026-06-19

## Completed

- Added `src/glass/report/dq_contract_profile.py`.
- Added a shared resident CUDA `dq_provenance` benchmark-contract profile for
  DQ, coverage, low-rejection, high-rejection, source terms, and resident
  artifact map-path evidence.
- Moved acceptance-audit DQ contract setup onto the shared profile while
  preserving existing field names, thresholds, and pass/fail semantics.
- Added `tests/test_dq_contract_profile.py` for profile defaults, override
  parameters, independent mutable lists, and attachment behavior.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\dq_contract_profile.py tests\test_dq_contract_profile.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_dq_contract_profile.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_401_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Results

- Ruff: passed.
- Focused pytest: 47 passed in 1.11 s.
- Full pytest: 954 passed in 37.29 s.
- CUDA doctor JSON: `runs/checkpoints/s2_gate_401_cuda_doctor.json`.

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Known Limitations

- This gate formalizes a resident DQ provenance contract profile only.
- It does not change DQ pixel semantics, coverage-map generation, rejection-map
  generation, integration math, CUDA kernels, runtime defaults, package
  artifacts, GitHub releases, or real-data benchmark outputs.
- The profile is currently consumed by acceptance-audit tests; later gates can
  reuse it in additional release, benchmark, or publication contract builders.

## Next Step

- Continue Phase 2 runtime hardening by applying the shared DQ provenance
  profile deeper into benchmark/release contract generation or returning to the
  resident registration/warp and H2D pipeline efficiency work.

## Clean-Room Compliance

- This gate used only GLASS-owned report contracts, tests, generated doctor
  output, and artifact metadata created by GLASS tests.
- It did not read PixInsight/WBPP/PJSR source code, proprietary implementation
  details, package contents, user image directories, or external reference
  outputs.
- Input image directories remain untouched.
