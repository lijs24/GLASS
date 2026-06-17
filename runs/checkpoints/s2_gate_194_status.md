# S2-Gate 194 Status: Strict Same-Source Windows Packages

## Gate

- Gate: S2-Gate 194
- Scope: rebuild and smoke-test all Windows portable package variants from one
  source stamp, then generate strict suite and manifest artifacts.
- Status: green
- Date: 2026-06-17

## Completed

- Generated a strict build plan with all package variants ready.
- Rebuilt `cuda13`, `cuda12`, `cuda11`, and `cpu` portable zips from source
  stamp `aa63510`.
- Smoke-tested each package immediately after build with the expected label and
  expected source stamp.
- Generated strict package-suite artifacts with `--require-same-source-stamp`.
- Generated strict release-manifest artifacts with `--require-same-source-stamp`.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe windows-package-build-plan --fail-on-missing --out runs\checkpoints\s2_gate_194_build_plan.json --markdown runs\checkpoints\s2_gate_194_build_plan.md
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cuda13 -BuildCuda -CudaArchitectures "86;89;90;100;120" -StaticCudaRuntime -CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2"
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda13.zip --expected-source aa63510 --expected-package-label cuda13 --require-cuda --out runs\checkpoints\s2_gate_194_cuda13_portable_smoke.json --markdown runs\checkpoints\s2_gate_194_cuda13_portable_smoke.md --fail-on-failure
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cuda12 -BuildCuda -CudaArchitectures "75;80;86;89;90" -StaticCudaRuntime -CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda12.zip --expected-source aa63510 --expected-package-label cuda12 --require-cuda --out runs\checkpoints\s2_gate_194_cuda12_portable_smoke.json --markdown runs\checkpoints\s2_gate_194_cuda12_portable_smoke.md --fail-on-failure
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cuda11 -BuildCuda -CudaArchitectures "50;52;60;61;70;75;80;86" -StaticCudaRuntime -CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda11.zip --expected-source aa63510 --expected-package-label cuda11 --require-cuda --out runs\checkpoints\s2_gate_194_cuda11_portable_smoke.json --markdown runs\checkpoints\s2_gate_194_cuda11_portable_smoke.md --fail-on-failure
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/build_portable.ps1 -Python .\.venv\Scripts\python.exe -Configuration Release -PackageLabel cpu
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cpu.zip --expected-source aa63510 --expected-package-label cpu --out runs\checkpoints\s2_gate_194_cpu_portable_smoke.json --markdown runs\checkpoints\s2_gate_194_cpu_portable_smoke.md --fail-on-failure
.\.venv\Scripts\glass.exe windows-package-suite --smoke cuda13=runs\checkpoints\s2_gate_194_cuda13_portable_smoke.json --smoke cuda12=runs\checkpoints\s2_gate_194_cuda12_portable_smoke.json --smoke cuda11=runs\checkpoints\s2_gate_194_cuda11_portable_smoke.json --smoke cpu=runs\checkpoints\s2_gate_194_cpu_portable_smoke.json --require-same-source-stamp --out runs\checkpoints\s2_gate_194_strict_windows_package_suite.json --markdown runs\checkpoints\s2_gate_194_strict_windows_package_suite.md --fail-on-failure
.\.venv\Scripts\glass.exe windows-release-manifest --suite runs\checkpoints\s2_gate_194_strict_windows_package_suite.json --require-same-source-stamp --out runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --markdown runs\checkpoints\s2_gate_194_strict_windows_release_manifest.md --fail-on-failure
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Full ruff: passed.
- Full pytest: `470 passed in 27.23s`.
- GLASS doctor: CUDA native extension loaded and CUDA available.

## Package Result

- Strict suite status: `package_suite_ready`.
- Strict manifest status: `release_manifest_ready`.
- Source stamps: `aa63510`.
- Failed checks: none.

## Rebuilt Packages

- `cuda13`: size `341358345` bytes,
  SHA256 `bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273`.
- `cuda12`: size `341223006` bytes,
  SHA256 `72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31`.
- `cuda11`: size `342200540` bytes,
  SHA256 `2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681`.
- `cpu`: size `296231852` bytes,
  SHA256 `32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d`.

## CUDA Status

- CUDA wrapper importable: `true`.
- CUDA native extension loaded: `true`.
- CUDA available: `true`.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`.

## Artifacts

- External root:
  `C:\glass_runs\phase2_s2_gate_194_strict_windows_packages`
- Build plan:
  `runs\checkpoints\s2_gate_194_build_plan.json`
- Package smoke artifacts:
  `runs\checkpoints\s2_gate_194_cuda13_portable_smoke.json`,
  `runs\checkpoints\s2_gate_194_cuda12_portable_smoke.json`,
  `runs\checkpoints\s2_gate_194_cuda11_portable_smoke.json`,
  `runs\checkpoints\s2_gate_194_cpu_portable_smoke.json`
- Strict suite:
  `runs\checkpoints\s2_gate_194_strict_windows_package_suite.json`
- Strict manifest:
  `runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json`

## Known Limitations

- This gate does not sign, upload, or create a GitHub release.
- The package zips live under `.release\windows` and are not committed to Git.
- CUDA13 build output included repeated NVIDIA header C4819 code-page warnings
  on this Chinese Windows environment; the build still completed and package
  smoke passed.
- No new real-data image-processing benchmark was run in this gate.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS build scripts, GLASS package artifacts, and GLASS
  doctor output.
- No input image directory was modified.

## Next Step

- Upload the strict package zips plus strict manifest to a Windows release, or
  return to the next Phase 2 algorithm-hardening gate.
