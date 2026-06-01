# S2-Gate 124 Status: Lanczos3 Replay Parity

## Gate

S2-Gate 124: Lanczos3 Replay Parity.

## Completed Work

- Extended `glass compare-tile-replay` with `--replay-interpolation`.
- Supported replay interpolation modes:
  - `bilinear`
  - `lanczos3`
- Implemented vectorized CPU Lanczos3 sampling for bounded residual-tile replay.
- Preserved the S2-Gate 123 source-window, master-cache calibration,
  registration-matrix, frame-selection, and ranking contract.
- Added focused tests covering bilinear and Lanczos3 replay.
- Updated the Phase 2 gate plan and algorithm-source ledger.

## Real 200-Light Lanczos3 Replay

Inputs:

- Tile pack:
  `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`
- Run:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200`

Artifacts:

- `C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_downweighted73_lanczos3_tile_replay.json`
- `C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_downweighted73_lanczos3_tile_replay.md`
- `C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_all193_lanczos3_tile_replay.json`
- `C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_all193_lanczos3_tile_replay.md`
- `C:\glass_runs\phase2_s2_gate_124_lanczos_replay\bilinear_vs_lanczos3_top10_compare.json`

All-positive-weight Lanczos3 replay summary:

| Tile | Selected frames | Replayed frames | Proxy mean delta to master | Top contributor | Top weighted delta mean |
| ---: | ---: | ---: | ---: | --- | ---: |
| 0 | 193 | 193 | 0.15974719588644803 | F000102 | 102.05427551269531 |
| 1 | 193 | 193 | 0.06887001561000944 | F000102 | 102.41472625732422 |
| 2 | 193 | 193 | 0.11224829868960172 | F000102 | 101.37688446044922 |

Bilinear vs Lanczos3 comparison:

| Tile | Top-10 order same? | Bilinear proxy mean | Lanczos3 proxy mean |
| ---: | --- | ---: | ---: |
| 0 | yes | 0.161083 | 0.159747 |
| 1 | yes | 0.067706 | 0.068870 |
| 2 | yes | 0.112329 | 0.112248 |

Shared top-10 contributor family:

- F000102
- F000100
- F000105
- F000101
- F000106/F000104 order remains tile-dependent only after the first four
- F000109
- F000110
- F000103
- F000107

Interpretation:

- The S2-Gate 123 frame-family finding survives closer interpolation parity.
- F000100-F000110 remain the dominant local positive contributors in all three
  residual tiles under Lanczos3 replay.
- The finding is therefore not a bilinear replay artifact.
- This still does not prove byte-exact native CUDA parity, because resident
  rejection and native Lanczos implementation details are not fully replayed in
  Python.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\compare_tile_replay.py src\glass\cli.py tests\test_compare_tile_replay.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_tile_replay.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe compare-tile-replay --tile-pack "C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json" --run "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200" --filter H --out "C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_downweighted73_lanczos3_tile_replay.json" --markdown "C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_downweighted73_lanczos3_tile_replay.md" --frame-strategy downweighted --max-frames 0 --replay-interpolation lanczos3
.\.venv\Scripts\glass.exe compare-tile-replay --tile-pack "C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json" --run "C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200" --filter H --out "C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_all193_lanczos3_tile_replay.json" --markdown "C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_all193_lanczos3_tile_replay.md" --frame-strategy frame_id --max-frames 0 --replay-interpolation lanczos3
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_124_doctor.json
```

## Test Result

- Focused ruff: passed.
- Focused pytest: 4 passed.
- Full ruff: passed.
- Full pytest: 330 passed in 20.62 s.
- Native CUDA build: passed; Ninja reported no work to do.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs\checkpoints\s2_gate_124_doctor.json`.

## Known Limitations

- This gate is diagnostic only and does not change registration, local
  normalization, rejection, weighting, or integration defaults.
- CPU Lanczos3 replay is closer to the resident benchmark interpolation choice,
  but it is still not a byte-exact native CUDA replay.
- The sigma proxy is recomputed from replayed frames and is not an exact replay
  of resident winsorized sigma rejection.
- All-positive-frame Lanczos3 replay is intentionally bounded to three residual
  tiles, but still takes several minutes.

## Next Step

S2-Gate 125 should inspect the F000100-F000110 frame family directly: compare
their registration matrices, agreement scores, local tile residual signs, and
possible rejection classifications against neighboring non-problem frames, then
decide whether the next correction belongs in registration quality, rejection,
or local normalization.

## Clean-Room Compliance

This gate uses only GLASS-generated artifacts, GLASS input paths, GLASS master
caches, and user-generated external reference products. It does not read, copy,
summarize, or rework proprietary implementation source code.
