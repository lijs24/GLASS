# S2-Gate 189 Status: CUDA11 Minimal Toolkit Install

## Gate

- Gate: S2-Gate 189
- Scope: download and install the minimal CUDA11 Toolkit components needed to
  build the Windows `cuda11` portable package.
- Status: green
- Date: 2026-06-17

## Completed

- Downloaded `cuda_11.8.0_522.06_windows.exe` with BITS.
- Verified SHA256:
  `b70f38f27321c0a53993438a91970a2e3c426f46da4c42eceff1eeea031a6555`.
- Installed CUDA11 components through
  `packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda11 -Install`.
- Requested components only: `nvcc_11.8`, `cudart_11.8`.
- Recorded `driver_component_included=false`.
- Installer exit code: `0`.
- Confirmed CUDA11 `nvcc.exe` exists and reports `V11.8.89`.
- Confirmed CUDA11 runtime/header artifacts:
  `cuda_runtime.h`, `cudart.lib`, `cudart64_110.dll`.
- Confirmed `nvidia-smi` still reports driver `596.21`.
- Refreshed Windows package build plan with `--fail-on-missing`.

## Commands Run

```powershell
Start-BitsTransfer -Source https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_522.06_windows.exe -Destination $env:LOCALAPPDATA\GLASS\cuda-installers\cuda_11.8.0_522.06_windows.exe -DisplayName GLASS-cuda11-11.8.0-download -Asynchronous
Complete-BitsTransfer -BitsJob <GLASS-cuda11-11.8.0-download>
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda11 -Download -OutJson C:\glass_runs\phase2_s2_gate_189_cuda11_toolkit_install\cuda11_minimal_toolkit_download.json
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda11 -Install -OutJson C:\glass_runs\phase2_s2_gate_189_cuda11_toolkit_install\cuda11_minimal_toolkit_install.json
& 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\nvcc.exe' --version
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
.\.venv\Scripts\glass.exe windows-package-build-plan --out C:\glass_runs\phase2_s2_gate_189_cuda11_toolkit_install\windows_package_build_plan_after_cuda11.json --markdown C:\glass_runs\phase2_s2_gate_189_cuda11_toolkit_install\windows_package_build_plan_after_cuda11.md --fail-on-missing
.\.venv\Scripts\glass.exe windows-package-build-plan --out runs\checkpoints\s2_gate_189_windows_package_build_plan_after_cuda11.json --markdown runs\checkpoints\s2_gate_189_windows_package_build_plan_after_cuda11.md --fail-on-missing
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Verification

- Full ruff: passed.
- Full pytest: `464 passed in 24.64s`.
- CUDA Toolkit roots after install: `v11.8`, `v12.4`, `v13.2`.
- CUDA11 nvcc: `Cuda compilation tools, release 11.8, V11.8.89`.
- Driver after install: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition,
  596.21`.
- Package build-plan status: `build_plan_ready`.
- Ready variants: `cuda13`, `cuda12`, `cuda11`, `cpu`.
- Missing CUDA variants: none.
- CUDA11 Toolkit match in build-plan: `exact`.

## Artifacts

- Download verification:
  `runs\checkpoints\s2_gate_189_cuda11_minimal_toolkit_download.json`
- Install verification:
  `runs\checkpoints\s2_gate_189_cuda11_minimal_toolkit_install.json`
- Post-install build plan:
  `runs\checkpoints\s2_gate_189_windows_package_build_plan_after_cuda11.json`
- Post-install build plan Markdown:
  `runs\checkpoints\s2_gate_189_windows_package_build_plan_after_cuda11.md`
- External artifact root:
  `C:\glass_runs\phase2_s2_gate_189_cuda11_toolkit_install`

## Known Limitations

- This gate installed the Toolkit components but did not build or smoke the
  `cuda11` portable package.
- CUDA11 package execution on Blackwell is expected to use PTX forward JIT and
  may be slower than CUDA13 native cubin.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- No input image directory was modified.
- No NVIDIA display driver component was requested by the installer helper.

## Next Step

- Build `GLASS-Portable-win64-cuda11.zip` using the refreshed build-plan command
  and run `glass windows-package-smoke --require-cuda --expected-package-label
  cuda11`.
