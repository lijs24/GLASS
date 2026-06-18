# S2-Gate 261 Status

- Gate: S2-Gate 261
- Scope: Resident Hardened Winsorized CUDA Parity Prototype
- Status: green
- Date: 2026-06-18

## Completed

- Added an optional native resident CUDA method, `integrate_hardened_winsorized_sigma`, for correctness parity with the hardened CPU winsorized baseline.
- Added a CUDA prototype kernel that sorts per-pixel resident samples, computes linear q25/q50/q75 percentiles, applies the Gate 258/259 median/IQR winsorized sigma thresholds, and emits master, weight, coverage, low rejection, and high rejection maps.
- Added Python wrapper support in `glass_cuda.ResidentCalibratedStack`.
- Added a focused CUDA parity test comparing the new native method against `glass.cpu.integration.weighted_integrate_stack(..., rejection="winsorized_sigma")`.
- Kept the existing default resident runtime and fast resident winsorized path unchanged.
- Updated the Phase 2 hardening plan and algorithm source ledger.

## Commands

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build build\native-cuda-glass --config Release --target _glass_cuda_native --parallel 8'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_matches_cpu_baseline`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_cpu_integration.py tests\test_stack_engine.py`
- `.\.venv\Scripts\ruff.exe check src\glass_cuda.py tests\test_cuda_resident_stack.py src\glass\engine\rejection.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native CUDA extension build: passed.
- Build warnings: CUDA header `C4819` code-page warnings from the local Windows toolchain.
- Focused hardened resident CUDA parity test: 1 passed.
- Focused resident/integration/StackEngine tests: 50 passed.
- Ruff check: passed.
- Full pytest: 595 passed.

## CUDA

- CUDA available: true.
- Native backend loaded: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.
- CUDA toolkit used for build: 13.2.

## Known Limitations

- This is a correctness-oriented prototype, not the default optimized resident integration path.
- The prototype is limited to at most 256 resident frames per call.
- The kernel uses per-pixel local sorting and is not performance optimized for the 200-light benchmark.
- The default resident `winsorized_sigma` path still records its existing mean/std approximation semantics.
- Tile-local, matrix-warped, and full runtime paths are not yet wired to this hardened CUDA method.
- No 200-light real-data benchmark was rerun in this gate.

## Next Step

- Promote the hardened CUDA winsorized implementation behind an explicit runtime flag or optimized resident path, then measure correctness and runtime on the 200-light real dataset before changing the default descriptor to CPU-baseline parity.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS-owned CPU formulas, synthetic CUDA tests, and project-defined rejection semantics.
- No PixInsight/WBPP/PJSR source code or proprietary implementation details were read, copied, summarized, or reworked.
