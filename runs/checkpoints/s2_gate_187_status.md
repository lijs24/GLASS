# S2-Gate 187 Status: CUDA12 Minimal Toolkit Install

## Gate

- Gate: S2-Gate 187
- Scope: download and install the minimal CUDA12 Toolkit components needed to
  build the Windows `cuda12` portable package.
- Status: green
- Date: 2026-06-17

## Completed

- Downloaded `cuda_12.4.1_551.78_windows.exe` with BITS.
- Verified SHA256:
  `7d20c5eb186e4d3c64680fe5096bed05926aea89754192102323c956c26244de`.
- Installed CUDA12 components through
  `packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda12 -Install`.
- Requested components only: `nvcc_12.4`, `cudart_12.4`.
- Recorded `driver_component_included=false`.
- Installer exit code: `0`.
- Confirmed CUDA12 `nvcc.exe` exists and reports `V12.4.131`.
- Confirmed CUDA12 runtime/header artifacts:
  `cuda_runtime.h`, `cudart.lib`, `cudart64_12.dll`.
- Confirmed `nvidia-smi` still reports driver `596.21`.
- Refreshed Windows package build plan after install.

## Commands Run

```powershell
Start-BitsTransfer -Source https://developer.download.nvidia.com/compute/cuda/12.4.1/local_installers/cuda_12.4.1_551.78_windows.exe -Destination $env:LOCALAPPDATA\GLASS\cuda-installers\cuda_12.4.1_551.78_windows.exe -DisplayName GLASS-cuda12-12.4.1-download -Asynchronous
Complete-BitsTransfer -BitsJob <GLASS-cuda12-12.4.1-download>
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda12 -Download -OutJson C:\glass_runs\phase2_s2_gate_187_cuda12_toolkit_download\cuda12_minimal_toolkit_download.json
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda12 -Install -OutJson C:\glass_runs\phase2_s2_gate_187_cuda12_toolkit_download\cuda12_minimal_toolkit_install.json
& 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin\nvcc.exe' --version
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
.\.venv\Scripts\glass.exe windows-package-build-plan --out C:\glass_runs\phase2_s2_gate_187_cuda12_toolkit_install\windows_package_build_plan_after_cuda12.json --markdown C:\glass_runs\phase2_s2_gate_187_cuda12_toolkit_install\windows_package_build_plan_after_cuda12.md
.\.venv\Scripts\glass.exe windows-package-build-plan --out runs\checkpoints\s2_gate_187_windows_package_build_plan_after_cuda12.json --markdown runs\checkpoints\s2_gate_187_windows_package_build_plan_after_cuda12.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Verification

- Full ruff: passed.
- Full pytest: `464 passed in 25.51s`.
- CUDA Toolkit roots after install: `v12.4`, `v13.2`.
- CUDA12 nvcc: `Cuda compilation tools, release 12.4, V12.4.131`.
- Driver after install: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition,
  596.21`.
- Package build-plan status: `partial_toolkits`.
- Ready variants: `cuda13`, `cuda12`, `cpu`.
- Missing CUDA variants: `cuda11`.
- CUDA12 Toolkit match in build-plan: `exact`.

## Artifacts

- Download verification:
  `runs\checkpoints\s2_gate_187_cuda12_minimal_toolkit_download.json`
- Install verification:
  `runs\checkpoints\s2_gate_187_cuda12_minimal_toolkit_install.json`
- Post-install build plan:
  `runs\checkpoints\s2_gate_187_windows_package_build_plan_after_cuda12.json`
- Post-install build plan Markdown:
  `runs\checkpoints\s2_gate_187_windows_package_build_plan_after_cuda12.md`
- External artifact root:
  `C:\glass_runs\phase2_s2_gate_187_cuda12_toolkit_install`

## Known Limitations

- CUDA11 is still missing.
- This gate installed the Toolkit components but did not build or smoke the
  `cuda12` portable package.
- A command used while copying artifacts attempted to copy a checkpoint file to
  itself and emitted a harmless PowerShell `Copy-Item` warning; all intended
  artifacts were still written and verified.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- No input image directory was modified.
- No NVIDIA display driver component was requested by the installer helper.

## Next Step

- Build `GLASS-Portable-win64-cuda12.zip` using the refreshed build-plan command
  and run `glass windows-package-smoke --require-cuda --expected-package-label
  cuda12`.
