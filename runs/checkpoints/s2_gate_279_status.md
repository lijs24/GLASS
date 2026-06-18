# S2-Gate 279 Status: Pipeline Contract Integration Engine Policy Guard

- Gate: S2-Gate 279
- Status: green
- Base commit before gate: `e8c0731 gate-278: make cuda integration fast path explicit`
- Completed at: 2026-06-18

## Completed Content

- Added `integration_default_engine_policy` to `glass pipeline-contract`.
- Non-resident integration artifacts now must carry top-level `integration_engine_policy`, per-output `engine_selection`, and `default_engine=stack_engine_cpu`.
- Non-resident `cuda_streaming_accumulator_fast_path` artifacts pass only when the fast path is explicit through policy opt-in or explicit CUDA backend selection.
- Resident CUDA stack outputs remain exempt from this non-resident guard and continue to be validated by the resident result contract.
- Pipeline-contract JSON now exposes `integration.engine_policy`.
- Pipeline-contract Markdown now includes an Integration Engine Policy section.
- Added focused tests for CPU StackEngine default evidence, explicit non-resident CUDA fast-path acceptance, and implicit non-resident CUDA fast-path rejection.
- Updated Phase 2 gate documentation and algorithm source log.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -c "import json; import glass_cuda as g; print(json.dumps({'cuda_available': bool(g.cuda_available()), 'devices': g.list_devices() if g.cuda_available() else []}, ensure_ascii=False))"`

## Test Results

- Ruff: passed
- `tests/test_pipeline_contract.py`: 20 passed
- `tests/test_pipeline_fixture.py`: 20 passed
- Full pytest: 640 passed in 28.01 s

## CUDA Availability

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Native backend loaded: yes

## Artifacts

- `runs/checkpoints/s2_gate_279_pipeline_contract_engine_policy.json`
- `runs/checkpoints/s2_gate_279_pipeline_contract_engine_policy.md`

The artifact uses temporary synthetic 2x2 FITS integration maps and records both:

- explicit non-resident CUDA fast path: audit passed
- implicit non-resident CUDA fast path: audit failed only at `integration_default_engine_policy`

## Known Limits

- This gate is an audit-contract change only.
- It does not change image math, CUDA kernels, runtime defaults, package builds, or publication handoff behavior.
- It does not rerun the 200-light real-data benchmark.
- Existing old non-resident artifacts without Gate278 engine-selection metadata will fail this new contract, which is intentional for current Phase 2 readiness artifacts.

## Next Step

- Continue to the next Phase 2 hardening gate, likely carrying the integration engine-policy evidence into downstream acceptance/status/publication artifacts so stale benchmark handoffs cannot drop this default-route guard.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- No external implementation behavior was used.
- No user image directory was read or modified.
- All evidence was generated from GLASS-owned synthetic fixtures and GLASS-owned audit code.
