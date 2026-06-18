# S2-Gate 258 Status

- Gate: S2-Gate 258
- Scope: Winsorized Sigma Stack Rejection Semantics
- Status: green
- Date: 2026-06-18

## Completed

- Hardened CPU StackEngine `winsorized_sigma` so it uses a distinct robust rejection path instead of sharing the ordinary sigma scale behavior.
- The first winsorization bounds now use a median center and IQR-derived sigma scale, with standard deviation only as a zero-scale fallback.
- The final rejection thresholds use mean/std measured after winsorization.
- Added `rejection_scale_estimator` to StackEngine metrics.
- Added full `rejection_policy` provenance to DQ provenance, including winsorization center/scale/final estimator metadata.
- Added a low-sample outlier regression where ordinary sigma keeps the outlier but `winsorized_sigma` rejects it while preserving result-contract checks.
- Updated Phase 2 planning docs and the algorithm source ledger.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_stack_engine.py tests\\test_stack_engine_result_contract.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\engine\\stack_engine.py tests\\test_stack_engine.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Focused StackEngine tests: 18 passed.
- Ruff check: passed.
- Full pytest: 592 passed.

## CUDA

- CUDA was not probed in this gate.
- This gate modifies the CPU StackEngine baseline only and does not modify CUDA kernels, resident CUDA runtime behavior, package builds, package uploads, or benchmark outputs.

## Known Limitations

- CUDA/resident parity for the hardened `winsorized_sigma` semantics remains future work.
- The robust IQR path is a project-defined clean-room baseline, not a claim of exact equivalence to any external stacking implementation.
- No 200-light real-data benchmark was rerun in this gate.

## Next Step

- Carry the hardened `winsorized_sigma` semantics into CUDA/resident integration parity work or add artifact/report surfacing for rejection estimator provenance before the next benchmark gate.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS-owned in-memory synthetic tests and project-defined robust statistics only.
- No PixInsight/WBPP/PJSR source code or external proprietary implementation details were read, copied, summarized, or reworked.
