# Gate 04 Status

Gate: 4 - CUDA tile calibration

Completed content:

- Implemented native CUDA `calibrate_tile_f32` kernel in `cpp/cuda/calibration_kernels.cu`.
- Added pybind wrapper in `_glass_cuda_native`.
- Python `glass_cuda.calibrate_tile_f32` now dispatches to native CUDA when native backend is loaded.
- Verified CPU/GPU agreement for:
  - dark includes bias semantics;
  - dark excludes bias semantics;
  - dark exposure scaling;
  - flat floor;
  - pedestal.
- Added a CPU calibration runner for `glass run --until-stage calibration`; this is a useful CPU path but does not claim Gate 6 streaming completion.

Commands run:

- `.\\.venv\\Scripts\\python -m pip install cmake ninja pybind11 scikit-build-core`
- `winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget --silent --accept-package-agreements --accept-source-agreements --override "--wait --quiet --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"`
- `winget install --id Nvidia.CUDA --source winget --accept-package-agreements --accept-source-agreements --override "-s nvcc_13.2 cudart_13.2 crt_13.2 nvvm_13.2 nvrtc_13.2 nvrtc_dev_13.2 nvjitlink_13.2 nvptxcompiler_13.2 cuobjdump_13.2 nvdisasm_13.2 nvprune_13.2 nvfatbin_13.2 thrust_13.2 visual_studio_integration_13.2"`
- `.\\.venv\\Scripts\\cmake -S . -B build\\native-cuda -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_BUILD_CUDA=OFF -DCMAKE_CUDA_ARCHITECTURES=120`
- `.\\.venv\\Scripts\\cmake --build build\\native-cuda --config Release`
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_cuda_import.py tests/test_cuda_device_info.py tests/test_cuda_smoke.py tests/test_gpu_calibration_vs_cpu.py`
- `.\\.venv\\Scripts\\glass synthetic --out runs/gate_04_synth_run/source --frames 4 --width 32 --height 32 --filter H --known-shift`
- `.\\.venv\\Scripts\\glass audit --root runs/gate_04_synth_run/source --out runs/gate_04_synth_run/audit --backend auto`
- `.\\.venv\\Scripts\\glass run --plan runs/gate_04_synth_run/audit/processing_plan.json --out runs/gate_04_synth_run/run --backend auto --until-stage calibration`
- `.\\.venv\\Scripts\\glass audit --root "E:\\摄影素材\\天协远程台原始素材\\远程�?40430\\-15\\M5" --out runs/local_audit_m5_small --backend auto`
- `.\\.venv\\Scripts\\python -m pytest -q`

Test result:

- CUDA focused tests: `6 passed`
- Full suite: `26 passed`
- Synthetic calibration runner: `3` master frames and `4` calibrated lights generated.
- Real small target audit: `30` M5 light frames scanned, no scan warnings, plan not executable because calibration frames were intentionally not included in that small target-only subset.

CUDA availability:

- Native backend loaded: yes
- CUDA available to GLASS: yes
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- CUDA Toolkit: `13.2`

Known limitations:

- The native `.pyd` is a local build artifact ignored by git; rebuild with the documented CMake command.
- Gate 4 covers tile calibration only. Master-frame CUDA streaming, light calibration streaming, registration, warp, LN, and integration remain future gates.
- Build currently targets `sm_120` for this workstation GPU.

Next step:

- Gate 5: CUDA streaming master frame generation, or first package the native build more cleanly with scikit-build if desired.

Clean-room compliance:

- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
- CUDA implementation is an independent kernel based on the documented calibration formula.
