# S2-Gate 278 Status: Explicit Non-Resident CUDA Integration Fast Path

## Gate

- Gate: S2-Gate 278
- Status: green
- Scope: non-resident light-integration engine selection policy

## Completed

- Added `IntegrationPolicy.allow_cuda_streaming_accumulator_fast_path`,
  defaulting to `false`.
- Changed non-resident `integrate_registered_frames(..., backend="auto")` so
  CUDA importability no longer silently bypasses `stack_engine_cpu` when
  rejection is `none`.
- Preserved the older non-resident CUDA streaming accumulator fast path only
  when explicitly requested by policy or by `backend="cuda"`.
- Added `integration_engine_policy` to `integration_results.json` and
  per-output `engine_selection` records for audit/report consumers.
- Added synthetic registered-frame tests with a monkeypatched GLASS CUDA module
  proving:
  - `backend=auto` keeps StackEngine as the default when CUDA is available.
  - policy opt-in enables `cuda_streaming_accumulator_fast_path`.
- Added Gate278 planning text in `docs/phase2_algorithm_hardening.md` and the
  clean-room source entry in `docs/algorithm_sources.md`.
- Generated Gate278 policy artifact:
  - `runs/checkpoints/s2_gate_278_integration_engine_policy.json`

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\engine\integration.py src\glass\models.py tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py`
- Generated `runs/checkpoints/s2_gate_278_integration_engine_policy.json` with
  synthetic registered FITS fixtures and a monkeypatched GLASS CUDA integration
  module.
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py tests\test_cpu_integration.py tests\test_stack_engine_contract.py tests\test_pipeline_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused pipeline fixture tests: `20 passed`.
- Related integration/StackEngine/pipeline contract tests: `55 passed`.
- Full suite: `638 passed in 27.81s`.

## CUDA

- CUDA kernels and resident CUDA behavior were not changed by this gate.
- Gate278 policy artifact used a monkeypatched GLASS CUDA integration module to
  prove engine selection without depending on live CUDA.
- Latest Gate276 CUDA evidence reports:
  - CUDA available: `true`
  - Native extension loaded: `true`
  - GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
  - Compute capability: `12.0`
  - VRAM: `97886 MiB`
  - Driver version: `596.21`

## Artifact Result

- `runs/checkpoints/s2_gate_278_integration_engine_policy.json`
  - status: `passed`
  - `auto_default_uses_stack_engine`: `true`
  - `auto_default_result_mean_preserved`: `true`
  - `policy_opt_in_uses_cuda_fast_path`: `true`
  - `policy_opt_in_result_mean_preserved`: `true`
  - default auto reason:
    `stack_engine_default_requires_explicit_cuda_fast_path`
  - policy opt-in reason: `explicit_cuda_fast_path_requested`

## Known Limitations

- This gate changes only the non-resident integration engine-selection policy.
- Resident CUDA integration, CUDA kernels, package artifacts, release state, and
  publication handoff artifacts are unchanged.
- Real-data and 200-light benchmark runs were not repeated.
- Explicit `backend="cuda"` remains an opt-in to the non-resident CUDA streaming
  accumulator fast path when it is eligible.

## Next Step

- Continue hardening actual default-route behavior by auditing whether report,
  pipeline-contract, and acceptance artifacts should require
  `integration_engine_policy.default_engine=stack_engine_cpu` for non-resident
  runs.

## Clean-Room

- This gate used GLASS-owned code, synthetic registered FITS fixtures, and a
  monkeypatched GLASS CUDA integration module.
- No external implementation source, proprietary source, PixInsight/WBPP source,
  user image directories, or input image pixels were read.
- Input image directories were not modified.
