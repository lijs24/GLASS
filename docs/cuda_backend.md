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

Every CUDA operation will have a CPU reference test. If CUDA is not available,
CUDA tests skip rather than failing the whole project. Kernel launch failures
must become clear Python exceptions.
