# S2-Gate 262 Status

- Gate: S2-Gate 262
- Scope: Opt-In Hardened Winsorized Resident Runtime
- Status: green
- Date: 2026-06-18

## Completed

- Added `--resident-winsorized-mode` to `glass run` and `glass audit`.
- Kept the default mode as `fast_approx` to preserve the current resident CUDA throughput path.
- Added opt-in `hardened_cpu_parity` routing for resident stack-dispatch `winsorized_sigma`, calling `ResidentCalibratedStack.integrate_hardened_winsorized_sigma`.
- Made resident `auto` dispatch select stack integration for hardened winsorized mode.
- Added explicit errors for unsupported hardened combinations with fused-matrix integration and tile-local policy application.
- Extended resident rejection descriptors and resident result contracts so both default fast-approx semantics and opt-in hardened CPU-parity semantics are auditable.
- Added CPU-only contract coverage for the hardened descriptor.
- Added a small CUDA resident FITS run test comparing hardened runtime master, weight, coverage, low rejection, and high rejection maps against the CPU `weighted_integrate_stack(..., rejection="winsorized_sigma")` baseline.
- Updated Phase 2 planning docs and the algorithm source ledger.

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\engine\rejection.py src\glass\report\resident_result_contract.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_result_contract.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_result_contract.py::test_resident_result_contract_accepts_hardened_winsorized_parity_descriptor tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_result_contract.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- CUDA probe via `glass_cuda.cuda_available()`, `glass_cuda.list_devices()`, and `ResidentCalibratedStack` method checks.

## Test Results

- Ruff check: passed.
- Focused hardened descriptor/runtime tests: 2 passed.
- Resident contract/CUDA stack/resident run tests: 87 passed.
- Full pytest: 597 passed.

## CUDA

- CUDA available: true.
- Native backend loaded: true.
- Hardened resident method available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.

## Known Limitations

- `fast_approx` remains the default resident winsorized mode.
- `hardened_cpu_parity` is an opt-in correctness path and is not yet performance tuned.
- The hardened CUDA prototype remains limited to at most 256 resident frames per native call.
- Hardened mode currently requires resident stack dispatch.
- Fused-matrix integration, tile-local policy application, and matrix-warped hardened parity remain future gates.
- No 200-light real-data benchmark, package build, package upload, GitHub release, or release README update was performed in this gate.

## Next Step

- Optimize or extend the hardened winsorized CUDA path beyond the per-pixel local-sort prototype, then benchmark against the 200-light dataset before considering a default switch.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS-owned rejection formulas, GLASS native CUDA methods, GLASS JSON contracts, and synthetic FITS tests only.
- No PixInsight/WBPP/PJSR source code or proprietary implementation details were read, copied, summarized, or reworked.
