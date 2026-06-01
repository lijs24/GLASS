# S2 Gate 131 Status

## Gate

S2-Gate 131: Resident Tile Contribution Capture

## Completed

- Added `glass resident-tile-contribution`.
- The command rebuilds selected positive-weight frames into a resident CUDA
  stack, applies the run's master calibration cache and registration matrices,
  downloads bounded post-warp resident tile pixels, and computes
  rejection/contribution diagnostics over those captured resident pixels.
- Added per-frame accepted/rejected pixel counts, accepted weighted delta,
  normalized contribution, focus/control summaries, diagnostic reconstructed
  master delta, and capture timing.
- Added focused CUDA-gated tests and CLI help coverage.
- Documented the gate in `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\resident_tile_contribution.py tests\test_resident_tile_contribution.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_tile_contribution.py tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\glass.exe resident-tile-contribution --tile-pack C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json --run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200 --out C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.json --markdown C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.md --frame-strategy frame_id --max-frames 0 --max-tiles 3 --focus-range-start F000100 --focus-range-end F000110 --control-before 5 --control-after 5 --interpolation lanczos3 --rejection winsorized_sigma`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_131_doctor.json`
- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`

## Test Results

- Focused ruff: passed.
- Focused tests: `3 passed in 0.62s`.
- Full ruff: passed.
- Full pytest: `348 passed in 40.20s`.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_131_doctor.json`.

## Real 193-Frame / 3-Tile Capture

- Input run:
  `C:\glass_runs\phase2_s2_gate_119_agreement_downweight_extended\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p5_agrs200`.
- Input tile pack:
  `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`.
- Output JSON:
  `C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.json`.
- Output Markdown:
  `C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.md`.
- Selected frames: 193 positive-weight frames.
- Tiles: 3.
- Capture elapsed: `116.44122040038928 s` recorded inside the artifact.
- End-to-end command wall time: about 154 s.
- Focus family: F000100-F000110.
- Focus contribution mean: `5.421223163604736`.
- Control contribution mean: `1.734009824693203`.
- Focus accepted fraction: `0.9685984848484849`.

## Parity Check Against S2-Gate 127 CPU Replay

- S2-Gate 127 focus contribution mean:
  `5.421224941809972`.
- S2-Gate 131 resident-captured focus contribution mean:
  `5.421223163604736`.
- Difference: approximately `1.8e-6`.
- S2-Gate 127 control contribution mean:
  `1.7340148488680522`.
- S2-Gate 131 resident-captured control contribution mean:
  `1.734009824693203`.
- Top focus contributors remain the same family. Tile examples:
  F000102, F000105, F000100, F000106/F000101.

## Interpretation

This gate confirms that the localized frame-family contribution finding does
not depend on CPU interpolation replay. Captured resident CUDA post-warp tile
pixels reproduce the S2-Gate 127 contribution summary to within tiny numerical
differences. The remaining gap to the external reference should therefore be
investigated at policy level: local rejection/weighting, local normalization,
or exact inside-kernel contribution tracing rather than calibration or CPU
replay error.

## Known Limitations

- Contribution/rejection statistics are computed on the CPU after downloading
  selected resident tiles.
- This is not yet an inside-kernel trace of the native integration kernel.
- Local normalization replay is not implemented in this diagnostic path.
- The 193-frame/3-tile diagnostic is useful but slower than normal resident
  integration because it reads, calibrates, warps, downloads, and analyzes
  every selected frame for auditability.

## Next Step

S2-Gate 132 should add a tile-local policy experiment or native trace that can
alter or report contribution only inside localized tiles, without applying a
global frame-wide multiplier. The S2-Gate 130 sign audit should gate any such
experiment before running a full 200-light benchmark.

## Clean-Room Compliance

Compliant. This gate uses only GLASS CUDA kernels, GLASS master cache files,
GLASS registration matrices, GLASS frame accounting, GLASS comparison tile
manifests, and user-generated reference artifacts. No proprietary
implementation source code was read, copied, summarized, or reworked.
