# S2-Gate 348 Status: Pipeline Contract Frame Admission Guard

## Gate

- Gate: S2-Gate 348
- Status: passed
- Date: 2026-06-19

## Completed

- Added `frame_accounting_no_integration_conflicts` to `glass pipeline-contract`.
- Added frame admission summary and per-conflict evidence to pipeline-contract JSON and Markdown.
- Added controlled tests proving a clean `frame_accounting.json` passes and a positive-weight rejected-frame ledger fails with frame id and upstream conflict reasons.
- Added adaptive effective `min_stars` metadata for tiny synthetic quality-gate fixtures so CPU audit smoke runs do not falsely enter the all-quality-rejected fallback path.
- Updated the shared `small_fits_dataset` fixture so its light frame contains off-tile synthetic stars while preserving the legacy constant tile read by existing tile-source tests.
- Generated controlled Gate348 conflict artifacts:
  - `runs/checkpoints/s2_gate_348_controlled_admission_conflict_run/`
  - `runs/checkpoints/s2_gate_348_pipeline_contract_conflict.json`
  - `runs/checkpoints/s2_gate_348_pipeline_contract_conflict.md`
  - `runs/checkpoints/s2_gate_348_cuda_doctor.json`

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\engine\quality.py src\glass\report\pipeline_contract.py tests\test_cpu_star_detect.py tests\test_pipeline_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_star_detect.py tests\test_pipeline_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_accounting.py tests\test_pipeline_fixture.py tests\test_stack_engine_contract.py`
- `.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_348_cuda_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\python.exe -m glass.cli pipeline-contract --run runs\checkpoints\s2_gate_348_controlled_admission_conflict_run --out runs\checkpoints\s2_gate_348_pipeline_contract_conflict.json --markdown runs\checkpoints\s2_gate_348_pipeline_contract_conflict.md`
- `.\.venv\Scripts\ruff.exe check tests\conftest.py tests\test_cli_smoke.py tests\test_phase2_contracts.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_guardrails_require_enabled_local_normalization tests\test_cli_smoke.py::test_cli_guardrails_local_norm_residual_thresholds tests\test_cli_smoke.py::test_cli_guardrails_registration_quality_thresholds tests\test_cli_smoke.py::test_cli_guardrails_warp_quality_thresholds tests\test_phase2_contracts.py::test_fits_image_source_reads_tile_and_mask`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused quality/pipeline-contract tests: 35 passed.
- Frame-accounting/pipeline fixture/StackEngine contract tests: 35 passed.
- Guardrails regression subset: 6 passed.
- Full pytest: 796 passed in 33.34 s.
- Controlled conflict CLI result: `glass pipeline-contract` exited with expected code 2 and reported one `frame_accounting_no_integration_conflicts` failure.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor recommendation: cuda.

## Known Limitations

- This gate adds contract/admission checks and tiny-fixture quality-gate metadata only.
- It does not change registration transform math, integration math, resident CUDA kernels, runtime defaults, packaging, publication artifacts, or real-data benchmark results.
- The reference-frame fallback path is now visible to pipeline-contract admission checks; degenerate all-quality-rejected runs should be treated as diagnostic failures unless explicitly handled by a later gate.

## Next Step

- Continue Phase 2 hardening with the next gate focused on turning reference fallback/admission edge cases into explicit run-stage policy before they reach integration.

## Clean-Room Compliance

- Compliant.
- This gate used only GLASS-owned code, tests, generated synthetic fixtures, and GLASS run artifacts.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- No input image directory was modified.
