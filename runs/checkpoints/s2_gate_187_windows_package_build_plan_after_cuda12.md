# GLASS Windows Package Build Plan

- Status: `partial_toolkits`
- Passed: `True`
- Recommendation: `build_ready_variants_and_install_missing_toolkits`
- Ready variants: `cuda13, cuda12, cpu`
- Missing CUDA variants: `cuda11`

## Discovered Toolkits

| Version | Path | nvcc |
| --- | --- | --- |
| 13.2 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2` | True |
| 12.4 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4` | True |

## Variants

| Label | Ready | Toolkit | Match | Zip |
| --- | --- | --- | --- | --- |
| cuda13 | True | 13.2 | major_compatible | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip` |
| cuda12 | True | 12.4 | exact | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip` |
| cuda11 | False | None | missing | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip` |
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

### cpu

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cpu
```

## Missing Toolkit Commands

### cuda11 download

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/install_cuda_toolkit_minimal.ps1 -Label cuda11 -Download
```

### cuda11 install

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/install_cuda_toolkit_minimal.ps1 -Label cuda11 -Install
```

## Checks

- PASS: `all_package_labels_known` - {'unknown_labels': [], 'requested_labels': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `cpu_package_planned` - {'ready_variants': ['cuda13', 'cuda12', 'cpu']}
- PASS: `at_least_one_cuda_variant_ready` - {'ready_cuda_variants': ['cuda13', 'cuda12'], 'missing_cuda_variants': ['cuda11']}
