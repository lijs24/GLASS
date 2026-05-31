# S2 Gate 82 Status

## Gate

S2-Gate 82: Fused resident matrix-warp weighted mean primitive.

## Completed

- Added a native CUDA primitive that computes weighted mean integration directly from unwarped resident frames plus one registration matrix per frame.
- Supported bilinear and Lanczos3 sampling with GLASS-owned matrix inversion, footprint rules, and Lanczos clamping semantics matching the existing warp kernels.
- Returned master, weight map, finite-sample coverage, geometric footprint coverage, and a timing dictionary.
- Exposed the primitive through `glass_cuda.ResidentCalibratedStack.integrate_matrix_warped_mean`.
- Added focused CUDA tests comparing fused output against the existing warp-then-integrate public path for bilinear and Lanczos3.
- Updated the Phase 2 gate plan and algorithm source ledger.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m ruff check cpp src tests docs`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_mean_bilinear_matches_warp_then_integrate tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_mean_lanczos3_matches_warp_then_integrate`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `.\.venv\Scripts\python.exe -c "import json, glass_cuda; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices() if glass_cuda.cuda_available() else []}, indent=2))"`

## Test Results

- Native CUDA build: passed.
- Ruff: passed.
- Focused CUDA fused primitive tests: `2 passed in 2.07s`.
- Full pytest: `285 passed in 12.16s`.
- Diff whitespace check: passed; only Git LF/CRLF warnings were reported.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## Numerical Validation

The focused tests compare `integrate_matrix_warped_mean` with the existing public warp-then-integrate behavior:

- Bilinear: fused master, weight map, finite-sample coverage, and geometric coverage match the expected warp-then-integrate result within test tolerances.
- Lanczos3: fused master, weight map, finite-sample coverage, and geometric coverage match the expected warp-then-integrate result within test tolerances.
- The fused timing dictionary reports `native_fused_matrix_warp_weighted_mean_one_sync`, `avoids_stack_scatter=true`, and `modifies_resident_stack=false`.
- The bilinear test verifies that calling the fused primitive does not mutate the resident stack by comparing against the still-unwarped resident mean.

## 200-Light Regression

Not run for this gate. Gate82 adds an opt-in native primitive and does not change the default resident CUDA pipeline, the Gate80/Gate81 default warp dispatch, or any real-data routing. A 200-light benchmark becomes required when a later gate wires fused warp integration into the pipeline or makes it selectable for real-data runs.

## Known Limits

- The primitive supports weighted mean with `rejection=none` only.
- It does not yet implement sigma or winsorized sigma rejection.
- It does not yet bridge local normalization, DQ map construction, or report artifacts in the real pipeline.
- It does not yet replace the default resident warp path.
- The current implementation allocates output buffers and downloads all maps in one call; future gates should reuse output workspace and optionally keep maps resident.

## Next Step

Add a fused resident sigma/winsorized integration primitive or a pipeline-level experimental route that can skip in-place warp when local normalization is off. That is the point where 200-light timing and numerical comparison should be repeated.

## Clean-Room Compliance

Compliant. The implementation uses GLASS-owned CUDA sampling formulas and public weighted-mean definitions. It did not read or copy official PixInsight/WBPP/PJSR source code and did not modify input image directories.
