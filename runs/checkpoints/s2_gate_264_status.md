# S2-Gate 264 Status

- Gate: S2-Gate 264
- Scope: Hardened Winsorized Timing Surface
- Status: green
- Date: 2026-06-18

## Completed

- Added `ResidentCalibratedStack.integrate_hardened_winsorized_sigma_timed` to the Python CUDA compatibility wrapper.
- The timed wrapper records timing model, native method, rejection mode, resident winsorized mode, frame count, image shape, pixel count, sigma thresholds, download/sync inclusion, and total wall time.
- Resident runtime now uses the timed wrapper for opt-in hardened winsorized stack-dispatch integration.
- `resident_artifacts.json` dispatch metadata and each `integration_results.json` output row now include `hardened_winsorized_timing_s`.
- Resident stage timing now includes `resident_hardened_winsorized_native`.
- Extended CUDA wrapper and resident runtime tests to assert timing metadata while preserving CPU/GPU numerical parity checks.
- Updated Phase 2 planning docs and the algorithm source ledger.

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_matches_cpu_baseline tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_resident_result_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- CUDA probe via `glass_cuda.cuda_available()`, `glass_cuda.list_devices()`, and timed method availability checks.

## Test Results

- Ruff check: passed.
- Focused timed hardened CUDA tests: 2 passed.
- Resident contract/CUDA stack/resident run tests: 89 passed.
- Full pytest: 599 passed.

## CUDA

- CUDA available: true.
- Native backend loaded: true.
- Timed hardened resident method available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.

## Known Limitations

- Timing is wall-clock around the Python wrapper call and includes native synchronization/download work.
- This is an audit/benchmark attribution surface, not a CUDA event profiler.
- No native CUDA kernel optimization, fused-matrix hardened parity, tile-local hardened parity, 200-light benchmark, package build/upload, release update, or default switch was performed in this gate.

## Next Step

- Use the new timing surface to profile hardened winsorized on representative data, then optimize or replace the local-sort CUDA prototype before any default-path consideration.

## Clean-Room Compliance

- Compliant.
- This gate records timing around GLASS-owned CUDA methods and GLASS runtime artifacts only.
- No PixInsight/WBPP/PJSR source code or proprietary implementation details were read, copied, summarized, or reworked.
