# Gate 05 Status

Gate: 5 - CUDA streaming master frame generation

Completed content:

- Implemented native CUDA `mean_stack_tiles_f32` kernel in `cpp/cuda/master_frame_kernels.cu`.
- Added pybind wrapper and Python `glass_cuda.mean_stack_tiles_f32`.
- Implemented `glass.gpu.master_frames.mean_stack_paths_tile_streaming`.
- GPU master-frame path reads FITS files with memmap and processes rectangular tiles instead of loading all source frames into one CPU/GPU stack.
- Added CPU/GPU tests for tiled mean stack and master bias/dark/flat shape/statistics.

Commands run:

- `.\\.venv\\Scripts\\cmake -S . -B build\\native-cuda -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -DCMAKE_CUDA_ARCHITECTURES=120`
- `.\\.venv\\Scripts\\cmake --build build\\native-cuda --config Release`
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_gpu_master_frames_vs_cpu.py tests/test_tile_scheduler.py`
- `.\\.venv\\Scripts\\python -m pytest -q`

Test result:

- Gate 5 focused tests: `3 passed`
- Full suite: `27 passed`

CUDA availability:

- Native backend loaded: yes
- CUDA available to GLASS: yes
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- CUDA Toolkit: `13.2`

Known limitations:

- The current GPU master-frame path uses per-tile host stacks; it is out-of-core with respect to full images but not yet optimized with pinned buffers or stream pools.
- Bias/dark/flat rejection and robust median/winsorized reductions are not implemented yet.
- Build currently targets `sm_120` for this workstation GPU.

Next step:

- Gate 6: connect light calibration to tile streaming, cache/resume behavior, and backend selection.
- Later benchmark gate: compare GLASS runtime against PixInsight/WBPP black-box output on the same small real dataset.

Clean-room compliance:

- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
- The CUDA master-frame kernel is an independent mean reduction implementation.

