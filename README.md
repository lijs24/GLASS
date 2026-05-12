# GPWBPP

GPWBPP is a clean-room, open implementation of a WBPP-like astronomical image
preprocessing pipeline with a CPU baseline and an optional CUDA backend.

The project is gate-driven. Early gates provide metadata scanning, planning,
synthetic FITS data, CPU calibration, reporting, and resumable state files.
Later gates add CUDA tile kernels, registration, local normalization, weighted
integration, diagnostic maps, and black-box comparison against user-generated
PixInsight/WBPP outputs.

Clean-room boundary:

- This repository does not read, copy, summarize, or rework official
  PixInsight WBPP/PJSR source code.
- PixInsight may only be used as a black-box reference through user-generated
  logs, settings, and outputs.
- Input image directories are treated as read-only.

Quick start:

```powershell
python -m pip install -e .[dev,report]
gpwbpp --help
gpwbpp synthetic --out runs/demo_synth --frames 8 --width 128 --height 128 --filter H --known-shift
gpwbpp audit --root runs/demo_synth --out runs/demo_audit --backend cpu
python -m pytest -q
```

Current capability flags are reported by:

```powershell
python -c "from gpwbpp.capabilities import capability_report; print(capability_report())"
```

