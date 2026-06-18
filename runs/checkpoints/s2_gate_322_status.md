# S2-Gate 322 Status - Standalone Warp Quality Contract CLI

## Gate

S2-Gate 322: Standalone warp quality contract CLI.

## Completed

- Added `glass warp-quality-contract`.
- The command writes `warp_quality_contract.json` and optional Markdown without requiring the broader `glass guardrails` bundle.
- The command reuses the same contract builder as guardrails, covering:
  - artifact readiness
  - all-registered coverage
  - valid-fraction threshold
  - skipped-frame threshold
  - coverage/DQ pixel verification
  - registered science residual verification
- Added `--fail-on-failed` for CI/checkpoint use.
- Added CLI smoke coverage for help, passing standalone contract generation, Markdown output, and injected valid-pixel drift failure.
- Documented S2-Gate 322 in `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\cli.py tests\test_cli_smoke.py docs\phase2_algorithm_hardening.md

.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_help_commands tests\test_cli_smoke.py::test_cli_warp_quality_contract_command

.venv\Scripts\python.exe -m glass.cli warp-quality-contract --run runs\checkpoints\s2_gate_316_enabled_run --out runs\checkpoints\s2_gate_322_warp_quality_contract.json --markdown runs\checkpoints\s2_gate_322_warp_quality_contract.md --min-valid-fraction 1.0 --max-skipped-frames 2 --require-artifacts --require-all-registered --pixel-verify --pixel-verify-tile-size 8 --pixel-tolerance 0 --science-residual-verify --max-science-rms 0.0 --max-science-max-abs 0.0 --science-residual-tile-size 8 --fail-on-failed

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_322_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 2 passed.
- Full pytest: 751 passed in 33.26 s.
- Standalone warp quality contract: passed.

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

- `runs/checkpoints/s2_gate_322_doctor.json`
- `runs/checkpoints/s2_gate_322_warp_quality_contract.json`
- `runs/checkpoints/s2_gate_322_warp_quality_contract.md`

## Contract Result

- Contract status: passed.
- Required: true.
- Output count: 1.
- Skipped count: 2.
- Artifact-ready count: 1.
- Pixel-verified output count: 1.
- Pixel failed output count: 0.
- Science residual verified output count: 1.
- Science residual failed output count: 0.
- Science residual reference frame: `F000010`.
- Science residual max RMS: 0.0.
- Science residual max absolute: 0.0.

## Known Limitations

- This gate exposes the existing warp quality contract as a standalone command; it does not add new image math.
- The checkpoint run has one accepted warp output, so the residual validates command plumbing and reference self-consistency rather than a multi-frame residual distribution.
- This gate does not change CUDA kernels, runtime defaults, package builds, release artifacts, or real-data benchmark outputs.
- This gate did not rerun the 200-light benchmark.

## Next Step

- Add multi-frame synthetic/fixture warp residual validation, or attach the standalone warp contract to higher-level acceptance/phase2 status evidence.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated run artifacts and checkpoint outputs.
- Input image directories were not modified.
