# S2-Gate 184 Status: CUDA13 Portable Package Smoke

## Gate

- Gate: S2-Gate 184
- Scope: build and smoke-test a CUDA13 Windows portable package.
- Status: green
- Date: 2026-06-17

## Completed

- Added `-PackageLabel` support to `packaging/windows/build_portable.ps1`.
- Added package manifest emission with package label, CUDA build flag,
  architecture setting, selected CUDA Toolkit root, runtime linkage, Python
  home, and source stamp.
- Wrote `package_manifest.json` without UTF-8 BOM.
- Made JSON reads tolerant of UTF-8 BOM for older generated artifacts.
- Added `PYTHONNOUSERSITE=1` isolation to portable launchers and build-time
  portable pip usage.
- Added Visual Studio C++ environment import via `vswhere.exe` and
  `vcvars64.bat` when `cl.exe` is not already on `PATH`.
- Extended `glass windows-package-smoke` with
  `--expected-package-label` and `--require-cuda`.
- Built `.release\windows\GLASS-Portable-win64-cuda13.zip`.
- Smoke-tested the portable package with CUDA required.
- Updated Phase 2, algorithm source, and Windows release documentation.

## Commands Run

```powershell
$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path packaging\windows\build_portable.ps1), [ref]$tokens, [ref]$errors)
.\.venv\Scripts\ruff.exe check src\glass\io\json_io.py src\glass\report\windows_package_smoke.py src\glass\cli.py tests\test_windows_package_smoke.py tests\test_windows_packaging_scripts.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_package_smoke.py tests\test_windows_packaging_scripts.py
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\build_portable.ps1 -Python .\.venv\Scripts\python.exe -BuildCuda -StaticCudaRuntime -CudaArchitectures native -PackageLabel cuda13
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda13.zip --expected-source 245c2f9 --expected-package-label cuda13 --require-cuda --out C:\glass_runs\phase2_s2_gate_184_cuda13_package_smoke\cuda13_portable_smoke.json --markdown C:\glass_runs\phase2_s2_gate_184_cuda13_package_smoke\cuda13_portable_smoke.md --fail-on-failure
.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda13.zip --expected-source 245c2f9 --expected-package-label cuda13 --require-cuda --out runs\checkpoints\s2_gate_184_cuda13_portable_smoke.json --markdown runs\checkpoints\s2_gate_184_cuda13_portable_smoke.md --fail-on-failure
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- PowerShell parser: passed.
- Focused ruff: passed.
- Focused pytest: `4 passed`.
- Full ruff: passed.
- Full pytest: `458 passed in 23.40s`.
- CUDA-required package smoke: passed.

## CUDA / Package Result

- CUDA available: yes.
- Portable CUDA native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA Toolkit used for build: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2`.
- CUDA runtime linkage requested: Static.
- Package label: `cuda13`.
- Package source stamp: `245c2f9`.
- Zip: `.release\windows\GLASS-Portable-win64-cuda13.zip`.
- Zip size: `339732356` bytes.
- Package manifest starts with `{` (`123 13 10`), confirming no UTF-8 BOM.

## Artifacts

- External smoke JSON:
  `C:\glass_runs\phase2_s2_gate_184_cuda13_package_smoke\cuda13_portable_smoke.json`
- External smoke Markdown:
  `C:\glass_runs\phase2_s2_gate_184_cuda13_package_smoke\cuda13_portable_smoke.md`
- Checkpoint smoke JSON:
  `runs\checkpoints\s2_gate_184_cuda13_portable_smoke.json`
- Checkpoint smoke Markdown:
  `runs\checkpoints\s2_gate_184_cuda13_portable_smoke.md`
- Prebuild doctor:
  `runs\checkpoints\s2_gate_184_prebuild_doctor.json`
- Package manifest:
  `.release\windows\GLASS\package_manifest.json`

## Failure Repaired During Gate

- Initial CUDA portable build could not find a C++ compiler in the package
  build environment.
- Fixed by importing the Visual Studio Build Tools environment with
  `vswhere.exe` and `vcvars64.bat` before CUDA CMake configure.
- Initial package-smoke read of `package_manifest.json` hit a UTF-8 BOM from
  PowerShell `Set-Content -Encoding UTF8`.
- Fixed by writing the manifest with .NET `UTF8Encoding(false)` and making
  JSON reads tolerate `utf-8-sig`.

## Known Limitations

- This gate built and smoked only the `cuda13` package on the local release
  machine.
- CUDA11 and CUDA12 package artifacts are planned by the release matrix but
  were not built or smoked in this gate.
- The portable package source stamp is `245c2f9` because the package was built
  before this Gate184 commit exists. Formal release artifacts should be rebuilt
  after the final release commit so the source stamp exactly matches the
  published code.
- The package is not signed and no installer was produced in this gate.
- This gate validates package startup and CUDA loading, not the 200-light
  benchmark runtime.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS package artifacts and GLASS doctor output.
- No input image directory was modified.

## Next Step

- Build and smoke the CUDA12 and CUDA11 variants, or rebuild the CUDA13 package
  after the Gate184 commit for a publishable source-stamped artifact.
