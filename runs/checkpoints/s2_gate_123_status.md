# S2-Gate 123 Status: Bounded Per-Frame Tile Replay

## Gate

S2-Gate 123: Bounded Per-Frame Tile Replay.

## Completed Work

- Added `glass compare-tile-replay`.
- The command consumes a `compare-tile-pack` manifest and a GLASS run directory.
- It discovers the resident master cache from `run_command.txt`, reads only the
  source windows required by each residual tile, applies GLASS master calibration
  semantics, applies registration matrices, and samples bounded destination
  tiles.
- It supports `lowest_weight`, `downweighted`, and `frame_id` frame-selection
  strategies.
- It ranks replayed frames by signed/weighted delta to the final GLASS master
  tile and reports diagnostic sigma-proxy low/high outlier counts.
- Added focused API and CLI tests.
- Updated the Phase 2 gate plan and algorithm-source ledger.

## Real 200-Light Replay

Inputs:

- Tile pack:
  `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`
- Run:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200`
- Discovered master cache:
  `C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache`

Artifacts:

- `C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_lowest32_tile_replay.json`
- `C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_lowest32_tile_replay.md`
- `C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_downweighted73_tile_replay.json`
- `C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_downweighted73_tile_replay.md`
- `C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_all193_tile_replay.json`
- `C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_all193_tile_replay.md`

All-positive-weight replay summary:

| Tile | Selected frames | Replayed frames | Proxy mean delta to master | Top contributor | Top weighted delta mean |
| ---: | ---: | ---: | ---: | --- | ---: |
| 0 | 193 | 193 | 0.161 | F000102 | 102.056 |
| 1 | 193 | 193 | 0.068 | F000102 | 102.414 |
| 2 | 193 | 193 | 0.112 | F000102 | 101.377 |

Top repeated contributors across all three localized residual tiles:

- F000102
- F000100
- F000105
- F000101
- F000106
- F000104
- F000109
- F000110

Interpretation:

- The full positive-weight replay covers all 193 integrated frames.
- The same frame family, especially F000100-F000110, dominates positive local
  delta rankings across all three residual tiles.
- The most extreme low-agreement frames, such as F000061 and F000159, are not
  the dominant local contributors in these tile replays.
- The replayed weighted-mean proxy is close to the final master at whole-tile
  mean level, so the residual is likely local structure around stars/nebulosity
  rather than a simple full-tile background offset.
- This strengthens the next target: compare exact interpolation/rejection
  behavior for that frame family and those tile coordinates.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\compare_tile_replay.py src\glass\cli.py tests\test_compare_tile_replay.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_tile_replay.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe compare-tile-replay --tile-pack "C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json" --run "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200" --filter H --out "C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_lowest32_tile_replay.json" --markdown "C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_lowest32_tile_replay.md" --frame-strategy lowest_weight --max-frames 32
.\.venv\Scripts\glass.exe compare-tile-replay --tile-pack "C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json" --run "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200" --filter H --out "C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_downweighted73_tile_replay.json" --markdown "C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_downweighted73_tile_replay.md" --frame-strategy downweighted --max-frames 0
.\.venv\Scripts\glass.exe compare-tile-replay --tile-pack "C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json" --run "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200" --filter H --out "C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_all193_tile_replay.json" --markdown "C:\glass_runs\phase2_s2_gate_123_tile_replay\agr0p5_all193_tile_replay.md" --frame-strategy frame_id --max-frames 0
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_123_doctor.json
```

## Test Result

- Focused ruff: passed.
- Focused pytest: 3 passed.
- Full ruff: passed.
- Full pytest: 329 passed in 24.26 s.
- Native CUDA build: passed; Ninja reported no work to do.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs\checkpoints\s2_gate_123_doctor.json`.

## Known Limitations

- This gate is diagnostic only and does not change registration, local
  normalization, rejection, weighting, or integration defaults.
- The replay path currently uses CPU bilinear sampling, while the resident CUDA
  benchmark used Lanczos3. This is useful attribution evidence, not a byte-exact
  resident replay.
- The sigma proxy is recomputed from replayed frames and is not an exact replay
  of the resident winsorized sigma implementation.
- The replay uses existing GLASS registration matrices and master calibration
  cache; it does not re-run star detection or registration.

## Next Step

S2-Gate 124 should add either exact CPU Lanczos3 replay parity for these tile
coordinates or a native resident tile-capture mode so F000100-F000110 can be
checked against the exact interpolation/rejection path before changing any
agreement or rejection policy.

## Clean-Room Compliance

This gate uses only GLASS-generated artifacts, GLASS input paths, and
user-generated external reference products. It does not read, copy, summarize,
or rework proprietary implementation source code.
