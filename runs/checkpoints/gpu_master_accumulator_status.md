# GPU Master Accumulator Helper Checkpoint

- Date: 2026-05-12
- Scope: Replace the standalone GPU master-frame helper's per-tile 3D stack with a bounded tile accumulator.
- Related gates: strengthens Gate 5 CUDA master-frame helper behavior.

## Completed

- Reworked `gpwbpp.gpu.master_frames.mean_stack_paths_tile_streaming` to read source FITS files through `FitsImageReader`.
- Removed Astropy HDU `.data` slicing and per-tile `np.stack` construction from the helper.
- Added a per-tile accumulator path:
  - Uses `gpwbpp_cuda.integrate_accumulate_mean_tile_f32` when native CUDA is available.
  - Uses a float64 CPU tile accumulator when CUDA is unavailable.
- Added a regression test that monkeypatches `numpy.stack` to fail, proving the fallback helper does not build a 3D tile stack.
- Updated memory-model and completion-audit docs.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/gpwbpp/gpu/master_frames.py tests/test_gpu_master_frames_vs_cpu.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_gpu_master_frames_vs_cpu.py tests/test_cpu_master_frames.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Focused master-frame tests: 4 passed in 0.33 s.
- Full pytest: 57 passed in 4.99 s.

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- The helper still returns the full master image as a NumPy array, because its public API is a CPU-visible `MasterFrameResult`. The bounded-memory guarantee applies to reading and combining input frames per tile, not to the final returned array.
- Robust/rejection master-frame combination is still future work.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Remove remaining optional full-frame convenience paths where they are not intentionally limited to small arrays, then continue toward WBPP black-box timing when reference output is available.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No user input directory was modified.
