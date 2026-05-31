# S2-Gate 5 Status: Robust Calibration Completion

Date: 2026-05-31

## Gate

S2-Gate 5: robust calibration first pass.

## Completed Content

- Extended `CalibrationPolicy` with:
  - master-frame rejection policy fields
  - overscan/trim fields
  - cosmetic correction fields
  - optional saturation threshold
- Added CPU overscan/trim helper in `src/glass/cpu/calibration.py`.
- Added CPU cosmetic correction in `src/glass/cpu/cosmetic.py` with DQ flags for:
  - `HOT_PIXEL`
  - `COLD_PIXEL`
  - `COSMETIC_CORRECTED`
  - `NO_DATA`
- Master bias/dark/flat StackEngine requests now use the calibration policy's
  master rejection settings and record StackEngine rejection metrics.
- Master flat creation now normalizes each source flat before StackEngine
  combination and records `normalization_stage=per_flat` plus per-flat scalar
  metadata.
- Calibrated-light generation can mark saturation and run cosmetic correction,
  recording DQ summaries and cosmetic metrics per light.
- HTML reports now include calibration policy and master-frame statistics from
  `calibration_artifacts.json`.
- Updated `docs/calibration_model.md` and `docs/algorithm_sources.md`.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_calibration.py tests\test_cpu_master_frames.py tests\test_pipeline_fixture.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_calibration.py tests\test_pipeline_fixture.py tests\test_stack_engine.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q`
- Synthetic representative smoke:
  - generated `runs\s2_gate_05_smoke\synthetic`
  - injected one saturated/hot light pixel
  - generated plan under `runs\s2_gate_05_smoke\plan`
  - edited the copied plan to enable `minmax` master rejection, cosmetic
    correction, and saturation detection
  - ran `glass run` through integration to `runs\s2_gate_05_smoke\run`
  - generated `runs\s2_gate_05_smoke\run\report.html`
- CUDA probe through `.venv\Scripts\python.exe` importing `glass_cuda`.
- `git diff --stat`
- `git status --short`

## Test Result

- Focused calibration tests: `22 passed in 7.08s`
- Focused calibration/StackEngine/CLI tests: `33 passed in 7.25s`
- Full test suite: `212 passed in 13.75s`

## Representative Smoke Result

Smoke run summary:

- Synthetic generation return code: `0`
- Planning audit return code: `0`
- Run return code: `0`
- Wall elapsed including generation, planning, and run: approximately `1.165 s`
- Master rejection recorded: `minmax`
- Flat normalization stage: `per_flat`
- Cosmetic correction enabled: `true`
- Saturated DQ flag observed: `true`
- Hot-pixel DQ flag observed: `true`
- Integration DQ map emitted: `true`
- Report generated with `Master frame statistics`, `DQ/mask summary`, and the
  active `minmax` master rejection policy.

## CUDA Availability

CUDA is available to GLASS in the current environment.

- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Driver version: `596.21`
- Total VRAM: `97886 MiB`
- Multiprocessors: `188`
- Native backend loaded: yes

## Known Limitations

- Overscan/trim is currently a CPU helper and tested first pass. It is not yet
  wired as a tiled pipeline transform for real data runs.
- Cosmetic correction uses a tile-local robust median/MAD scale estimate. More
  camera-aware bad-pixel maps and column defects are later work.
- Master-frame rejection is CPU StackEngine-backed in tile mode. Resident CUDA
  master construction keeps the Phase 1 fast path until CUDA StackEngine parity
  is implemented.
- Per-flat normalization currently supports bias/dark subtraction through the
  existing matching master path; flat-dark specialization remains future work.

## Next Step

Proceed to S2-Gate 6: improved star/PSF quality and weighting, including
stronger star metrics, subframe quality output, and combined weight policy.

## Clean-Room / Independence Status

This gate used standard astronomical calibration equations and robust
statistics. No proprietary PixInsight/WBPP/PJSR source code was read, copied,
summarized, or modified.
