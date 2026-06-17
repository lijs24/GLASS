# Windows Release Plan

This document describes the first Windows-only distribution plan for GLASS.

## Release Artifacts

| Artifact | Audience | Notes |
| --- | --- | --- |
| `GLASS-Portable-win64.zip` | Most beta testers | Unpack and run `glass.cmd` or `glass-doctor.cmd`; the package contains its own relocatable Python runtime. |
| `GLASS-Setup-win64.exe` | Ordinary Windows users | Installer built from the portable folder with Inno Setup. |
| `glass-stack` wheel/sdist | Python users | CPU-capable package, useful for scripts and development. |
| Future `glass-cuda-cu12` wheel | NVIDIA users | CUDA native module package once binary wheel build is separated. |

## User Prerequisites

Ordinary GPU users should need:

- Windows x64.
- A recent NVIDIA driver.
- Enough RAM/VRAM for the selected processing mode.

They should not need:

- CUDA Toolkit.
- Visual Studio Build Tools.
- CMake.
- Ninja.

Those tools are only for source builds.

## CUDA Compatibility Strategy

Windows releases are split into CPU, CUDA 11, CUDA 12, and CUDA 13 portable
packages. GPU users should not need the CUDA Toolkit, Visual Studio, CMake, or
Ninja. Each CUDA portable package includes the GLASS native module plus the CUDA
runtime components that are redistributable for that toolkit line; the installed
NVIDIA display driver still provides the kernel driver and PTX JIT.

The preferred package is the newest package with native GPU code for the target
card. Newer GPUs can also try older CUDA packages when their NVIDIA driver
supports the bundled runtime: those packages use PTX forward JIT instead of a
native cubin for the newest architecture. This gives a practical fallback path,
although first launch may be slower and peak performance can be lower than the
native package.

Current Windows CUDA package intent:

| Package | Toolkit | Native targets | Compatibility fallback |
| --- | --- | --- | --- |
| `cuda11` | 11.8 | 5.0, 5.2, 6.0, 6.1, 7.0, 7.5, 8.0, 8.6 | Newer GPUs through PTX JIT if the installed driver supports CUDA 11.8 runtime loading. |
| `cuda12` | 12.4 | 7.5, 8.0, 8.6, 8.9, 9.0 | Newer GPUs through PTX JIT if the installed driver supports CUDA 12.4 runtime loading. |
| `cuda13` | 13.0 | 8.6, 8.9, 9.0, 10.0, 12.0 | Preferred for Blackwell-class cards and later CUDA 13-era systems. |

For example, an RTX PRO 6000 Blackwell machine should try `cuda13` first for
native `sm_120` performance, but `cuda12` and `cuda11` are valid fallback
attempts on a sufficiently new driver. `glass doctor` reports this package try
order on the target machine.

The portable builder can build the native module with either shared or static
CUDA runtime linkage:

```powershell
.\packaging\windows\build_portable.ps1 -BuildCuda -StaticCudaRuntime
```

For broad public releases, prefer static CUDA runtime linkage unless testing
shows a strong reason to ship dynamic CUDA DLLs.
The builder also copies any `cudart64_*.dll` from the selected CUDA Toolkit into
the package. Some Toolkit/MSVC combinations still leave a runtime DLL import
even when static linkage is requested, so the portable zip must carry that
redistributable DLL for reliable loading.

The portable builder copies the base Python runtime into the package before
installing GLASS and its dependencies. This avoids non-relocatable virtual
environment launchers that point back to a build-machine Python path.

## Build Commands

CPU-capable Python distribution:

```powershell
.\packaging\windows\build_wheel.ps1
```

Portable folder without CUDA:

```powershell
.\packaging\windows\build_portable.ps1
```

Portable folder with CUDA native module:

```powershell
.\packaging\windows\build_portable.ps1 -BuildCuda -StaticCudaRuntime
```

Portable folder with an explicit release label:

```powershell
.\packaging\windows\build_portable.ps1 -BuildCuda -StaticCudaRuntime -PackageLabel cuda13
```

The label changes the zip name, for example
`GLASS-Portable-win64-cuda13.zip`, and is recorded in
`package_manifest.json` alongside the CUDA build flag, CUDA architecture
setting, selected Toolkit root, runtime linkage, Python home, and source stamp.

Before building multiple variants, generate a local build plan:

```powershell
glass windows-package-build-plan --out windows_package_build_plan.json --markdown windows_package_build_plan.md
```

