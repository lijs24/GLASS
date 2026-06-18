# S2-Gate 295 Status: Default Promotion StackEngine Runtime Default Guard

## Gate

S2-Gate 295: Default Promotion StackEngine Runtime Default Guard

## Completed Work

- Extended `glass default-promotion-manifest` so resident CUDA default promotion
  requires the S2-Gate 294 StackEngine runtime-default handoff.
- Added default-promotion checks for:
  - `acceptance_stack_engine_runtime_default_handoff_passed`
  - `pipeline_stack_engine_runtime_default_handoff_passed`
- Surfaced acceptance and direct pipeline runtime-default status, check state,
  master counts, legacy master counts, failed master/output counts, explicit
  CUDA fast-path counts, and failed row details in JSON evidence.
- Added Markdown summary lines for acceptance-side and pipeline-side
  StackEngine runtime-default readiness.
- Added focused tests covering ready evidence, stale/missing runtime-default
  evidence, acceptance-side legacy master drift, pipeline-side failed output
  drift, and CLI Markdown output.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.venv\Scripts\ruff.exe check src\glass\report\default_promotion_manifest.py tests\test_default_promotion_manifest.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_default_promotion_manifest.py`
- generated Gate295 ready/failed default-promotion checkpoint artifacts
- `.venv\Scripts\ruff.exe check src tests`
- `.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- CUDA capability probe through `glass.capabilities` and `glass.gpu.device`

## Test Results

- Targeted ruff: passed.
- Targeted pytest: `18 passed in 0.32s`.
- Full ruff: passed.
- Full pytest: `682 passed in 34.13s`.
- `git diff --check`: passed with CRLF conversion warnings only.

## CUDA Status

- CUDA extension importable: true.
- CUDA available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.
- Reported CUDA feature flags include smoke add, calibration, warp, local
  normalization, resident stack, resident weighting, and resident sigma
  rejection support.

## Artifacts

- `runs/checkpoints/s2_gate_295_default_promotion_ready.json`
- `runs/checkpoints/s2_gate_295_default_promotion_ready.md`
- `runs/checkpoints/s2_gate_295_default_promotion_acceptance_runtime_default_failed.json`
- `runs/checkpoints/s2_gate_295_default_promotion_acceptance_runtime_default_failed.md`
- `runs/checkpoints/s2_gate_295_default_promotion_pipeline_runtime_default_failed.json`
- `runs/checkpoints/s2_gate_295_default_promotion_pipeline_runtime_default_failed.md`
- `runs/checkpoints/s2_gate_295_fixtures/`
- `runs/checkpoints/s2_gate_295_status.md`

## Known Limitations

- This gate is a default-promotion evidence guard only. It does not change image
  math, CUDA kernels, runtime defaults, package artifacts, GitHub release
  publication behavior, or benchmark outputs.
- No 200-light real-data benchmark rerun was performed for this gate because
  the change is report and promotion-contract scoped.
- The resident CUDA default candidate remains subject to later gates that carry
  this runtime-default evidence through the Windows release matrix and final
  publish preflight.

## Next Step

S2-Gate 296 should carry the default-promotion StackEngine runtime-default
guard into `glass windows-release-matrix`, so Windows CUDA release readiness
cannot drop the runtime-default evidence after default-promotion generation.

## Clean-Room Compliance

- This gate consumed only GLASS-owned release-decision, Phase 2 status, and
  generated checkpoint artifacts.
- No PixInsight/WBPP/PJSR implementation source, proprietary scripts, or
  external implementation code were read, summarized, copied, or modified.
- User image directories were not modified.
