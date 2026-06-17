# S2-Gate 185 Status: Windows Package Build Plan

## Gate

- Gate: S2-Gate 185
- Scope: add a read-only Windows CPU/CUDA portable package build preflight.
- Status: green
- Date: 2026-06-17

## Completed

- Added `glass windows-package-build-plan`.
- Added Toolkit discovery for local Windows CUDA Toolkit roots.
- Planned package variants for `cuda13`, `cuda12`, `cuda11`, and `cpu`.
- Recorded package labels, package zip paths, shared package-root behavior,
  CMake CUDA architecture strings, build-ready status, missing-toolkit reasons,
  and copy-pasteable `build_portable.ps1` commands.
- Added `--toolkit-root LABEL=PATH`, `--packages`, `--release-root`,
  `--python`, `--configuration`, `--shared-cuda-runtime`,
  `--require-all-toolkits`, `--fail-on-missing`, and `--fail-on-failure`.
- Added focused tests for current-machine-like CUDA13-only planning, strict
  missing-toolkit blocking, CLI JSON/Markdown writes, and Toolkit discovery.
- Updated Phase 2, algorithm source, and Windows release documentation.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\windows_package_build_plan.py src\glass\cli.py tests\test_windows_package_build_plan.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_package_build_plan.py tests\test_cli_smoke.py
.\.venv\Scripts\glass.exe windows-package-build-plan --out C:\glass_runs\phase2_s2_gate_185_windows_package_build_plan\windows_package_build_plan.json --markdown C:\glass_runs\phase2_s2_gate_185_windows_package_build_plan\windows_package_build_plan.md
.\.venv\Scripts\glass.exe windows-package-build-plan --out runs\checkpoints\s2_gate_185_windows_package_build_plan.json --markdown runs\checkpoints\s2_gate_185_windows_package_build_plan.md
.\.venv\Scripts\glass.exe windows-package-build-plan --help
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused ruff: passed.
- Focused pytest: `19 passed in 1.72s`.
- CLI help: passed.
- Full ruff: passed.
- Full pytest: `463 passed in 22.91s`.

## Real Preflight Result

- Status: `partial_toolkits`.
- Passed: `true`.
- Recommendation: `build_ready_variants_and_install_missing_toolkits`.
- Ready variants: `cuda13`, `cpu`.
- Missing CUDA variants: `cuda12`, `cuda11`.
- Detected Toolkit: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2`.
- Detected nvcc: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe`.
- `cuda13` Toolkit match: `major_compatible`.
- Planned `cuda13` architectures: `86;89;90;100;120`.
- Planned `cuda12` architectures: `75;80;86;89;90`.
- Planned `cuda11` architectures: `50;52;60;61;70;75;80;86`.

## Artifacts

- External build plan JSON:
  `C:\glass_runs\phase2_s2_gate_185_windows_package_build_plan\windows_package_build_plan.json`
- External build plan Markdown:
  `C:\glass_runs\phase2_s2_gate_185_windows_package_build_plan\windows_package_build_plan.md`
- Checkpoint build plan JSON:
  `runs\checkpoints\s2_gate_185_windows_package_build_plan.json`
- Checkpoint build plan Markdown:
  `runs\checkpoints\s2_gate_185_windows_package_build_plan.md`

## CUDA

- CUDA runtime is available on this machine through the existing CUDA13 setup.
- Only CUDA Toolkit `v13.2` is installed under the default Toolkit base.
- CUDA12 and CUDA11 package builds require installing matching Toolkit major
  versions or passing explicit `--toolkit-root` overrides.

## Known Limitations

- This gate does not install CUDA Toolkits.
- This gate does not build packages.
- Toolkit matching is major-version based unless an exact version is present.
- Each `build_portable.ps1` invocation overwrites `.release\windows\GLASS`, so
  release automation must zip/smoke/archive each variant before building the
  next one.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate reads only local CUDA Toolkit directory metadata and GLASS files.
- No input image directory was modified.

## Next Step

- Install or locate CUDA12 and CUDA11 Toolkits, then rerun
  `glass windows-package-build-plan --fail-on-missing` before building those
  package variants.
