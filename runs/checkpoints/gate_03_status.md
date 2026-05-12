# Gate 03 Status

Gate: 3 - CUDA extension skeleton

Status:

- Completed after installing/configuring the required local build tools.

Completed diagnostic content:

- Added importable `gpwbpp_cuda` compatibility module.
- `list_devices()` reports devices visible through `nvidia-smi`.
- `smoke_add_f32()` and `reduce_mean_tile_f32()` provide CPU smoke fallbacks.
- Added native `_gpwbpp_cuda_native` pybind/CUDA module.
- Native `cuda_available()`, `list_devices()`, `get_device_info()`, and CUDA `smoke_add_f32()` pass tests.
- Installed project-local CMake/Ninja through `.venv`.
- Installed Visual Studio Build Tools 2022 C++ workload.
- Installed CUDA Toolkit 13.2 selected toolkit components without changing the NVIDIA display driver.
- Checked for `nvidia-smi`: available.
- Detected GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Reported compute capability: `12.0`
- Reported VRAM: `97887 MiB`
- Reported driver version: `596.21`

Commands run:

- `where.exe nvcc`
- `where.exe nvidia-smi`
- `nvidia-smi --query-gpu=name,compute_cap,memory.total,driver_version --format=csv,noheader`
- `where.exe cmake`
- `where.exe cl`
- `.\\.venv\\Scripts\\python -m pip install -e .[dev,report]`
- `.\\.venv\\Scripts\\python -m pip install cmake ninja pybind11 scikit-build-core`
- `winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget --silent --accept-package-agreements --accept-source-agreements --override "--wait --quiet --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"`
- `winget install --id Nvidia.CUDA --source winget --accept-package-agreements --accept-source-agreements --override "-s nvcc_13.2 cudart_13.2 crt_13.2 nvvm_13.2 nvrtc_13.2 nvrtc_dev_13.2 nvjitlink_13.2 nvptxcompiler_13.2 cuobjdump_13.2 nvdisasm_13.2 nvprune_13.2 nvfatbin_13.2 thrust_13.2 visual_studio_integration_13.2"`
- `.\\.venv\\Scripts\\cmake -S . -B build\\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -DCMAKE_CUDA_ARCHITECTURES=120`
- `.\\.venv\\Scripts\\python -m pytest -q`

Test result:

- Full suite before compatibility API: `16 passed, 7 skipped`
- CUDA API smoke subset:
  `4 passed`
- Full suite after native module:
  `24 passed`

CUDA availability:

- NVIDIA GPU present: yes
- CUDA runtime/native extension available to GPWBPP: yes
- CUDA API module importable: yes

Known limitations:

- The native binary is a local build artifact and is not committed.
- CMake/scikit-build packaging is still manual; editable install uses the Python shim plus local native build artifact.

Next step:

- Gate 4: implement and validate CUDA tile calibration.

Clean-room compliance:

- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
- The CUDA blocker is purely local toolchain availability.
