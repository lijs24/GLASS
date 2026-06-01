# S2-Gate 122 Status: Localized Tile Map Attribution

## Gate

S2-Gate 122: Localized Tile Map Attribution.

## Completed Work

- Added `glass compare-tile-attribution`.
- The command consumes a `compare-tile-pack` manifest and a GLASS run directory.
- It joins each localized residual tile with available integration output maps:
  coverage, weight, DQ, low rejection, and high rejection.
- It joins the same artifact with `frame_accounting.json`, including integrated,
  zero-weight, lowest-weight, and agreement-downweighted frame context.
- It writes JSON and optional Markdown summaries.
- Added focused API and CLI tests.
- Updated the Phase 2 gate plan and algorithm-source ledger.

## Real 200-Light Attribution

Inputs:

- Tile pack:
  `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`
- Run:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200`

Artifacts:

- `C:\glass_runs\phase2_s2_gate_122_tile_attribution\agr0p5_tile_attribution.json`
- `C:\glass_runs\phase2_s2_gate_122_tile_attribution\agr0p5_tile_attribution.md`

Tile map summary:

| Tile | Coverage mean | Coverage min..max | Rejection sample fraction | Low rejection samples | High rejection samples | Weight mean | DQ warp edge | Recommendation |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 192.19298095703124 | 185..193 | 0.004181445818490933 | 98143 | 232412 | 180.09080518428237 | 0 | coverage_variable_tile |
| 1 | 192.03996337890624 | 185..193 | 0.004974283010848446 | 122579 | 270652 | 179.96644323024898 | 0 | coverage_variable_tile |
| 2 | 192.1593603515625 | 185..193 | 0.004355645846826425 | 95839 | 248487 | 180.03987155526877 | 0 | coverage_variable_tile |

Frame accounting summary:

- Total frames: 200.
- Integrated frames: 193.
- Zero-weight frames: 7.
- Agreement-downweighted frames: 73.
- Lowest positive agreement-downweighted frames include:
  F000061 weight 0.0036232011191353465, F000159 weight
  0.12054602464373809, F000090 weight 0.26383411945412594, and F000194
  weight 0.28116921423886115.

Interpretation:

- The top localized residual tiles are not warp-edge regions.
- Rejection fractions are mild, around 0.42% to 0.50% of pre-rejection samples.
- Coverage varies locally from 185 to 193, but the average coverage remains near
  192 in all three tiles.
- Existing output maps do not fully explain the signed residual morphology seen
  in S2-Gate 121 previews.
- The next gate should save or replay bounded per-frame registered tile samples
  for these coordinates to identify which frames and resampling/rejection
  decisions drive the localized negative residuals.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\compare_tile_attribution.py src\glass\cli.py tests\test_compare_tile_attribution.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_tile_attribution.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe compare-tile-attribution --tile-pack "C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json" --run "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200" --filter H --out "C:\glass_runs\phase2_s2_gate_122_tile_attribution\agr0p5_tile_attribution.json" --markdown "C:\glass_runs\phase2_s2_gate_122_tile_attribution\agr0p5_tile_attribution.md" --frame-limit 24
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_122_doctor.json
```

## Test Result

- Focused ruff: passed.
- Focused pytest: 3 passed.
- Full ruff: passed.
- Full pytest: 327 passed in 20.74 s.
- Native CUDA build: passed; Ninja reported no work to do.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs\checkpoints\s2_gate_122_doctor.json`.

## Known Limitations

- This gate is diagnostic only and does not change registration, local
  normalization, rejection, weighting, or integration defaults.
- Existing resident artifacts do not include per-frame registered tile samples,
  so the attribution cannot prove individual frame causality.
- Map-level rejection/coverage summaries are useful for ruling out edge-heavy
  artifacts, but they are not enough to explain the localized signed residuals.

## Next Step

S2-Gate 123 should implement a bounded per-frame tile replay or capture path
for the S2-Gate 121 coordinates, then rank per-frame signed contribution,
coverage validity, rejection classification, and agreement/registration metrics
inside each residual tile.

## Clean-Room Compliance

This gate uses only GLASS-generated artifacts and user-generated external
reference outputs. It does not read, copy, summarize, or rework proprietary
implementation source code.
