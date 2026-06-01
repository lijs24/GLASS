# S2-Gate 126 Status: Resident Tile Capture Parity

## Gate

S2-Gate 126: Resident Tile Capture Parity.

## Completed

- Added native `ResidentCalibratedStack.download_frame_tile(index, x0, y0, x1, y1)`.
- Added the Python wrapper method `glass_cuda.ResidentCalibratedStack.download_frame_tile`.
- Added `glass resident-tile-capture`.
- The command rebuilds selected positive-weight frames into a small resident CUDA stack, applies the run's master calibration cache, applies registration matrices with resident CUDA warp kernels, and downloads only localized post-warp tiles.
- The command writes JSON and optional Markdown summaries, and can optionally write captured FITS tiles.
- The command can join an existing `compare-tile-replay` artifact and compare resident CUDA captured weighted-delta means against bounded CPU Lanczos3 replay.
- Added CUDA tests for native tile download and small resident capture parity.
- Updated Phase 2 gate planning and algorithm-source attribution docs.

## Real 200-Light Diagnostic

Artifact directory:

- `C:\glass_runs\phase2_s2_gate_126_resident_tile_capture`

Artifacts:

- `C:\glass_runs\phase2_s2_gate_126_resident_tile_capture\agr0p5_f100_f110_resident_tile_capture.json`
- `C:\glass_runs\phase2_s2_gate_126_resident_tile_capture\agr0p5_f100_f110_resident_tile_capture.md`
- `C:\glass_runs\phase2_s2_gate_126_resident_tile_capture\capture_tiles\*.fits`

Capture scope:

- Source run: `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200`
- Tile pack: `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`
- CPU replay comparison: `C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_all193_lanczos3_tile_replay.json`
- Frames: F000100-F000110.
- Tiles: top 3 localized residual tiles.
- Captured FITS tiles: 33.
- Resident capture interpolation: Lanczos3.
- Lanczos3 clamping threshold: 0.3.
- Elapsed: 5.248217 s.
- Calibration total from native timings: 0.215601 s.

Tile parity summary:

| tile | frames | resident weighted-delta mean | resident-minus-CPU mean | max abs resident-minus-CPU |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 11 | 95.453647 | -0.000003361 | 0.000045504 |
| 1 | 11 | 94.828904 | -0.000001237 | 0.000016132 |
| 2 | 11 | 94.063143 | -0.000004294 | 0.000034835 |

Top tile-0 resident contributors:

- F000102: resident weighted delta 102.054273 ADU; CPU replay 102.054276 ADU.
- F000100: resident weighted delta 100.217630 ADU; CPU replay 100.217598 ADU.
- F000105: resident weighted delta 99.759313 ADU; CPU replay 99.759315 ADU.
- F000101: resident weighted delta 98.004840 ADU; CPU replay 98.004868 ADU.
- F000106: resident weighted delta 97.365700 ADU; CPU replay 97.365715 ADU.

Interpretation:

- The S2-Gate 123/124 CPU Lanczos3 replay is numerically aligned with resident CUDA calibration plus resident CUDA Lanczos3 warp for the localized residual tiles.
- The F000100-F000110 frame-family finding is not explained by CPU replay interpolation, CPU calibration replay, or missing resident warp clamping.
- The next corrective work should focus on integration/rejection/weighting policy or exact per-frame accepted/rejected contribution inside the winsorized integration kernel.

## Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src/glass/report/resident_tile_capture.py src/glass/cli.py tests/test_resident_tile_capture.py tests/test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_help_commands
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_tile_capture.py
.\.venv\Scripts\glass.exe resident-tile-capture --tile-pack C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json --run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200 --replay C:\glass_runs\phase2_s2_gate_124_lanczos_replay\agr0p5_all193_lanczos3_tile_replay.json --frame-range-start F000100 --frame-range-end F000110 --out-dir C:\glass_runs\phase2_s2_gate_126_resident_tile_capture\capture_tiles --out C:\glass_runs\phase2_s2_gate_126_resident_tile_capture\agr0p5_f100_f110_resident_tile_capture.json --markdown C:\glass_runs\phase2_s2_gate_126_resident_tile_capture\agr0p5_f100_f110_resident_tile_capture.md --max-tiles 3 --write-tiles
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_126_doctor.json
```

## Test Results

- Focused ruff: passed.
- CLI help smoke: passed.
- Native CUDA build: passed.
- Focused CUDA tests: 3 passed.
- Full ruff: passed.
- Full pytest: 335 passed in 20.46 s.
- Final native CUDA build: passed (`ninja: no work to do`).
- Doctor JSON: `runs\checkpoints\s2_gate_126_doctor.json`.

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

- Diagnostic only; no default processing behavior changed.
- Captures selected post-calibration, post-warp resident frame tiles before integration rejection decisions.
- Does not yet capture per-frame accepted/rejected contribution inside the resident winsorized integration kernel.
- Does not replay local normalization; this real diagnostic used a run with local normalization off.
- The command currently reads selected source FITS frames fully before uploading them to the small resident capture stack.

## Next Step

- S2-Gate 127 should target exact per-frame contribution accounting inside winsorized resident integration, or implement a focused family-aware rejection/weighting experiment now that replay and resident capture parity are verified.

## Clean-Room

- Compliant.
- The implementation uses GLASS-owned CUDA kernels, GLASS run artifacts, and user-generated input/output data only.
- No external proprietary source code was read, copied, summarized, or reworked.
