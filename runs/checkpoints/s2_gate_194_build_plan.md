# GLASS Windows Package Build Plan

- Status: `build_plan_ready`
- Passed: `True`
- Recommendation: `build_all_variants`
- Ready variants: `cuda13, cuda12, cuda11, cpu`
- Missing CUDA variants: ``

## Discovered Toolkits

| Version | Path | nvcc |
| --- | --- | --- |
| 13.2 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2` | True |
| 12.4 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4` | True |
| 11.8 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8` | True |

## Variants

| Label | Ready | Toolkit | Match | Zip |
| --- | --- | --- | --- | --- |
| cuda13 | True | 13.2 | major_compatible | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip` |
| cuda12 | True | 12.4 | exact | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip` |
| cuda11 | True | 11.8 | exact | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip` |
| cpu | True | None | not_required | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip` |

## Build Commands

### cuda13

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cuda13 -BuildCuda -CudaArchitectures "86;89;90;100;120" -StaticCudaRuntime -CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2"
```

### cuda12

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cuda12 -BuildCuda -CudaArchitectures "75;80;86;89;90" -StaticCudaRuntime -CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"
```

### cuda11

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cuda11 -BuildCuda -CudaArchitectures "50;52;60;61;70;75;80;86" -StaticCudaRuntime -CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
```

### cpu

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cpu
```

## Checks

- PASS: `all_package_labels_known` - {'unknown_labels': [], 'requested_labels': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `cpu_package_planned` - {'ready_variants': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `at_least_one_cuda_variant_ready` - {'ready_cuda_variants': ['cuda13', 'cuda12', 'cuda11'], 'missing_cuda_variants': []}
