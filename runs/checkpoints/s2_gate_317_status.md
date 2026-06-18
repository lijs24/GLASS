# S2-Gate 317 Status: Local Normalization Residual Quality Guardrail

## Gate

S2-Gate 317

## Completed

- Added residual-quality aggregation to `local_norm_contract.json`.
- The LN contract summary now records output count, valid-output count,
  failed-output count, zero-valid-output count, total valid pixels, maximum
  residual RMS, maximum absolute residual, and per-output residual rows.
- Added residual max RMS/max absolute values to the LN contract Markdown.
- Added `glass guardrails --max-local-normalization-rms`.
- Added `glass guardrails --max-local-normalization-max-abs`.
- Guardrails now fail when a residual threshold is supplied and LN is missing,
  disabled, has a failed contract, lacks residual diagnostics, or exceeds the
  threshold.
- Surfaced residual quality and thresholds in guardrails summary, acceptance
  bundle, console output, local-normalization contract, and HTML report.
- Added focused tests for residual aggregation, passing thresholds, threshold
  failure after injected residual drift, and report visibility.
- Updated Phase 2 and Local Normalization documentation.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\local_norm_contract.py src\glass\report\html_report.py tests\test_cli_smoke.py tests\test_local_norm_contract.py docs\phase2_algorithm_hardening.md docs\local_normalization_model.md
.venv\Scripts\python.exe -m pytest -q tests\test_local_norm_contract.py tests\test_cli_smoke.py::test_cli_guardrails_local_norm_residual_thresholds tests\test_cli_smoke.py::test_cli_report_summarizes_local_norm_contract
.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_316_enabled_run --out-dir runs\checkpoints\s2_gate_317_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --require-local-normalization-enabled --max-local-normalization-rms 100 --max-local-normalization-max-abs 100 --pixel-verify --pixel-verify-tile-size 8
.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_317_doctor.json
.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q tests\test_local_norm_contract.py
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused ruff checks: passed.
- Focused residual/report tests: `7 passed`.
- CLI smoke tests: `24 passed`.
- Local-normalization contract tests: `5 passed`.
- Full test suite: `742 passed in 36.65s`.

## Checkpoint Artifacts

- `runs/checkpoints/s2_gate_317_status.md`
- `runs/checkpoints/s2_gate_317_doctor.json`
- `runs/checkpoints/s2_gate_317_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_317_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_317_guardrails/local_norm_contract.json`
- `runs/checkpoints/s2_gate_317_guardrails/local_norm_contract.md`
- `runs/checkpoints/s2_gate_317_guardrails/pipeline_contract.json`
- `runs/checkpoints/s2_gate_317_guardrails/pipeline_contract.md`
- `runs/checkpoints/s2_gate_317_guardrails/stack_engine_contract.json`
- `runs/checkpoints/s2_gate_317_guardrails/stack_engine_contract.md`
- `runs/checkpoints/s2_gate_317_guardrails/report.html`

The checkpoint reuses the small Gate316 enabled-LN CPU run as read-only input.
The generated residual summary reports one enabled LN output, 576 valid
residual pixels, max RMS `0.0`, and max absolute residual `0.0`.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- Residual thresholds are opt-in and unit-dependent; no default threshold is
  imposed.
- This gate does not change local-normalization math, calibration,
  registration, integration, or CUDA kernels.
- The checkpoint validation run is intentionally tiny and CPU-only; no
  200-light real-data benchmark was rerun.

## Next Step

- Continue Phase 2 hardening by adding comparable quality thresholds for
  registration, rejection, or frame-accounting evidence, or by extending
  residual-quality checks to resident CUDA parity artifacts.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No PixInsight installation directory was touched.
- This gate only consumes GLASS-generated run artifacts and metadata.
- Input image directories were treated as read-only.
