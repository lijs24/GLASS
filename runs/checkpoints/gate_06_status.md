# Gate 06 Status

Gate: 6 - light calibration streaming

Completed content:

- `gpwbpp run --until-stage calibration` now calibrates light frames tile-by-tile.
- Calibrated FITS outputs are created as empty FITS images and filled by memmap tile writes.
- CUDA backend uses native `gpwbpp_cuda.calibrate_tile_f32` per tile when requested/available.
- CPU backend uses the CPU reference formula per tile.
- `calibration_artifacts.json` records backend, tile size, and tile count per calibrated frame.
- `run_state.json` records completed `master_calibration` and `light_calibration` stages.
- Synthetic generator now supports smaller test image dimensions by adapting star margins.

Commands run:

- `.\\.venv\\Scripts\\python -m pytest -q tests/test_pipeline_fixture.py tests/test_synthetic_generator.py tests/test_gpu_calibration_vs_cpu.py`
- `.\\.venv\\Scripts\\python -m pytest -q`
- `.\\.venv\\Scripts\\gpwbpp synthetic --out runs/gate_06_synth/source --frames 3 --width 36 --height 30 --filter H --known-shift`
- `.\\.venv\\Scripts\\gpwbpp audit --root runs/gate_06_synth/source --out runs/gate_06_synth/audit --backend auto`
- `.\\.venv\\Scripts\\gpwbpp run --plan runs/gate_06_synth/audit/processing_plan.json --out runs/gate_06_synth/run --backend cuda --until-stage calibration --tile-size 10`

Test result:

- Focused tests: `7 passed`
- Full suite: `28 passed`
- CLI validation generated `3` masters and `3` calibrated lights.
- All validated calibrated lights used backend `cuda` with `12` tiles per frame.

CUDA availability:

- Native backend loaded: yes
- CUDA available to GPWBPP: yes
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- CUDA Toolkit: `13.2`

Known limitations:

- Master frames are still held as full arrays during light calibration; Gate 6 only makes light calibration output streaming.
- Resume currently records completed stages and artifacts, but checksum-based skip/reuse is still future work.
- Calibrated cache writing is FITS-only at this gate.

Next step:

- Gate 7: star detection and quality metrics with frame_quality.json and report integration.
- Benchmark target: later compare GPWBPP and PixInsight/WBPP as black boxes on the same small real target dataset.

Clean-room compliance:

- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
- Real data directories were not modified.

