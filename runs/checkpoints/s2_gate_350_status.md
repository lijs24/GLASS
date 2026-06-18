# S2-Gate 350 Status: Registration Admission Run-State Guard

## Gate

- Gate: S2-Gate 350
- Status: passed
- Date: 2026-06-19

## Completed

- Added CLI control-flow handling for `reference_admission.status=blocked`.
- `glass audit` now returns exit code 2 for blocked registration reference admission.
- `glass run --until-stage integration` now returns exit code 2 for the same blocked-admission case.
- Both command paths write `run_state.json` with:
  - `current_stage=registration`
  - `failed_stage=registration`
  - an explicit registration admission error message
- Timing records now keep the registration stage as `failed`.
- Blocked-admission command paths do not create `integration_results.json`.
- Added CLI smoke coverage for both audit and run using a deliberately uniform no-star data set.
- Generated controlled Gate350 artifacts:
  - `runs/checkpoints/s2_gate_350_registration_admission_cli_data/`
  - `runs/checkpoints/s2_gate_350_registration_admission_cli_run/`
  - `runs/checkpoints/s2_gate_350_registration_admission_cli_result.json`
  - `runs/checkpoints/s2_gate_350_cuda_doctor.json`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\cli.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_audit_and_run_write_state_for_registration_admission_block tests\test_cli_smoke.py::test_cli_scan_plan_report_audit_smoke tests\test_cpu_registration.py tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_350_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_audit_and_run_write_state_for_registration_admission_block tests\test_cli_smoke.py tests\test_pipeline_fixture.py tests\test_benchmarks.py::test_bench_end_to_end_cpu_outputs_required_fields`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Initial CLI/run-state focused subset: 38 passed.
- Gate350 focused CLI/pipeline/benchmark subset: 49 passed.
- Full pytest: 800 passed in 34.01 s.
- Controlled CLI artifact:
  - exit code: 2
  - failed stage: registration
  - registration timing status: failed
  - integration artifact present: false

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor recommendation: cuda.

## Known Limitations

- This gate covers `glass audit` and `glass run`; `glass resume` still follows its existing resume-specific control flow and can be hardened separately.
- This gate changes CLI/run-state behavior only. It does not change registration transform math, quality metric math, integration math, CUDA kernels, runtime defaults, packaging, publication artifacts, or real-data benchmark results.

## Next Step

- Continue Phase 2 hardening with resume-specific failure propagation or the next contract/report layer that should surface blocked registration admission.

## Clean-Room Compliance

- Compliant.
- This gate used only GLASS-owned code, generated synthetic/uniform FITS fixtures, and GLASS run artifacts.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- No user input image directory was modified.
