# S2-Gate 190 Status: CUDA11 Portable Package Smoke

## Gate

- Gate: S2-Gate 190
- Scope: build and smoke-test the Windows `cuda11` portable package.
- Status: green
- Date: 2026-06-17

## Completed

- Built `GLASS-Portable-win64-cuda11.zip`.
- Used CUDA Toolkit root:
  `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`.
- Used CUDA compiler: NVIDIA CUDA `11.8.89`.
- Used package label: `cuda11`.
- Used CMake CUDA architectures: `50;52;60;61;70;75;80;86`.
- Requested static CUDA runtime linkage.
- Manifest is UTF-8 without BOM and starts with `{` (`123 13 10`).
- Ran package smoke with `--expected-package-label cuda11`,
  `--expected-source 260c832`, and `--require-cuda`.

## Commands Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cuda11 -BuildCuda -CudaArchitectures "50;52;60;61;70;75;80;86" -StaticCudaRuntime -CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda11.zip --expected-source 260c832 --expected-package-label cuda11 --require-cuda --out C:\glass_runs\phase2_s2_gate_190_cuda11_package_smoke\cuda11_portable_smoke.json --markdown C:\glass_runs\phase2_s2_gate_190_cuda11_package_smoke\cuda11_portable_smoke.md --fail-on-failure
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda11.zip --expected-source 260c832 --expected-package-label cuda11 --require-cuda --out runs\checkpoints\s2_gate_190_cuda11_portable_smoke.json --markdown runs\checkpoints\s2_gate_190_cuda11_portable_smoke.md --fail-on-failure
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_calibration_vs_cpu.py
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Package Result

- CUDA focused pytest: `6 passed in 0.27s`.
- Full ruff: passed.
- Full pytest: `464 passed in 27.13s`.
- Status: `package_smoke_passed`.
- Recommendation: `portable_package_ready_for_next_release_step`.
- Zip: `.release\windows\GLASS-Portable-win64-cuda11.zip`.
- Zip size: `342183616` bytes.
- Source stamp: `260c832`.
- Package label: `cuda11`.
- CUDA Toolkit root in manifest:
  `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`.
- Native extension size in package: `7424512` bytes.

## CUDA Smoke Result

- CUDA available: `true`.
- Native extension loaded: `true`.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Package guidance still recommends try order: `cuda13`, `cuda12`, `cuda11`,
  `cpu`.

## Artifacts

- External smoke JSON:
  `C:\glass_runs\phase2_s2_gate_190_cuda11_package_smoke\cuda11_portable_smoke.json`
- External smoke Markdown:
  `C:\glass_runs\phase2_s2_gate_190_cuda11_package_smoke\cuda11_portable_smoke.md`
- Checkpoint smoke JSON:
  `runs\checkpoints\s2_gate_190_cuda11_portable_smoke.json`
- Checkpoint smoke Markdown:
  `runs\checkpoints\s2_gate_190_cuda11_portable_smoke.md`

## Known Limitations

- CUDA11 package is expected to run on the local Blackwell GPU through PTX
  forward JIT rather than native `sm_120` cubin.
- This gate validates package startup/CUDA loading; it does not benchmark the
  200-light workload on CUDA11.
- The package is not signed and no installer was produced.
- The package source stamp is `260c832`; formal release artifacts should be
  rebuilt after final release commits/tags if exact source-stamp matching is
  required.
- After the portable build, the development-tree `_glass_cuda_native` was a
  CUDA11 build. For local dev-env tests, `cudart64_110.dll` had to be present
  beside the generated pyd; the portable package already carries this runtime
  DLL in `site-packages`.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS package artifacts and GLASS doctor output.
- No input image directory was modified.

## Next Step

- Run focused CUDA tests and full pytest, then proceed to package matrix smoke
  or benchmark comparisons across `cuda13`, `cuda12`, and `cuda11`.
