# S2-Gate 320 Status - Warp Pixel Verification Guardrail

## Gate

S2-Gate 320: Warp pixel verification guardrail.

## Completed

- Extended `warp_quality_contract.json` with optional tiled pixel verification of warp coverage and DQ maps.
- Added guardrail options:
  - `--warp-pixel-verify`
  - `--warp-pixel-verify-tile-size`
  - `--warp-pixel-tolerance`
- Pixel verification streams coverage and DQ FITS tiles and compares:
  - reported `valid_pixels`
  - coverage valid-pixel count
  - DQ valid-pixel count
  - DQ `WARP_EDGE` count
  - DQ summary counts
- Preserved default compatibility: coverage/DQ FITS pixels are not scanned unless `--warp-pixel-verify` is supplied.
- Surfaced pixel verification status, count deltas, verified output count, and failed output count in JSON, Markdown, guardrails summaries, bundles, and HTML reports.
- Added focused tests for passing pixel verification and injected valid-pixel drift failure.
- Documented S2-Gate 320 in the Phase 2 hardening notes and registration/warp model notes.

## Commands Run

```powershell
.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\html_report.py src\glass\report\warp_quality.py tests\test_cli_smoke.py tests\test_warp_quality_contract.py docs\phase2_algorithm_hardening.md docs\registration_model.md

.venv\Scripts\python.exe -m pytest -q tests\test_warp_quality_contract.py tests\test_cli_smoke.py::test_cli_guardrails_warp_quality_thresholds tests\test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report

.venv\Scripts\python.exe -m glass.cli guardrails --run runs\checkpoints\s2_gate_316_enabled_run --out-dir runs\checkpoints\s2_gate_320_guardrails --expected-integration-engine stack_engine_cpu --require-stack-default-ready --require-local-normalization-enabled --min-warp-valid-fraction 1.0 --max-warp-skipped-frames 2 --require-warp-artifacts --require-warp-all-registered --warp-pixel-verify --warp-pixel-verify-tile-size 8 --warp-pixel-tolerance 0 --pixel-verify --pixel-verify-tile-size 8

.venv\Scripts\python.exe -m glass.cli doctor --allow-cpu-only --json runs\checkpoints\s2_gate_320_doctor.json

.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused pytest: 5 passed.
- Full pytest: 749 passed in 33.00 s.
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

- `runs/checkpoints/s2_gate_320_doctor.json`
- `runs/checkpoints/s2_gate_320_guardrails/guardrails_summary.json`
- `runs/checkpoints/s2_gate_320_guardrails/acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_320_guardrails/warp_quality_contract.json`
- `runs/checkpoints/s2_gate_320_guardrails/warp_quality_contract.md`
- `runs/checkpoints/s2_gate_320_guardrails/report.html`

## Warp Pixel Verification Result

- Contract status: passed.
- Pixel verification enabled: true.
- Pixel-verified output count: 1.
- Pixel failed output count: 0.
- Pixel max delta: 0.
- Reported valid pixels: 576.
- Coverage valid pixels: 576.
- DQ valid pixels: 576.
- DQ `WARP_EDGE` pixels: 0.
- Expected `WARP_EDGE` pixels from invalid coverage: 0.
- Verification tile size: 8.
- Tolerance: 0.

## Known Limitations

- Pixel verification scans coverage and DQ diagnostics only; it does not compare registered science pixels against a reference image.
- DQ summary `warp_edge` is optional when there are no warp-edge pixels, matching the existing sparse DQ summary convention.
- This gate does not change interpolation math, registration math, CUDA kernels, runtime defaults, package builds, or release artifacts.
- This gate did not rerun the 200-light benchmark; it reused the existing S2-Gate 316 enabled run for deterministic guardrail validation.

## Next Step

- Continue Phase 2 hardening by adding registered science-image residual checks or resident runtime regression contracts, depending on whether the next risk target is correctness or throughput.

## Clean-Room Compliance

- No PixInsight WBPP/PJSR source was read, copied, summarized, or reworked.
- This gate used only GLASS-generated run artifacts and synthetic/checkpoint outputs.
- Input image directories were not modified.
