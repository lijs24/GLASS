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
- `glass windows-release-matrix --doctor-json DOCTOR.json --release-decision
  RELEASE_DECISION.json --acceptance-audit ACCEPTANCE.json
  --expected-primary-package cuda13 --out windows_release_matrix.json
  --fail-on-not-ready` passes on the release GPU machine before publishing CUDA
  packages.
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