The plan is read-only. It reports which package labels are build-ready on the
current machine, which CUDA Toolkit roots are missing, and the exact
`build_portable.ps1` command for each ready variant. Use `--fail-on-missing` or
`--require-all-toolkits` in CI/release automation when all CUDA variants must be
present.

When CUDA12/CUDA11 Toolkits are missing, use the minimal installer helper rather
than a default full Toolkit install:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/install_cuda_toolkit_minimal.ps1 -Label cuda12
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/install_cuda_toolkit_minimal.ps1 -Label cuda12 -Download
powershell -NoProfile -ExecutionPolicy Bypass -File packaging/windows/install_cuda_toolkit_minimal.ps1 -Label cuda12 -Install
```

The helper defaults to plan-only mode. The `-Install` path requests only the
`nvcc` and `cudart` Toolkit components for the selected label and does not
request display driver components. Rerun `glass windows-package-build-plan`
after installation to verify `nvcc.exe` discovery.

After installing a missing Toolkit, verify it before building:

```powershell
glass windows-package-build-plan --out windows_package_build_plan_after_install.json --markdown windows_package_build_plan_after_install.md
```

Installer:

1. Build the portable folder.
2. Open `packaging/windows/GLASS.iss` in Inno Setup.
3. Compile `GLASS-Setup-win64.exe`.

## Release Checklist

- Branding and package-name checks return no stale tracked matches.
- `python -m pytest -q` passes.
- `glass doctor --allow-cpu-only` succeeds.
- CUDA machine: `glass doctor` reports native CUDA available.
- CUDA smoke tests pass on the release machine.
- `glass windows-package-build-plan --out windows_package_build_plan.json
  --markdown windows_package_build_plan.md` is archived before building package
  variants; strict releases add `--fail-on-missing` after all target CUDA
  Toolkits are installed.
- `glass windows-release-matrix --doctor-json DOCTOR.json --release-decision
  RELEASE_DECISION.json --acceptance-audit ACCEPTANCE.json
  --expected-primary-package cuda13 --out windows_release_matrix.json
  --fail-on-not-ready` passes on the release GPU machine before publishing CUDA
  packages.
- `glass windows-package-smoke --package-root .release\windows\GLASS --zip
  .release\windows\GLASS-Portable-win64.zip --out windows_package_smoke.json
  --fail-on-failure` passes for every portable package variant before upload.
- CUDA package variants use the labeled zip and require CUDA in the package
  smoke:

```powershell
glass windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64-cuda13.zip --expected-package-label cuda13 --require-cuda --out windows_package_smoke_cuda13.json --fail-on-failure
```

- After all package variants pass individual smoke tests, aggregate them into a
  suite artifact:

```powershell
glass windows-package-suite --smoke cuda13=windows_package_smoke_cuda13.json --smoke cuda12=windows_package_smoke_cuda12.json --smoke cuda11=windows_package_smoke_cuda11.json --smoke cpu=windows_package_smoke_cpu.json --out windows_package_suite.json --markdown windows_package_suite.md --require-same-source-stamp --fail-on-failure
```

- Record final release file sizes and SHA256 checksums:

```powershell
glass windows-release-manifest --suite windows_package_suite.json --out windows_release_manifest.json --markdown windows_release_manifest.md --require-same-source-stamp --fail-on-failure
```

- Before uploading, generate release notes and the exact GitHub upload command:

```powershell
glass windows-github-release-plan --manifest windows_release_manifest.json --tag v0.1.0-windows-gpu.N --title "GLASS v0.1.0-windows-gpu.N Windows CUDA packages" --out github_release_plan.json --markdown github_release_plan.md --notes github_release_notes.md --require-same-source-stamp --check-gh --fail-on-failure
```

- Release-grade 200-light acceptance uses the benchmark contract plus
  `--pipeline-contract-json`, and all `contract_pipeline_contract_*` checks pass.
- Acceptance Markdown and HTML report show the release pipeline-contract
  evidence section for the same run.
- Candidate/runtime sweep plans include a `pipeline_contract` step before
  `acceptance_audit`.
- Portable zip starts on a clean Windows test account.
- Installer runs `glass-doctor.cmd` after install.
- No `runs/`, `.venv/`, `build/`, `.pdb`, `.ilk`, or local data files are
  included in the source distribution or portable artifact except the runtime
  intentionally created by the portable builder.
