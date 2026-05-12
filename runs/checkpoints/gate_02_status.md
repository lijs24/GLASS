# Gate 02 Status

Gate: 2 - synthetic data and CPU calibration baseline

Completed content:

- `gpwbpp synthetic` generates small controlled FITS datasets with bias, dark, flat, light, hot pixels, gradients, stars, known shifts, and `golden_truth.json`.
- CPU master bias, master dark, and normalized master flat are implemented.
- CPU light calibration supports both `master_dark_includes_bias=true` and `master_dark_includes_bias=false` semantics.
- `docs/calibration_model.md` records the calibration formulas and policy flags.

Commands run:

- `.\\.venv\\Scripts\\gpwbpp synthetic --out runs/gate_02_synthetic --frames 6 --width 48 --height 40 --filter H --known-shift`
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_synthetic_generator.py tests/test_cpu_master_frames.py tests/test_cpu_calibration.py`
- `.\\.venv\\Scripts\\python -m pytest -q`

Test result:

- Gate 2 focused tests: `4 passed`
- Full suite: `16 passed, 7 skipped`
- Skips are CUDA tests because `gpwbpp_cuda` is not built yet.

CUDA availability:

- CUDA extension importable: no
- CUDA available to GPWBPP: no

Known limitations:

- Master frame stacking is CPU mean stacking only at this gate.
- Rejection and streaming master-frame generation are future gates.
- Synthetic generator currently prioritizes monochrome H-like data; OSC/CFA is future work.

Next step:

- Gate 3: build an optional `gpwbpp_cuda` extension skeleton or clearly record toolchain blockage.

Clean-room compliance:

- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
- Calibration formulas are independently documented from common astronomical preprocessing semantics.

