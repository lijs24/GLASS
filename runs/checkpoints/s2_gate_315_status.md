# S2-Gate 315 Status: Local Normalization Contract Report Handoff

## Gate

S2-Gate 315

## Completed

- Added a first-class "Local normalization contract" section to the HTML
  report.
- Added `glass report --local-norm-contract` for explicit contract report
  handoff.
- Preserved automatic report discovery for run-local
  `local_norm_contract*.json` artifacts.
- Updated guardrails report generation to pass the auto-generated
  `local_norm_contract.json` into `report.html`.
- Surfaced LN contract status, pass/fail state, enabled state, reference frame,
  model, coefficient-field model, crop box, output counts, failed checks,
  failed outputs, and per-output coefficient-grid summaries in HTML.
- Updated Phase 2 and Local Normalization documentation.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\html_report.py
.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_report_summarizes_local_norm_contract
.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_314_cpu_run --out-dir runs\checkpoints\s2_gate_315_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 8
.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_315_doctor.json
.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\html_report.py tests\test_cli_smoke.py docs\phase2_algorithm_hardening.md docs\local_normalization_model.md
.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_report_summarizes_local_norm_contract tests\test_cli_smoke.py::test_cli_report_summarizes_pipeline_contract
.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused ruff checks: passed.
- Focused report/guardrails tests: `3 passed`.
- CLI smoke tests: `22 passed`.
- Full test suite: `740 passed in 36.08s`.

## Checkpoint Artifacts

- `runs/checkpoints/s2_gate_315_status.md`
- `runs/checkpoints/s2_gate_315_doctor.json`
- `runs/checkpoints/s2_gate_315_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_315_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_315_guardrails/local_norm_contract.json`
- `runs/checkpoints/s2_gate_315_guardrails/local_norm_contract.md`
- `runs/checkpoints/s2_gate_315_guardrails/pipeline_contract.json`
- `runs/checkpoints/s2_gate_315_guardrails/pipeline_contract.md`
- `runs/checkpoints/s2_gate_315_guardrails/stack_engine_contract.json`
- `runs/checkpoints/s2_gate_315_guardrails/stack_engine_contract.md`
- `runs/checkpoints/s2_gate_315_guardrails/report.html`

The checkpoint reuses the small Gate314 CPU validation run as input to avoid
adding duplicate FITS input fixtures.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- This gate is report/audit plumbing only. It does not change local
  normalization math, calibration, registration, integration, or CUDA kernels.
- The checkpoint validation run is intentionally tiny and CPU-only; no
  200-light real-data benchmark was rerun.
- The checkpoint report shows the disabled local-normalization passthrough
  contract. Enabled/failing contract report coverage is exercised by focused
  tests using synthetic contract JSON.

## Next Step

- Continue Phase 2 hardening by strengthening enabled local-normalization
  runtime evidence or promoting another algorithm contract into guardrails and
  reports.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No PixInsight installation directory was touched.
- This gate only consumes GLASS-generated run artifacts and metadata.
- Input image directories were treated as read-only.
