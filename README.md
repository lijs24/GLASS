# GLASS

**GLASS** is the **GPU-accelerated Lightframe Alignment and Stacking System**:
a deep-sky image calibration, alignment, rejection, and integration engine with
a CPU baseline and an optional CUDA resident backend.

The project is designed for large FITS/XISF datasets. It uses staged manifests,
processing plans, resumable run state, diagnostic artifacts, HTML reports, and
out-of-core or full-VRAM execution modes. On suitable NVIDIA hardware, the
resident CUDA path keeps calibrated light frames in VRAM and minimizes round
trips through disk and host memory. Input image directories are treated as
read-only.

## Real Dataset Benchmark

On a 200-light H-alpha M38 dataset with 20 bias, 20 dark, and 20 flat frames
at 9600x6422 pixels, the resident CUDA backend completed calibration,
alignment, rejection, and integration in about 30-32 seconds on an NVIDIA RTX
PRO 6000 Blackwell workstation. The WBPP reference run on the same data took
1092.541 seconds.

| Run | Time | Speedup vs WBPP | RMS vs reference | P99 abs diff | Shape |
| --- | ---: | ---: | ---: | ---: | --- |
| WBPP reference | 1092.541 s | 1.00x | reference | reference | 9600x6422 |
| GLASS CUDA 11 package | 30.361 s | 35.98x | 0.00155829 | 0.000430955 | match |
| GLASS CUDA 12 package | 30.515 s | 35.80x | 0.00155829 | 0.000430955 | match |
| GLASS CUDA 13 package | 32.004 s | 34.14x | 0.00155911 | 0.000430912 | match |

The CUDA 11 and CUDA 12 outputs were bit-identical in this run. CUDA 13 showed
only small floating-point/code-generation differences while keeping the same
reference-level image agreement. These numbers are a single workstation
measurement, but they show the intended GLASS execution model: keep the stack
resident in VRAM, reduce disk round trips, and make heavy alignment and stacking
work GPU-bound instead of storage-bound.

Current Phase 2 development builds have also been validated on the same
200-light data in a shared-master-cache resident hot path: the latest run
completed in 5.305 seconds wall time, used 193 active frames with 7 zero-weight
frames, matched the previous GLASS output bit-for-bit across all six output
maps, and measured a 205.94x wall-time speedup against the 1092.541-second WBPP
black-box reference. This hot-path number excludes rebuilding cached master
calibration frames; it is useful for tracking the resident GPU execution limit.

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
- `glass compare`: compare a GLASS master with a reference master.
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
