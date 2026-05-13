# Gate 10 Resident Grid LN Apply Status

## Gate

Gate 10 resident Local Normalization building-block checkpoint.

This checkpoint does not complete full resident tile/window LN. It adds the missing resident apply primitive so future resident LN can apply tile/grid coefficients without downloading full frames to the host.

## Completed Content

- Added native `ResidentCalibratedStack.apply_grid_normalization_frame(index, scales, offsets, tile_height, tile_width)`.
- The method validates coefficient grid shape against resident frame shape and applies the scale/offset table directly in VRAM.
- Added the Python wrapper method on `gpwbpp_cuda.ResidentCalibratedStack`.
- Added resident stack test comparing in-place resident grid normalization against the standalone CUDA `local_norm_apply_grid_f32` result.
- Updated CUDA and Local Normalization documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp_cuda.py tests\test_cuda_resident_stack.py
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build "C:\Users\ljs\WORK\astro\gpuwbpp\build\native-cuda"'
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_normalization_matches_standalone_cuda tests\test_gpu_local_norm_vs_cpu.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Native CUDA extension build: passed.
- Targeted resident/grid LN tests: `6 passed in 0.92s`.
- Full test suite: `169 passed in 8.15s`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- Resident coefficient estimation is not implemented here.
- The resident pipeline still uses the existing global mean/std LN mode when `--local-normalization on` is requested.
- Grid coefficients are piecewise constant per tile; interpolation/smoothing remains future work.

## Next Step

- Add resident tile statistics or a controlled coefficient-estimation bridge, then wire resident `--local-normalization on` to grid coefficients instead of global mean/std.

## Clean-room Compliance

- Compliant. The implementation uses project-owned CUDA kernels and general tile scale/offset normalization math.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
