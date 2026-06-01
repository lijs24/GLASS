# S2-Gate 127 Status: Localized Integration Contribution Audit

- Gate: S2-Gate 127
- Date: 2026-06-01
- Status: green

## Completed

- Added `glass compare-tile-integration`.
- Added localized residual-tile replay through GLASS resident rejection semantics:
  - `none`
  - two-pass mean/std `sigma_clip`
  - two-stage `winsorized_sigma` approximation used by the current resident CUDA path
- Added per-frame accepted/rejected pixel accounting, low/high rejection counts, accepted weighted deltas, normalized contribution, focus/control group summaries, and diagnostic reconstructed-master delta.
- Added focused unit and CLI tests.
- Updated Phase 2 gate plan and algorithm source attribution.

## Real 200-Light Diagnostic Run

- Source run:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200`
- Tile pack:
  `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`
- Output JSON:
  `C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.json`
- Output Markdown:
  `C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.md`
- Scope:
  - 3 localized top residual tiles
  - 193 selected positive-weight frames
  - focus frames F000100-F000110
  - 10 neighboring positive-weight control frames
  - Lanczos3 replay
  - winsorized sigma rejection from `integration_results.json`
- Runtime:
  - 561.4 s diagnostic replay wall time

## Key Findings

- Diagnostic reconstructed tile master matched the actual GLASS master tile:
  - tile 0 mean delta: `-9.4360e-06` ADU
  - tile 1 mean delta: `1.5166e-05` ADU
  - tile 2 mean delta: `5.0622e-05` ADU
  - p99 deltas were about `0.0035` to `0.0041` ADU
- Focus family survived rejection:
  - focus accepted fraction: `0.968598`
  - control accepted fraction: `0.995473`
  - focus high-rejected fraction: `0.031356`
  - control high-rejected fraction: `0.004395`
- Focus family still contributed materially after rejection:
  - focus accepted weighted-delta mean: `91.6515` ADU
  - control accepted weighted-delta mean: `31.5548` ADU
  - focus tile contribution sum mean: `5.4212` ADU
  - control tile contribution sum mean: `1.7340` ADU
  - focus-minus-control contribution mean: `3.6872` ADU
- Top frame remained `F000102` on all three audited tiles.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_tile_integration.py tests\test_cli_smoke.py
.\.venv\Scripts\ruff.exe check src\glass\report\compare_tile_integration.py src\glass\cli.py tests\test_compare_tile_integration.py tests\test_cli_smoke.py
.\.venv\Scripts\glass.exe compare-tile-integration --tile-pack C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json --run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200 --out C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.json --markdown C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.md --filter H --frame-strategy frame_id --max-frames 0 --max-tiles 3 --replay-interpolation lanczos3 --focus-range-start F000100 --focus-range-end F000110 --control-before 5 --control-after 5
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_127_doctor.json
.\.venv\Scripts\glass.exe compare-tile-integration --help
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused tests: `12 passed in 1.43s`
- Full ruff: passed
- Full pytest: `337 passed in 21.06s`
- Native CUDA build: passed, `ninja: no work to do`

## CUDA

- CUDA available: yes
- CUDA wrapper importable: yes
- CUDA native extension loaded: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommendation: cuda
- Doctor artifact:
  `runs/checkpoints/s2_gate_127_doctor.json`

## Known Limitations

- `compare-tile-integration` is a bounded CPU diagnostic replay, not a performance path.
- Tiny numerical drift from native CUDA is expected; the diagnostic validates the local rejection/contribution explanation rather than tracing every CUDA instruction.
- The audit does not change default weighting, registration, local normalization, rejection, or integration behavior.
- The focus/control contrast uses neighboring frame ids, not a physically matched observational control set.

## Next Step

- S2-Gate 128 should implement and benchmark a corrective motion-family policy. The evidence now points away from calibration, interpolation, and warp replay, and toward a policy that handles coherent high-motion frame families before or during weighting/rejection.

## Clean-Room Compliance

- Compliant.
- The gate uses only GLASS code, GLASS-generated artifacts, GLASS input paths, master cache files, registration matrices, and final GLASS output maps.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used.
- Original image directories were treated as read-only.
