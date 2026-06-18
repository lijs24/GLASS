# S2-Gate 318 Status - Registration Quality Guardrail

## Gate

S2-Gate 318: Registration quality guardrail.

## Completed

- Added a reusable registration quality contract artifact:
  - `registration_quality_contract.json`
  - `registration_quality_contract.md`
- Added opt-in guardrail thresholds:
  - `--max-registration-rms-px`
  - `--min-registration-inliers`
  - `--require-registration-all-accepted`
- Preserved default compatibility: registration quality is reported when registration artifacts exist, but it only blocks when thresholds or all-accepted enforcement are requested.
- Added registration quality to guardrails summaries, acceptance bundles, console output, and HTML reports.
- Added focused tests for pass/fail contract behavior and CLI threshold enforcement.
- Documented the S2-Gate 318 contract in the Phase 2 hardening notes and registration model notes.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\html_report.py src\glass\report\registration_quality.py tests\test_cli_smoke.py tests\test_registration_quality_contract.py docs\phase2_algorithm_hardening.md docs\registration_model.md

.venv\Scripts\python.exe -m pytest -q tests\test_registration_quality_contract.py tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_guardrails_registration_quality_thresholds

.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_316_enabled_run --out-dir runs\checkpoints\s2_gate_318_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --require-local-normalization-enabled --max-registration-rms-px 0.1 --min-registration-inliers 5 --pixel-verify --pixel-verify-tile-size 8

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_318_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 4 passed.
- Full pytest: 745 passed in 37.25 s.
- Guardrails: passed.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor recommendation: cuda.

## Artifacts

- `runs/checkpoints/s2_gate_318_doctor.json`
- `runs/checkpoints/s2_gate_318_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_318_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_318_guardrails/registration_quality_contract.json`
- `runs/checkpoints/s2_gate_318_guardrails/registration_quality_contract.md`
- `runs/checkpoints/s2_gate_318_guardrails/report.html`

## Registration Quality Result

- Contract status: passed.
- Output count: 3.
- Accepted count: 1.
- Failed/rejected count: 2.
- Accepted max RMS: 0.0 px.
- Accepted min inliers: 5.
- Quality-gate rejected frames: 2.
- Reference frame: `F000010`.
- Transform model: translation.

## Known Limitations

- The contract verifies reported registration artifacts; it does not make the current registration model PixInsight-equivalent.
- Rejected registration rows are allowed by default and only become blocking when `--require-registration-all-accepted` is used.
- The current threshold checks apply to accepted registration outputs. Rejected rows are surfaced in the contract and summary, but are not threshold-checked unless all-accepted enforcement is requested.
- This gate did not rerun the 200-light benchmark dataset; it reused the existing S2-Gate 316 enabled run for deterministic guardrail validation.

## Next Step

- Continue Phase 2 hardening by turning the next high-risk quality surface into a contract-backed gate, preferably registration/warp pixel residual diagnostics or resident pipeline performance regression tracking.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated run artifacts and synthetic/checkpoint outputs.
- Input image directories were not modified.
