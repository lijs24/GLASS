# Gate 07 Status

Gate: 7 - star detection and quality metrics

Completed content:

- Added `measure_calibrated_quality()` to produce `frame_quality.json` from calibrated cache outputs.
- Added automatic reference selection using max star count, then max weight, then min background RMS.
- Added quality-stage support to `gpwbpp run --until-stage quality`.
- Added frame quality table and selected reference display to HTML report.
- CPU baseline star detection and metrics are used for this gate; CUDA pixel kernels from earlier gates remain available for calibration.

Commands run:

- `.\\.venv\\Scripts\\python -m pytest -q tests/test_cpu_star_detect.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python -m pytest -q`
- `.\\.venv\\Scripts\\gpwbpp synthetic --out runs/gate_07_synth/source --frames 4 --width 40 --height 40 --filter H --known-shift`
- `.\\.venv\\Scripts\\gpwbpp audit --root runs/gate_07_synth/source --out runs/gate_07_synth/audit --backend auto`
- `.\\.venv\\Scripts\\gpwbpp run --plan runs/gate_07_synth/audit/processing_plan.json --out runs/gate_07_synth/run --backend cuda --until-stage quality --tile-size 10`
- `.\\.venv\\Scripts\\gpwbpp report --run runs/gate_07_synth/run --manifest runs/gate_07_synth/audit/manifest.json --plan runs/gate_07_synth/audit/processing_plan.json --out runs/gate_07_synth/report.html`

Test result:

- Focused tests: `6 passed`
- Full suite: `30 passed`
- CLI validation generated quality rows for `4` calibrated lights and selected reference `F000010`.

CUDA availability:

- Native backend loaded: yes
- CUDA available to GPWBPP: yes
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- CUDA Toolkit: `13.2`

Known limitations:

- Star detection and FWHM/eccentricity are CPU baseline approximations at this gate.
- CUDA star-detection kernels are still future work.
- Synthetic validation found one bright star per small frame with the current conservative detector threshold.

Next step:

- Gate 8: registration results from detected stars and known synthetic shifts.
- Benchmark target: later compare GPWBPP and PixInsight/WBPP black-box runtime on the same small real target dataset.

Clean-room compliance:

- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
- PixInsight remains a future black-box benchmark only.

