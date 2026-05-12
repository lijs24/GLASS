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
- `estimate_translation_search_f32(reference, moving, max_shift_x, max_shift_y)`
- `estimate_translation_from_catalogs_f32(reference_x, reference_y, moving_x, moving_y, tolerance_px)`
- `star_local_max_mask_f32(tile, threshold)`
- `star_candidates_f32(tile, threshold, max_candidates)`
- `star_top_candidates_f32(tile, threshold, max_candidates)`
- `ResidentCalibratedStack.integrate_sigma_clip(...)`
- `ResidentCalibratedStack.apply_translation_frame(...)`
- `ResidentCalibratedStack.star_local_max_mask(index, threshold)`
- `ResidentCalibratedStack.star_candidates(index, threshold, max_candidates)`
- `ResidentCalibratedStack.star_top_candidates(index, threshold, max_candidates)`

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
- two-stage winsorized mean/std sigma rejection approximation;
- output weight, coverage, low rejection, and high rejection maps.
- optional preview-scale phase-correlation translation registration followed by
  integer-pixel CUDA warp with NaN edge fill.
- GPU local-maximum star candidate masking on standalone tiles and directly on
  resident calibrated frames.
- GPU compaction of local maxima into bounded `(x, y, flux)` star catalogs on
  standalone tiles and directly on resident calibrated frames.
- GPU top-N selection and descending flux sorting for bounded star catalogs,
  available on standalone tiles and directly on resident calibrated frames.
- GPU integer-translation search with per-shift normalized cross-correlation,
  followed by device-side best-shift selection and CUDA translation warp.
- GPU star-catalog pair-offset voting for translation estimation from bounded
  top-N catalogs.

The current resident rejection kernel is an engineering baseline for the
high-VRAM path. It is not yet a byte-for-byte reproduction of PixInsight
FastIntegration's robust rejection and alignment internals. The resident
translation path is useful for diagnosis and high-VRAM timing, but it does not
replace the star-based registration/Lanczos warp gates.

For registration, the next CUDA step is to run asterism matching, subpixel
refinement, similarity/affine scoring, and transform application on the device
from bounded star catalogs. CPU should only orchestrate and receive compact
diagnostics.
