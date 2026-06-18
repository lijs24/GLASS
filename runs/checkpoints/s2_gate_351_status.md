# S2-Gate 351 Status: Resume Registration Admission Guard

## Gate

- Gate: S2-Gate 351
- Status: passed
- Date: 2026-06-19

## Completed

- Extended blocked registration reference-admission handling to `glass resume`.
- If an existing `registration_results.json` contains `reference_admission.status=blocked`, resume now:
  - stops at registration;
  - writes `run_state.json` with `failed_stage=registration`;
  - writes a failed registration timing record with `resume_existing_artifact=true`;
  - returns exit code 2;
  - avoids warp/integration fall-through.
- Reused the Gate350 no-star admission fixture pattern to test resume behavior.
- Generated controlled Gate351 artifacts:
  - `runs/checkpoints/s2_gate_351_resume_admission_data/`
  - `runs/checkpoints/s2_gate_351_resume_admission_run/`
  - `runs/checkpoints/s2_gate_351_resume_admission_result.json`
  - `runs/checkpoints/s2_gate_351_cuda_doctor.json`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\cli.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_audit_and_run_write_state_for_registration_admission_block tests\test_cli_smoke.py::test_cli_scan_plan_report_audit_smoke tests\test_pipeline_fixture.py::test_resume_continues_from_warp_without_repeating_calibration`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_351_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_audit_and_run_write_state_for_registration_admission_block tests\test_pipeline_fixture.py::test_resume_continues_from_warp_without_repeating_calibration tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Initial resume focused subset: 3 passed.
- Gate351 focused CLI/resume subset: 29 passed.
- Full pytest: 800 passed in 33.86 s.
- Controlled resume artifact:
  - audit exit code: 2
  - resume exit code: 2
  - failed stage: registration
  - registration timing status: failed
  - `resume_existing_artifact`: true
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

- This gate changes resume control flow only.
- It does not change registration transform math, quality metric math, integration math, CUDA kernels, runtime defaults, packaging, publication artifacts, or real-data benchmark results.

## Next Step

- Continue Phase 2 hardening with report/contract surfacing for blocked registration admission, or move back to measured real-data optimization gates.

## Clean-Room Compliance

- Compliant.
- This gate used only GLASS-owned code, generated uniform FITS fixtures, and GLASS run artifacts.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- No user input image directory was modified.
