# S2-Gate 277 Status: Strict StackEngine Master Calibration Default

## Gate

- Gate: S2-Gate 277
- Status: green
- Scope: master-calibration StackEngine default fallback policy

## Completed

- Added `CalibrationPolicy.allow_legacy_stack_fallback`, defaulting to `false`.
- Changed master bias/dark StackEngine failures to raise by default instead of
  silently falling back to the legacy streaming accumulator.
- Changed flat per-frame StackEngine master fallback to the same strict default:
  legacy raw-flat normalization fallback now requires the explicit policy flag.
- Preserved the old legacy fallback path for diagnostic compatibility runs when
  `allow_legacy_stack_fallback=true`.
- Recorded `legacy_fallback_explicitly_allowed=true` in fallback metrics.
- Added focused tests proving default strict failure and explicit fallback
  preservation.
- Added Gate277 planning text in `docs/phase2_algorithm_hardening.md` and the
  clean-room source entry in `docs/algorithm_sources.md`.
- Generated Gate277 fallback-policy artifact:
  - `runs/checkpoints/s2_gate_277_strict_stack_fallback_policy.json`

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\models.py src\glass\engine\pipeline.py tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py tests\test_cli_smoke.py tests\test_stack_engine_contract.py`
- Generated `runs/checkpoints/s2_gate_277_strict_stack_fallback_policy.json` with a synthetic FITS fixture that forces StackEngine failure and verifies strict/default vs explicit fallback behavior.
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused pipeline fixture tests: `18 passed`.
- Related pipeline/CLI/StackEngine contract tests: `50 passed`.
- Full suite: `636 passed in 26.42s`.

## CUDA

- CUDA was not changed by this gate.
- CUDA availability was not reprobed by a new Phase 2 status artifact in this
  gate.
- Latest Gate276 CUDA evidence reports:
  - CUDA available: `true`
  - Native extension loaded: `true`
  - GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
  - Compute capability: `12.0`
  - VRAM: `97886 MiB`
  - Driver version: `596.21`
  - Windows package recommendation: primary `cuda13`, fallback order
    `cuda13,cuda12,cuda11,cpu`.

## Artifact Result

- `runs/checkpoints/s2_gate_277_strict_stack_fallback_policy.json`
  - status: `passed`
  - strict default raises: `true`
  - strict default writes no output: `true`
  - explicit fallback preserves legacy mean: `true`
  - explicit fallback records policy: `true`

## Known Limitations

- This gate changes fallback policy only; it does not change image math when
  StackEngine succeeds.
- Real-data and 200-light benchmark runs were not repeated.
- Existing plan files that explicitly set `allow_legacy_stack_fallback=true`
  can still request diagnostic legacy fallback; default generated policy keeps
  it disabled.

## Next Step

- Continue reducing actual default-route gaps by auditing other runtime
  fallback surfaces, especially light integration fast paths and any remaining
  calibration/flat normalization downgrade paths.

## Clean-Room

- This gate used only GLASS source code and synthetic FITS fixtures generated
  locally for the fallback-policy artifact.
- No external implementation source, proprietary source, PixInsight/WBPP source,
  user image directories, or input image pixels were read.
- Input image directories were not modified.
