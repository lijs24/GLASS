# S2-Gate 259 Status

- Gate: S2-Gate 259
- Scope: CPU Integration Rejection Baseline Unification
- Status: green
- Date: 2026-06-18

## Completed

- Added `glass.engine.rejection` as the shared CPU rejection statistics module.
- Routed CPU StackEngine rejection center/scale estimation through the shared module.
- Routed legacy `glass.cpu.integration.weighted_integrate_stack` sigma/winsorized rejection through the same shared module.
- Unified legacy CPU `winsorized_sigma` with the S2-Gate 258 median/IQR-guided winsorized baseline.
- Added a low-sample CPU integration regression where ordinary `sigma_clip` keeps an outlier but `winsorized_sigma` rejects it.
- Updated Phase 2 planning docs and the algorithm source ledger.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cpu_integration.py tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\rejection.py src\\glass\\engine\\stack_engine.py src\\glass\\cpu\\integration.py tests\\test_cpu_integration.py tests\\test_stack_engine.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Focused CPU integration and StackEngine tests: 24 passed.
- Ruff check: passed.
- Full pytest: 593 passed.

## CUDA

- CUDA was not probed in this gate.
- This gate unifies CPU baseline semantics only and does not modify CUDA kernels, resident CUDA runtime behavior, package builds, package uploads, or benchmark outputs.

## Known Limitations

- Resident CUDA `winsorized_sigma` still reports the existing two-stage mean/std winsorized approximation; parity with the new shared CPU baseline remains future work.
- The shared robust statistics are project-defined clean-room baseline semantics, not a claim of exact equivalence to any external stacking implementation.
- No 200-light real-data benchmark was rerun in this gate.

## Next Step

- Add resident/CUDA parity evidence for the hardened winsorized rejection semantics, or explicitly gate/report the current resident approximation until the CUDA kernel is updated.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS-owned in-memory synthetic tests and project-defined robust statistics only.
- No PixInsight/WBPP/PJSR source code or external proprietary implementation details were read, copied, summarized, or reworked.
