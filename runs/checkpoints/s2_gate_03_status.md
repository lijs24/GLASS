# S2-Gate 3 Status: StackEngine Pipeline Integration

Date: 2026-05-31

## Gate

S2-Gate 3: wire StackEngine into master frame creation and light integration
while preserving fallback paths.

## Completed Content

- Updated `src/glass/engine/pipeline.py` so CPU master bias, dark, and raw flat
  stacking use `CPUStackEngine` by default.
- Preserved the legacy streaming mean master path as fallback if the StackEngine
  path fails.
- Added master metadata fields:
  - `tile_stack_mode`
  - `stack_engine_enabled`
  - `stack_engine_fallback_reason`
- Updated `src/glass/engine/integration.py` so non-resident CPU integration uses
  `CPUStackEngine` for mean/weighted mean, coverage, weight, and low/high
  rejection maps.
- Preserved the CUDA `rejection=none` streaming accumulator fast path to protect
  the Phase 1 200-light performance baseline until a CUDA StackEngine path is
  implemented.
- Added integration output metadata:
  - `stack_engine_enabled`
  - `stack_engine_metrics`
  - `stack_engine_rejection_method`
- Updated `tests/test_pipeline_fixture.py` for the new default StackEngine
  path, master equivalence to legacy streaming output, and explicit fallback
  behavior under forced StackEngine failure.
- Updated `docs/algorithm_sources.md` with the S2-Gate 3 migration record.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py tests\test_stack_engine.py`
- `.venv\Scripts\python.exe -m pytest -q`
- Synthetic representative smoke:
  - generated `runs\s2_gate_03_smoke\synthetic`
  - ran `audit` to `runs\s2_gate_03_smoke\run`
  - backend: `cpu`
  - tile size: `12`
  - integration rejection: `winsorized_sigma`
- CUDA probe through `.venv\Scripts\python.exe` importing `glass_cuda`.
- `git diff --stat`
- `git status --short`

## Test Result

- Focused pipeline/StackEngine tests: `21 passed in 5.35s`
- Full test suite: `206 passed in 11.00s`

## Representative Smoke Result

- Synthetic audit elapsed: approximately `0.480 s` including dataset generation
  and audit.
- `run_timing.json` total staged elapsed: `0.4198035995941609 s`
- Calibration masters in
  `runs\s2_gate_03_smoke\run\calibration_artifacts.json` report:
  - `tile_stack_mode`: `stack_engine_cpu`
  - `stack_engine_enabled`: `true`
  - `stack_engine_fallback_reason`: `null`
- Integration in `runs\s2_gate_03_smoke\run\integration_results.json` reports:
  - `tile_stack_mode`: `stack_engine_cpu`
  - `stack_engine_enabled`: `true`
  - `stack_engine_rejection_method`: `winsorized_sigma`

## CUDA Availability

CUDA is available to GLASS in the current environment.

- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Driver version: `596.21`
- Total VRAM: `97886 MiB`
- Multiprocessors: `188`
- Native backend loaded: yes

## Known Limitations

- The resident CUDA path is not yet StackEngine-backed. It remains on the Phase
  1 fast path to avoid unmeasured regressions in the 200-light benchmark.
- The CPU StackEngine currently materializes output maps in memory. It does not
  load all input frames at once, but the final master/maps are held as arrays in
  this reference path.
- Master flat normalization still uses the existing exact-median scratch path
  after raw flat stacking.
- CUDA parity for StackEngine maps and rejection is a future gate.

## Next Step

Proceed to S2-Gate 4: formal DQ/mask propagation across calibration, warp,
local normalization, and integration, including diagnostic summaries and
optional map outputs.

## Clean-Room / Independence Status

This migration used project-owned StackEngine interfaces and existing GLASS
pipeline behavior. No proprietary PixInsight/WBPP/PJSR source code was read,
copied, summarized, or modified.
