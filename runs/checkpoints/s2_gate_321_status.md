# S2-Gate 321 Status - Warp Science Residual Guardrail

## Gate

S2-Gate 321: Warp science residual guardrail.

## Completed

- Extended `warp_quality_contract.json` with optional tiled registered science-image residual verification.
- Added guardrail options:
  - `--warp-science-residual-verify`
  - `--warp-science-reference-frame-id`
  - `--max-warp-science-rms`
  - `--max-warp-science-max-abs`
  - `--warp-science-residual-tile-size`
- Residual verification streams registered and coverage FITS tiles, compares only common finite covered pixels, and records mean, mean absolute residual, RMS, maximum absolute residual, and common-valid pixel count.
- Residual thresholds are opt-in and become blocking only when verification or thresholds are supplied.
- Surfaced science residual status and aggregate metrics in JSON, Markdown, guardrails summaries, bundles, and HTML reports.
- Added focused tests for passing and failing residual thresholds.
- Updated `docs/algorithm_sources.md`, `docs/phase2_algorithm_hardening.md`, and `docs/registration_model.md`.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\html_report.py src\glass\report\warp_quality.py tests\test_cli_smoke.py tests\test_warp_quality_contract.py docs\phase2_algorithm_hardening.md docs\registration_model.md docs\algorithm_sources.md

.venv\Scripts\python.exe -m pytest -q tests\test_warp_quality_contract.py tests\test_cli_smoke.py::test_cli_guardrails_warp_quality_thresholds

.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_316_enabled_run --out-dir runs\checkpoints\s2_gate_321_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --require-local-normalization-enabled --min-warp-valid-fraction 1.0 --max-warp-skipped-frames 2 --require-warp-artifacts --require-warp-all-registered --warp-pixel-verify --warp-pixel-verify-tile-size 8 --warp-pixel-tolerance 0 --warp-science-residual-verify --max-warp-science-rms 0.0 --max-warp-science-max-abs 0.0 --warp-science-residual-tile-size 8 --pixel-verify --pixel-verify-tile-size 8

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_321_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 5 passed.
- Full pytest: 750 passed in 32.79 s.
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

- `runs/checkpoints/s2_gate_321_doctor.json`
- `runs/checkpoints/s2_gate_321_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_321_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_321_guardrails/warp_quality_contract.json`
- `runs/checkpoints/s2_gate_321_guardrails/warp_quality_contract.md`
- `runs/checkpoints/s2_gate_321_guardrails/report.html`

## Warp Science Residual Result

- Contract status: passed.
- Science residual verification enabled: true.
- Reference frame: `F000010`.
- Verified output count: 1.
- Failed output count: 0.
- Common valid pixels: 576.
- Mean residual: 0.0.
- Mean absolute residual: 0.0.
- RMS residual: 0.0.
- Maximum absolute residual: 0.0.
- RMS threshold: 0.0.
- Maximum absolute threshold: 0.0.
- Tile size: 8.

## Known Limitations

- The checkpoint run has one accepted warp output, so the residual validates the streaming path and reference self-consistency but not a multi-frame real registration residual distribution.
- Residuals are internal GLASS registered-output consistency checks; they are not PixInsight-equivalence claims.
- This gate does not change registration, interpolation, integration, CUDA kernels, runtime defaults, package builds, or release artifacts.
- This gate did not rerun the 200-light benchmark; it reused the existing S2-Gate 316 enabled run for deterministic guardrail validation.

## Next Step

- Continue correctness hardening by running the residual contract on a multi-frame synthetic warp fixture, or continue throughput hardening by adding a resident runtime regression contract.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated run artifacts and synthetic/checkpoint outputs.
- Input image directories were not modified.
