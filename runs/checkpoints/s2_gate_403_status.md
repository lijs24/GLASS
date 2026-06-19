# S2-Gate 403 Status

- Gate: S2-Gate 403
- Scope: Acceptance-Audit Benchmark Profile Shortcut
- Status: green
- Date: 2026-06-19

## Completed

- Added `benchmark_contract_profile` support to `build_acceptance_audit`.
- Added `glass acceptance-audit --benchmark-contract-profile resident_cuda_dq_v1`.
- Preserved existing `--benchmark-contract` file-path behavior.
- Made acceptance-audit JSON summaries record benchmark contract source,
  path, and profile when a contract payload is active.
- Added Python API and CLI coverage proving the built-in resident CUDA DQ
  benchmark profile is consumed by acceptance-audit and triggers DQ checks.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\acceptance_audit.py src\glass\report\benchmark_contract_profile.py src\glass\cli.py tests\test_benchmark_contract_profile.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmark_contract_profile.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --help`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_403_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Results

- Ruff: passed.
- Focused pytest: 50 passed in 1.30 s.
- Full pytest: 961 passed in 37.53 s.
- CLI help: `glass acceptance-audit --help` showed
  `--benchmark-contract-profile {resident_cuda_dq_v1}`.
- CUDA doctor JSON: `runs/checkpoints/s2_gate_403_cuda_doctor.json`.

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

- This gate adds an in-memory profile shortcut for acceptance-audit; it does
  not replace the generated JSON contract artifact path from S2-Gate 402.
- The shortcut currently supports only `resident_cuda_dq_v1`.
- It does not alter benchmark contract check semantics, DQ pixel semantics,
  quality metric math, star detection, registration, integration, CUDA
  kernels, runtime defaults, package artifacts, GitHub releases, or real-data
  benchmark outputs.

## Next Step

- Continue Phase 2 by wiring the resident CUDA DQ benchmark profile into
  higher-level release/acceptance bundles, or return to resident runtime
  hardening for registration/warp orchestration and H2D pipeline efficiency.

## Clean-Room Compliance

- This gate used only GLASS-owned acceptance-audit code, benchmark profile
  builders, tests, generated doctor output, and GLASS fixture artifacts.
- It did not read PixInsight/WBPP/PJSR source code, proprietary implementation
  details, package contents, user image directories, or external reference
  outputs.
- Input image directories remain untouched.
