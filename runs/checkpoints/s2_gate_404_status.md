# S2-Gate 404 Status

- Gate: S2-Gate 404
- Scope: Runtime Sweep Acceptance Profile Handoff
- Status: green
- Date: 2026-06-19

## Completed

- Updated `glass candidate-runtime-sweep-plan` so planned
  `acceptance-audit` commands use
  `--benchmark-contract-profile resident_cuda_dq_v1` when no explicit
  `--benchmark-contract` file is supplied.
- Preserved explicit benchmark-contract file behavior; when a file is supplied,
  planned acceptance commands continue to use `--benchmark-contract`.
- Recorded the effective benchmark contract source/profile in plan-level and
  per-variant artifact metadata.
- Updated focused tests for explicit file contracts, default profile contracts,
  and CLI-generated runtime sweep plans.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands

- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\candidate_runtime_sweep_plan.py src\glass\cli.py tests\test_candidate_runtime_sweep_plan.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_candidate_runtime_sweep_plan.py tests\test_benchmark_contract_profile.py`
- `.\.venv\Scripts\python.exe -m glass.cli candidate-runtime-sweep-plan --help`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_404_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\candidate_runtime_sweep_plan.py src\glass\cli.py tests\test_candidate_runtime_sweep_plan.py tests\test_tile_local_rejection_registration_plan.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_candidate_runtime_sweep_plan.py tests\test_benchmark_contract_profile.py tests\test_tile_local_rejection_registration_plan.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Results

- Initial focused ruff: passed.
- Initial focused pytest: 10 passed in 0.38 s.
- CLI help: `glass candidate-runtime-sweep-plan --help` showed
  `--benchmark-contract-profile {resident_cuda_dq_v1}`.
- Initial full pytest exposed a CLI handler regression in
  `tile-local-rejection-registration-plan`; the misplaced
  `benchmark_contract_profile` argument was removed and the intended
  `candidate-runtime-sweep-plan` handler was wired instead.
- Repair focused ruff: passed.
- Repair focused pytest: 12 passed in 0.44 s.
- Final full pytest: 961 passed in 37.33 s.
- CUDA doctor JSON: `runs/checkpoints/s2_gate_404_cuda_doctor.json`.

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

- This gate updates runtime sweep planning and generated acceptance commands
  only; it does not execute the real 200-light sweep.
- The default planned profile is currently `resident_cuda_dq_v1`; explicit
  benchmark-contract JSON files still take precedence.
- No runtime execution behavior, benchmark contract check semantics, DQ pixel
  semantics, quality metric math, star detection, registration, integration,
  CUDA kernels, package artifacts, GitHub releases, or real-data benchmark
  outputs changed.

## Next Step

- Continue Phase 2 by adding the same profile provenance to release promotion
  or Phase 2 status summaries, or return to resident runtime hardening for
  registration/warp orchestration and H2D pipeline efficiency.

## Clean-Room Compliance

- This gate used only GLASS-owned runtime sweep planning code, CLI code, tests,
  generated doctor output, and GLASS fixture artifacts.
- It did not read PixInsight/WBPP/PJSR source code, proprietary implementation
  details, package contents, user image directories, or external reference
  outputs.
- Input image directories remain untouched.
