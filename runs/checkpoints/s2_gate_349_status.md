# S2-Gate 349 Status: Registration Reference Admission Policy

## Gate

- Gate: S2-Gate 349
- Status: passed
- Date: 2026-06-19

## Completed

- Added `reference_admission` metadata to `registration_results.json`.
- Default policy now blocks a selected reference frame from becoming an accepted registration output when:
  - quality-gate rejection is enforced; and
  - the selected reference has `quality_gate_status=rejected`; and
  - `registration_policy.allow_quality_rejected_reference` is not explicitly true.
- Blocked reference fallback writes diagnostic registration rows with `status=quality_rejected`, `registration_solution_source=quality_reference_admission`, and failed validation evidence.
- Verified that blocked registration outputs stop warp before integration with `registration produced no accepted frames for warp`.
- Preserved an explicit diagnostic override through `registration_policy.allow_quality_rejected_reference=true`.
- Improved tiny synthetic fixtures by generating fewer separated stars below 64 px so smoke benchmarks do not create overcrowded zero-detection star fields.
- Generated controlled Gate349 artifacts:
  - `runs/checkpoints/s2_gate_349_blocked_reference_run/`
  - `runs/checkpoints/s2_gate_349_blocked_reference_warp_error.json`
  - `runs/checkpoints/s2_gate_349_cuda_doctor.json`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\engine\registration.py tests\test_cpu_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_349_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\ruff.exe check src\glass\engine\registration.py tests\test_cpu_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_pipeline_fixture.py tests\test_cli_smoke.py tests\test_pipeline_contract.py`
- `.\.venv\Scripts\ruff.exe check src\glass\engine\registration.py src\glass\synthetic\generator.py tests\test_cpu_registration.py tests\test_synthetic_generator.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_synthetic_generator.py tests\test_benchmarks.py::test_bench_end_to_end_cpu_outputs_required_fields`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Registration focused tests: 16 passed.
- Pipeline/CLI/pipeline-contract regression subset: 91 passed.
- Synthetic/benchmark focused tests: 19 passed.
- Full pytest: 799 passed in 33.81 s.
- Controlled blocked-reference artifact:
  - `reference_admission.status=blocked`
  - `reference_admission.quality_gate_status=rejected`
  - warp status: `blocked`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor recommendation: cuda.

## Known Limitations

- This gate changes registration admission policy, not transform estimation math.
- Existing diagnostic experiments can still allow a rejected reference by setting `registration_policy.allow_quality_rejected_reference=true`.
- The command runner still reports stage errors according to existing CLI flow; this gate ensures the registration artifact itself no longer presents rejected fallback references as accepted registration results.
- No real-data benchmark was rerun.

## Next Step

- Continue Phase 2 hardening with the next gate focused on making stage-failure/run-state reporting catch registration admission failures earlier in the CLI flow.

## Clean-Room Compliance

- Compliant.
- This gate used only GLASS-owned code, generated synthetic data, and GLASS run artifacts.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- No input image directory was modified.
