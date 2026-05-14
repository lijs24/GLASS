# Windows Release Plan

This document describes the first Windows-only distribution plan for GLASS.

## Release Artifacts

| Artifact | Audience | Notes |
| --- | --- | --- |
| `GLASS-Portable-win64.zip` | Most beta testers | Unpack and run `glass.cmd` or `glass-doctor.cmd`. |
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

The first public CUDA track should target CUDA 12 on Windows x64. The portable
builder can build the native module with either shared or static CUDA runtime
linkage:

```powershell
.\packaging\windows\build_portable.ps1 -BuildCuda -StaticCudaRuntime
```

For broad public releases, prefer static CUDA runtime linkage unless testing
shows a strong reason to ship dynamic CUDA DLLs. GLASS still relies on the
installed NVIDIA display driver.

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
- Portable zip starts on a clean Windows test account.
- Installer runs `glass-doctor.cmd` after install.
- No `runs/`, `.venv/`, `build/`, `.pdb`, `.ilk`, or local data files are
  included in the source distribution or portable artifact except the runtime
  intentionally created by the portable builder.
