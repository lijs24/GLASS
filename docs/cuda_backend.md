# CUDA Backend

The CUDA backend is optional. CPU-only installation must remain functional even
when CUDA, NVCC, or a compatible NVIDIA driver is not present.

Until the native extension is built, `src/gpwbpp_cuda.py` provides a compatibility
API. It can import, report devices visible through `nvidia-smi`, and run CPU
fallback smoke helpers. It deliberately reports `cuda_available() == false` so
tests and reports do not confuse fallback helpers with real CUDA kernels.

Gate 3 introduces the `gpwbpp_cuda` Python extension with:

- `cuda_available()`
- `list_devices()`
- `get_device_info(device_id)`
- `smoke_add_f32(a, b)`
- `reduce_mean_tile_f32(tile)`
- `calibrate_tile_f32(...)`
- `integrate_accumulate_mean_tile_f32(...)`
- `ResidentCalibratedStack.integrate_sigma_clip(...)`

Every CUDA operation will have a CPU reference test. If CUDA is not available,
CUDA tests skip rather than failing the whole project. Kernel launch failures
must become clear Python exceptions.

Local native build command used on Windows:

```powershell
$pybind = (& .\.venv\Scripts\python -m pybind11 --cmakedir).Trim()
cmd /c "call `"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat`" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -Dpybind11_DIR=`"$pybind`" -DCMAKE_MAKE_PROGRAM=`"$((Resolve-Path .\.venv\Scripts\ninja.exe))`" -DCMAKE_CUDA_COMPILER=`"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe`" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release"
```

The command writes `_gpwbpp_cuda_native*.pyd` into `src/` for local testing. The
binary is ignored by git; source, CMake configuration, and tests are tracked.

Resident CUDA integration now supports:

- weighted mean for already resident calibrated frames;
- two-pass mean/std sigma clipping;
- two-pass mean/std winsorized sigma clipping;
- output weight, coverage, low rejection, and high rejection maps.

The current resident rejection kernel is an engineering baseline for the
high-VRAM path. It is not yet a byte-for-byte reproduction of PixInsight
FastIntegration's robust rejection and alignment internals.
