# S2-Gate 316 Status: Enabled Local Normalization Guardrail

## Gate

S2-Gate 316

## Completed

- Added `glass guardrails --require-local-normalization-enabled`.
- Guardrails now fail when the new requirement is set and local normalization
  is missing, disabled, or has a failed `local_norm_contract.json`.
- Preserved compatibility for LN-off runs: disabled passthrough remains valid
  unless the require-enabled flag is supplied.
- Added `require_local_normalization_enabled` and
  `local_norm_contract_enabled` to `guardrails_summary.json`,
  `acceptance_contract_bundle.json`, console output, and guardrail checks.
- Added focused tests for disabled passthrough failure and enabled continuous
  local normalization success.
- Updated Phase 2 and Local Normalization documentation.

## Commands Run

```powershell
.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_314_synthetic_data --out runs\checkpoints\s2_gate_316_enabled_probe_run --backend cpu --tile-size 8 --local-normalization on
.venv\Scripts\python.exe -m glass.cli local-norm-contract --run runs\checkpoints\s2_gate_316_enabled_probe_run --out runs\checkpoints\s2_gate_316_enabled_probe_local_norm_contract.json --fail-on-failed
.venv\Scripts\ruff.exe check src\glass\cli.py tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_guardrails_require_enabled_local_normalization
.venv\Scripts\python.exe -m glass.cli audit --root runs\checkpoints\s2_gate_314_synthetic_data --out runs\checkpoints\s2_gate_316_enabled_run --backend cpu --tile-size 8 --local-normalization on
.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_316_enabled_run --out-dir runs\checkpoints\s2_gate_316_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --require-local-normalization-enabled --pixel-verify --pixel-verify-tile-size 8
.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_316_doctor.json
.venv\Scripts\ruff.exe check src\glass\cli.py tests\test_cli_smoke.py docs\phase2_algorithm_hardening.md docs\local_normalization_model.md
.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_guardrails_require_enabled_local_normalization
.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused ruff checks: passed.
- Focused guardrail tests: `2 passed`.
- CLI smoke tests: `23 passed`.
- Full test suite: `741 passed in 36.10s`.

## Checkpoint Artifacts

- `runs/checkpoints/s2_gate_316_status.md`
- `runs/checkpoints/s2_gate_316_doctor.json`
- `runs/checkpoints/s2_gate_316_enabled_run/`
- `runs/checkpoints/s2_gate_316_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_316_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_316_guardrails/local_norm_contract.json`
- `runs/checkpoints/s2_gate_316_guardrails/local_norm_contract.md`
- `runs/checkpoints/s2_gate_316_guardrails/pipeline_contract.json`
- `runs/checkpoints/s2_gate_316_guardrails/pipeline_contract.md`
- `runs/checkpoints/s2_gate_316_guardrails/stack_engine_contract.json`
- `runs/checkpoints/s2_gate_316_guardrails/stack_engine_contract.md`
- `runs/checkpoints/s2_gate_316_guardrails/report.html`

The checkpoint uses the small Gate314 synthetic data set as read-only input and
runs CPU `--local-normalization on` to produce an enabled continuous LN
contract.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- This gate adds an acceptance guardrail only. It does not change local
  normalization math, calibration, registration, integration, or CUDA kernels.
- The checkpoint validation run is intentionally tiny and CPU-only; no
  200-light real-data benchmark was rerun.
- The require-enabled flag is opt-in so existing LN-off benchmark evidence
  remains compatible unless a future gate explicitly requires LN-on.

## Next Step

- Continue Phase 2 hardening by applying similar opt-in guardrails to other
  algorithm requirements, or by strengthening enabled continuous LN runtime
  diagnostics and resident CUDA parity.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or modified.
- No PixInsight installation directory was touched.
- This gate only consumes GLASS-generated run artifacts and metadata.
- Input image directories were treated as read-only.
