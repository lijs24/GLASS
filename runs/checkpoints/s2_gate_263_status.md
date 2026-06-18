# S2-Gate 263 Status

- Gate: S2-Gate 263
- Scope: Hardened Winsorized Runtime Guardrails
- Status: green
- Date: 2026-06-18

## Completed

- Promoted the hardened resident winsorized frame limit into `RESIDENT_WINSORIZED_SIGMA_HARDENED_FRAME_LIMIT`.
- Added a resident winsorized runtime contract helper that records mode, implementation, frame count, frame limit, stack-dispatch requirement, and pass/fail booleans.
- Validated `resident_winsorized_mode=hardened_cpu_parity` before resident stack allocation, so over-limit groups fail with a clear error instead of a later native failure.
- Recorded the resident winsorized runtime contract in both `resident_artifacts.json` dispatch metadata and each `integration_results.json` output row.
- Added CPU-only helper tests for over-limit hardened mode and non-applicable fast-approx mode.
- Extended the small CUDA resident hardened winsorized run test to assert the emitted capacity/dispatch contract.
- Updated Phase 2 planning docs and the algorithm source ledger.

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\engine\rejection.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_rejects_over_limit tests\test_resident_cuda_run.py::test_resident_fast_winsorized_contract_does_not_apply_hardened_limit tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- CUDA probe via `glass_cuda.cuda_available()`, `glass_cuda.list_devices()`, and `ResidentCalibratedStack` method checks.

## Test Results

- Ruff check: passed.
- Focused guardrail and hardened runtime tests: 3 passed.
- Resident contract/CUDA stack/resident run tests: 89 passed.
- Full pytest: 599 passed.

## CUDA

- CUDA available: true.
- Native backend loaded: true.
- Hardened resident method available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.

## Known Limitations

- The guardrail documents and enforces the current 256-frame hardened prototype limit; it does not raise that limit.
- `fast_approx` remains the default resident winsorized mode.
- `hardened_cpu_parity` remains stack-dispatch only and opt-in.
- No CUDA kernel optimization, fused-matrix hardened parity, tile-local hardened parity, 200-light benchmark, package build/upload, or release update was performed in this gate.

## Next Step

- Optimize or replace the per-pixel local-sort hardened CUDA prototype so it can be benchmarked on the 200-light dataset without risking a large runtime regression.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS-owned runtime contracts, JSON artifact schemas, and synthetic CUDA tests only.
- No PixInsight/WBPP/PJSR source code or proprietary implementation details were read, copied, summarized, or reworked.
