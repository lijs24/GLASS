# S2-Gate 157 Status: Resumable Runtime Sweep Executor

## Gate

S2-Gate 157: Resumable Runtime Sweep Executor.

## Completed Content

- Added `glass candidate-runtime-sweep-execute`.
- Added `src/glass/report/candidate_runtime_sweep_execute.py`.
- The executor consumes a `candidate_runtime_sweep_plan` artifact and records
  variant step status for `run`, `compare_reference`, `compare_baseline`,
  `acceptance_audit`, `candidate_comparison`, and final sweep summary.
- Supports dry-run, `--skip-existing`, repeated `--variant`, `--start-at`,
  `--stop-after`, `--no-sweep-summary`, `--glass-executable`, `--cwd`, and
  `--fail-on-failed`.
- Hardened local diagnostics:
  - `glass doctor --skip-cuda-probe` avoids Windows/CUDA probe hangs.
  - CUDA tests skip when `nvidia-smi` reports low free VRAM or saturated GPU.
  - Optional astroalign-dependent tests skip when an astroalign smoke test
    times out.
  - Optional benchmark subprocesses have explicit timeouts.
  - Removed a `np.testing` call that triggered Windows WMI platform queries in
    this environment.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\glass.exe candidate-runtime-sweep-execute --plan C:\glass_runs\phase2_s2_gate_156_prefetch_matrix\candidate_runtime_sweep_plan.json --out C:\glass_runs\phase2_s2_gate_157_runtime_executor\prefetch_matrix_execution_dry_run.json --dry-run --skip-existing --glass-executable C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\glass.exe --cwd C:\Users\ljs\WORK\astro\gpuwbpp`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --skip-cuda-probe --json runs\checkpoints\s2_gate_157_doctor.json`
- `.\.venv\Scripts\glass.exe candidate-runtime-sweep-execute --help`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_candidate_runtime_sweep_execute.py tests/test_cli_smoke.py::test_cli_help_commands tests/test_cli_smoke.py::test_cli_doctor_cpu_only_success tests/test_capabilities.py tests/test_cuda_skip_policy.py tests/test_benchmarks.py::test_compare_astroalign_gpu_alignment_records_direct_diff`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cpu_registration.py tests/test_benchmarks.py::test_compare_astroalign_gpu_alignment_records_direct_diff -vv`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_tile_capture.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader,nounits`
- Direct `glass_cuda` probe from Python.

## Test Results

- Focused Gate157 tests after Windows command-token fix: `12 passed in 1.65s`.
- Astroalign gate tests after smoke-test guard: `11 passed, 4 skipped in 8.39s`.
- Resident tile capture after WMI-safe assertion fix: `3 passed in 0.51s`.
- Final full test suite: `397 passed in 18.94s`.
- Ruff: `All checks passed!`

The astroalign smoke-test guard remains in place because it previously timed
out in this environment during Gate157 debugging. The final authoritative full
suite completed without skips after the environment recovered.

## Artifacts

- Dry-run execution artifact:
  `C:\glass_runs\phase2_s2_gate_157_runtime_executor\prefetch_matrix_execution_dry_run.json`
- Doctor report:
  `runs/checkpoints/s2_gate_157_doctor.json`

Dry-run summary:

- `artifact_type`: `candidate_runtime_sweep_execution`
- selected variants: 9
- status: `planned`
- completed variants: 0
- skipped existing variants: 0
- final sweep summary status: `planned`

## CUDA Status

- `glass_cuda.cuda_available()`: `True`
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB reported by `glass_cuda`
- Driver: 596.21
- `nvidia-smi` during checkpoint:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 596.21, 97887, 1389, 0, 38`
- The doctor report was intentionally run with `--skip-cuda-probe`, so its
  CUDA availability fields are CPU-safe diagnostic fields rather than the
  authoritative GPU availability check.

## Known Limitations

- Gate157 validates the executor using dry-run mode. It does not execute the
  9-cell S2-Gate 156 matrix.
- `--skip-existing` currently checks for the candidate-comparison artifact for
  each variant. It does not independently validate every intermediate run or
  compare artifact.
- If a non-dry-run step fails, execution stops at the first failed step and the
  recorded JSON should be used to resume with `--start-at` or `--skip-existing`
  after fixing the cause.
- Astroalign is treated as optional. If its small smoke test times out,
  astroalign-dependent tests skip rather than hanging the whole suite.

## Next Step

S2-Gate 158 should execute the Gate156 prefetch/worker matrix when the GPU is
reserved for GLASS, then run reference compare, baseline compare, acceptance
audit, candidate comparison, and final sweep summary for the measured variants.

## Clean-Room Compliance

Compliant. This gate adds GLASS command orchestration, diagnostic skip policies,
and test harness hardening. It does not read image pixels for algorithm
development, does not use external implementation source, does not alter
scientific defaults, and does not modify input image directories.
