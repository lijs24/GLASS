# S2-Gate 125 Status: Residual Frame-Family Audit

## Gate

S2-Gate 125: Residual Frame-Family Audit.

## Completed

- Added `glass compare-frame-family`.
- The command consumes a `compare-tile-replay` JSON artifact and a GLASS run directory.
- It selects focus frames by explicit frame ids or an id range.
- It selects neighboring positive-weight controls unless explicit controls are provided.
- It joins replay tile ranks/deltas, frame accounting weights, agreement warning fields, registration status/RMS, and matrix-derived translation metrics.
- It writes JSON and optional Markdown summaries with focus/control group statistics and focus-minus-control contrasts.
- Added focused tests and CLI help coverage.
- Ran the audit on the S2-Gate 124 all-positive-weight Lanczos3 replay for F000100-F000110 against neighboring controls.

## Real 200-Light Audit Result

Artifact directory:

- `C:\glass_runs\phase2_s2_gate_125_frame_family`

Artifacts:

- `C:\glass_runs\phase2_s2_gate_125_frame_family\agr0p5_f100_f110_family_audit.json`
- `C:\glass_runs\phase2_s2_gate_125_frame_family\agr0p5_f100_f110_family_audit.md`

Focus frames:

- F000100, F000101, F000102, F000103, F000104, F000105, F000106, F000107, F000108, F000109, F000110

Control frames:

- F000096, F000097, F000098, F000099, F000111, F000112, F000113, F000114, F000115

Key findings:

- Top focus frame: F000102.
- Focus frames downweighted: 11 / 11.
- Control frames downweighted: 2 / 9.
- Focus mean agreement score: 0.455105.
- Control mean agreement score: 0.524657.
- Focus mean integration weight: 0.910211.
- Control mean integration weight: 0.992368.
- Focus mean registration RMS: 0.655819 px.
- Control mean registration RMS: 0.615895 px.
- Focus mean translation_x: 44.878904 px.
- Control mean translation_x: 5.318185 px.
- Focus mean translation_y: 6.616153 px.
- Control mean translation_y: 11.217717 px.
- Focus mean local weighted-delta: 94.781901 ADU.
- Control mean local weighted-delta: 37.799604 ADU.
- Focus minus control local weighted-delta: 56.982297 ADU.

Top ranked focus contributors:

- F000102: weighted delta mean 101.948629 ADU, weight 0.885900, tx 49.407448, ty 5.644435.
- F000100: weighted delta mean 100.281054 ADU, weight 0.830793, tx 44.873844, ty 5.573986.
- F000105: weighted delta mean 99.195040 ADU, weight 0.939700, tx 51.932159, ty 8.141267.
- F000101: weighted delta mean 98.031171 ADU, weight 0.830232, tx 45.856438, ty 3.502602.
- F000104: weighted delta mean 96.249942 ADU, weight 0.899657, tx 51.003582, ty 9.171472.

Interpretation:

- The S2-Gate 123/124 residual contributor finding is a coherent frame-family signal, not an isolated bad frame.
- The focus family is a distinct motion/registration cluster with much larger positive local contribution than neighboring controls.
- The current linear agreement downweighting recognizes the family as lower agreement, but does not suppress its localized residual contribution enough to satisfy strict p99 comparison.

## Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src/glass/report/compare_frame_family.py src/glass/cli.py tests/test_compare_frame_family.py tests/test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_compare_frame_family.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe compare-frame-family --replay C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_all193_lanczos3_tile_replay.json --run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200 --focus-range-start F000100 --focus-range-end F000110 --control-before 4 --control-after 5 --out C:\glass_runs\phase2_s2_gate_125_frame_family\agr0p5_f100_f110_family_audit.json --markdown C:\glass_runs\phase2_s2_gate_125_frame_family\agr0p5_f100_f110_family_audit.md
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_125_doctor.json
```

## Test Results

- Focused ruff: passed.
- Focused pytest: 3 passed.
- Full ruff: passed.
- Full pytest: 332 passed in 20.54 s.
- Native CUDA build: passed (`ninja: no work to do`).
- Doctor JSON: `runs\checkpoints\s2_gate_125_doctor.json`.

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Recommendation: cuda.

## Known Limitations

- This gate is diagnostic only and does not change registration, weighting, rejection, or integration defaults.
- Neighboring controls are sequence neighbors with positive weights, not a fully matched observational control population.
- The replay artifact is still bounded CPU diagnostic replay, not exact resident CUDA per-frame contribution capture.
- The sigma proxy remains diagnostic and is not a byte-exact winsorized rejection replay.

## Next Step

- S2-Gate 126 should either add exact resident per-frame tile contribution capture for the localized residual tiles, or design a coherent motion-family handling policy that can reduce the F000100-F000110 localized contribution without dropping required benchmark frames.

## Clean-Room

- Compliant.
- The implementation uses GLASS-owned frame accounting, registration results, and replay artifacts only.
- No external proprietary source code was read, copied, summarized, or reworked.
