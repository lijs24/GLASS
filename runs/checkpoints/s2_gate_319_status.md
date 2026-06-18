# S2-Gate 319 Status - Warp Quality Guardrail

## Gate

S2-Gate 319: Warp quality guardrail.

## Completed

- Added `warp_quality_contract.json` and `warp_quality_contract.md` artifacts generated from `warp_results.json`.
- Added opt-in guardrail thresholds and requirements:
  - `--min-warp-valid-fraction`
  - `--max-warp-skipped-frames`
  - `--require-warp-artifacts`
  - `--require-warp-all-registered`
- Preserved default compatibility: warp quality is reported when warp artifacts exist, but it only blocks when a warp threshold or requirement is supplied.
- Added warp quality to guardrails summaries, acceptance bundles, console output, and HTML reports.
- Added focused tests for standalone warp contract pass/fail behavior and CLI threshold enforcement.
- Documented the S2-Gate 319 contract in the Phase 2 hardening notes and registration/warp model notes.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\html_report.py src\glass\report\warp_quality.py tests\test_cli_smoke.py tests\test_warp_quality_contract.py docs\phase2_algorithm_hardening.md docs\registration_model.md

.venv\Scripts\python.exe -m pytest -q tests\test_warp_quality_contract.py tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report tests\test_cli_smoke.py::test_cli_guardrails_warp_quality_thresholds

.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_316_enabled_run --out-dir runs\checkpoints\s2_gate_319_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --require-local-normalization-enabled --min-warp-valid-fraction 1.0 --max-warp-skipped-frames 2 --require-warp-artifacts --require-warp-all-registered --pixel-verify --pixel-verify-tile-size 8

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_319_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 5 passed.
- Full pytest: 749 passed in 33.24 s.
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

- `runs/checkpoints/s2_gate_319_doctor.json`
- `runs/checkpoints/s2_gate_319_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_319_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_319_guardrails/warp_quality_contract.json`
- `runs/checkpoints/s2_gate_319_guardrails/warp_quality_contract.md`
- `runs/checkpoints/s2_gate_319_guardrails/report.html`

## Warp Quality Result

- Contract status: passed.
- Required: true.
- Output count: 1.
- Skipped count: 2.
- Artifact-ready count: 1.
- Accepted registration count: 1.
- Missing warp outputs for accepted registration frames: 0.
- Minimum valid fraction: 1.0.
- Maximum valid fraction: 1.0.
- Interpolation: bilinear.
- Interpolator registry: nearest, bilinear, bicubic, lanczos3.

## Known Limitations

- The contract verifies warp metadata, FITS header shape, and artifact readiness; it does not re-read full warp images by default.
- The contract trusts reported `valid_pixels` unless future pixel-verification gates explicitly attach a full coverage-map scan.
- This gate does not change interpolation math, registration math, CUDA kernels, runtime defaults, package builds, or release artifacts.
- This gate did not rerun the 200-light benchmark; it reused the existing S2-Gate 316 enabled run for deterministic guardrail validation.

## Next Step

- Continue Phase 2 hardening by adding a pixel-level warp/coverage verification mode or by turning resident runtime regressions into a first-class guardrail contract.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated run artifacts and synthetic/checkpoint outputs.
- Input image directories were not modified.
