# Gate 10 CUDA tile mean/std local-normalization checkpoint

Date: 2026-05-13

Status: completed incremental Gate 10 capability. This is not the full PixInsight/WBPP Local Normalization model; it adds a tested CUDA tile primitive that moves local-normalization statistics and apply one step further onto the GPU.

## Completed work

- Added native CUDA pair statistics for local-normalization tiles:
  - `local_norm_pair_stats_f32(source, reference)`
  - finite-pixel source/reference mean and standard deviation
  - ignores pixels where either source or reference is non-finite
- Added Python wrapper:
  - `gpwbpp_cuda.local_norm_pair_stats_f32`
  - `gpwbpp_cuda.local_norm_estimate_apply_mean_std_f32`
- Added CPU baseline helper:
  - `estimate_tile_normalization_mean_std`
- Wired non-resident `local_normalize_registered_frames(..., backend="cuda")` to use CUDA mean/std stats plus CUDA apply when available.
- Preserved CPU median/std local-normalization behavior when CUDA is unavailable.
- Updated `docs/local_normalization_model.md` to distinguish:
  - CPU median/std baseline
  - CUDA mean/std tile primitive
  - resident global mean/std diagnostic mode

## Verification commands

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda --config Release --target _gpwbpp_cuda_native'
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests\test_cpu_local_norm.py `
  tests\test_gpu_local_norm_vs_cpu.py `
  tests\test_pipeline_fixture.py::test_pipeline_fixture_run_local_normalization `
  tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke
```

Result: 8 passed in 1.50 s.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 123 passed in 6.59 s.

```powershell
.\.venv\Scripts\python.exe - <<'PY'
import numpy as np, gpwbpp_cuda
src = np.arange(12, dtype=np.float32).reshape(3, 4)
ref = src * 2 + 3
out, stats = gpwbpp_cuda.local_norm_estimate_apply_mean_std_f32(src, ref)
print(gpwbpp_cuda.cuda_available(), stats["stats_backend"], float(np.max(np.abs(out - ref))))
PY
```

Observed: CUDA available, `stats_backend=cuda`, max absolute error 0.0.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Native module rebuilt: `src\_gpwbpp_cuda_native.cp312-win_amd64.pyd`.

## Known limitations

- The CUDA primitive uses mean/std, not median/std. This is intentional for the first GPU statistics primitive.
- Mask support in the Python wrapper is implemented by marking invalid pixels as NaN for the CUDA stats pass and restoring invalid pixels after apply.
- Resident CUDA still exposes only `resident_global_mean_std`; full resident tile/window LN remains a later increment.
- This does not claim PixInsight-identical Local Normalization.

## Next step

Use this CUDA tile primitive to implement a resident tiled LN pass, or add a smooth grid/interpolation model over the per-tile coefficients to reduce tile boundary discontinuities.

## Clean-room compliance

Compliant. This implementation uses only GPWBPP code, CUDA primitives, and generic local-normalization formulas. No official WBPP/PJSR source was read or copied.
