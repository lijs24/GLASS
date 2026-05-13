# GLASS

**GLASS** is the **GPU-Accelerated Lightframe Alignment and Stacking System**:
a clean-room deep-sky image calibration, alignment, rejection, and integration
engine with a CPU baseline and an optional CUDA resident backend.

The project is designed for large FITS/XISF datasets. It uses staged manifests,
processing plans, resumable run state, diagnostic artifacts, HTML reports, and
out-of-core or full-VRAM execution modes. On suitable NVIDIA hardware, the
resident CUDA path keeps calibrated light frames in VRAM and minimizes round
trips through disk and host memory.

## Clean-Room Boundary

- GLASS does not read, copy, summarize, or rework official PixInsight WBPP/PJSR
  source code.
- PixInsight/WBPP may be used only as a black-box reference through
  user-generated logs, settings, and outputs.
- Input image directories are treated as read-only.

## Quick Start

```powershell
python -m pip install -e .[dev,report]
glass --help
glass doctor --allow-cpu-only
glass synthetic --out runs/demo_synth --frames 8 --width 128 --height 128 --filter H --known-shift
glass audit --root runs/demo_synth --out runs/demo_audit --backend cpu
python -m pytest -q
```

CUDA diagnostics:

```powershell
glass doctor
python -c "from glass.capabilities import capability_report; print(capability_report())"
```

## Main Commands

- `glass doctor`: diagnose Python, CUDA wrapper, native backend, GPU, driver, and fallback status.
- `glass scan`: recursively scan FITS/FIT/XISF metadata without loading full image pixels.
- `glass plan`: build `processing_plan.json` with calibration matching and warnings.
- `glass run`: execute staged CPU, tile CUDA, or resident CUDA processing.
- `glass resume`: summarize and resume-safe state for an existing run directory.
- `glass report`: generate an HTML report from run artifacts.
- `glass audit`: scan, plan, run, and report in one command.
- `glass compare`: compare a GLASS master with a black-box reference master.
- `glass synthetic`: generate controlled FITS fixtures for correctness tests.

## Windows Distribution Strategy

Ordinary Windows users should not need the CUDA Toolkit. The target release
shape is a portable folder or installer that includes Python, GLASS,
dependencies, and the optional native CUDA module. Users only need a compatible
NVIDIA driver for GPU acceleration.

Release helpers live in `packaging/windows/`:

```powershell
.\packaging\windows\build_portable.ps1 -BuildCuda -StaticCudaRuntime
.\packaging\windows\build_wheel.ps1
```

See [docs/project_overview.md](docs/project_overview.md) and
[docs/windows_release.md](docs/windows_release.md) for the project and release
model.
