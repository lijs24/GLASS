# S2 Gate 83 Status

## Gate

S2-Gate 83: Fused resident matrix-warp sigma/winsorized rejection primitive.

## Completed

- Added a native CUDA primitive that computes sigma or winsorized-sigma integration directly from unwarped resident frames plus one registration matrix per frame.
- Reused the GLASS-owned bilinear and Lanczos3 matrix sampling semantics from Gate82.
- Returned master, weight map, finite-sample coverage, low rejection map, high rejection map, geometric footprint coverage, and timing diagnostics.
- Exposed the primitive through `glass_cuda.ResidentCalibratedStack.integrate_matrix_warped_sigma_clip`.
- Added focused CUDA tests comparing fused sigma and fused winsorized-sigma output against the existing public warp-then-`integrate_sigma_clip` path.
- Updated the Phase 2 gate plan and algorithm source ledger.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m ruff check cpp src tests docs`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_sigma_bilinear_matches_warp_then_integrate tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_winsorized_lanczos3_matches_warp_then_integrate`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`
- `.\.venv\Scripts\python.exe -c "import json, glass_cuda; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices() if glass_cuda.cuda_available() else []}, indent=2))"`

## Test Results

- Native CUDA build: passed; final rebuild reported `ninja: no work to do`.
- Ruff: passed.
- Focused CUDA fused rejection tests: `2 passed in 0.19s`.
- Full pytest: `287 passed in 12.09s`.
- Diff whitespace check: passed; only Git LF/CRLF warnings were reported.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## Numerical Validation

The focused tests compare `integrate_matrix_warped_sigma_clip` with the existing public warp-then-integrate behavior:

- Bilinear sigma clip: fused master, weight map, finite-sample coverage, low/high rejection maps, and geometric coverage match public warp plus `integrate_sigma_clip`.
- Lanczos3 winsorized sigma: fused master, weight map, finite-sample coverage, low/high rejection maps, and geometric coverage match public warp plus `integrate_sigma_clip`.
- The timing dictionary reports `native_fused_matrix_warp_sigma_clip_one_sync`, the selected interpolation, `sigma_clip` or `winsorized_sigma`, sigma thresholds, `avoids_stack_scatter=true`, and `modifies_resident_stack=false`.

## 200-Light Regression

Not run for this gate. Gate83 adds an opt-in native primitive and does not change the default resident CUDA pipeline, default warp dispatch, DQ/report artifacts, or real-data routing. A 200-light benchmark is required when a later gate wires this primitive into an experimental or default pipeline path.

## Known Limits

- The primitive does not yet integrate local normalization or DQ map generation.
- It downloads all output maps to host and allocates temporary device output buffers per call.
- It is not yet exposed as a `glass run` option.
- It is not yet a default path and does not affect the current 200-light production route.
- The focused tests compare against existing GLASS native warp/integration behavior; the underlying resident sigma implementation already has CPU reference tests.

## Next Step

Add an experimental resident pipeline route for `local_normalization=off` that uses fused matrix-warp winsorized integration after registration, then run the 200-light benchmark and compare both timing and output against the Gate80/Gate81 default route.

## Clean-Room Compliance

Compliant. The implementation uses GLASS-owned CUDA sampling formulas and public mean/std plus winsorized clipping definitions. It did not read or copy official PixInsight/WBPP/PJSR source code and did not modify input image directories.
