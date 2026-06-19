# S2-Gate 402 Status

- Gate: S2-Gate 402
- Scope: Resident Benchmark Contract Profile Generator
- Status: green
- Date: 2026-06-19

## Completed

- Added `src/glass/report/benchmark_contract_profile.py`.
- Added the reusable `resident_cuda_dq_v1` benchmark-contract generator for
  resident CUDA acceptance audits.
- Added `glass benchmark-contract-profile` to write a loadable benchmark
  contract artifact with:
  - 200 light / 20 bias / 20 dark / 20 flat dataset minima.
  - 190 active light frame minimum.
  - Resident route and throughput-pipeline command-token requirements.
  - 2x minimum speedup-vs-reference threshold.
  - Compare tolerances for coverage fraction, RMS difference, and p99 absolute
    difference.
  - The shared resident DQ provenance profile from S2-Gate 401.
- Added `tests/test_benchmark_contract_profile.py`, including generation,
  override, CLI, independent-list, and acceptance-audit consumption coverage.
- Generated `runs/checkpoints/s2_gate_402_resident_cuda_dq_contract.json` with
  the new CLI.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\benchmark_contract_profile.py src\glass\report\dq_contract_profile.py src\glass\cli.py tests\test_benchmark_contract_profile.py tests\test_dq_contract_profile.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmark_contract_profile.py tests\test_dq_contract_profile.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m glass.cli benchmark-contract-profile --help`
- `.\.venv\Scripts\python.exe -m glass.cli benchmark-contract-profile --out runs\checkpoints\s2_gate_402_resident_cuda_dq_contract.json --dq-map-verify-tile-size 2048 --count-map-verify-tile-size 2048`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_402_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Results

- Ruff: passed.
- Focused pytest: 52 passed in 1.22 s.
- Full pytest: 959 passed in 37.38 s.
- CLI help: `glass benchmark-contract-profile --help` passed.
- Generated benchmark contract:
  `runs/checkpoints/s2_gate_402_resident_cuda_dq_contract.json`.
- CUDA doctor JSON: `runs/checkpoints/s2_gate_402_cuda_doctor.json`.

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

- This gate generates a benchmark-contract artifact; it does not run or update
  the real 200-light benchmark.
- The generated profile intentionally does not embed a release-baseline elapsed
  time unless supplied by the caller.
- The profile is currently focused on resident CUDA DQ/coverage/rejection
  acceptance. Later gates can extend generated profiles for frame-accounting,
  warp-quality, pipeline-contract, and StackEngine promotion bundles.
- No DQ pixel semantics, quality metric math, star detection, registration,
  integration, CUDA kernel, runtime default, package artifact, GitHub release,
  or real-data benchmark behavior changed.

## Next Step

- Continue Phase 2 by using this generated contract in higher-level
  acceptance/release bundles, or return to runtime hardening for resident
  registration/warp orchestration and H2D pipeline efficiency.

## Clean-Room Compliance

- This gate used only GLASS-owned policy dictionaries, CLI code, tests,
  generated contract JSON, and generated doctor output.
- It did not read PixInsight/WBPP/PJSR source code, proprietary implementation
  details, package contents, user image directories, or external reference
  outputs.
- Input image directories remain untouched.
