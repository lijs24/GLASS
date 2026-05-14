# GLASS Project Overview

**GLASS** means **GPU-Accelerated Lightframe Alignment and Stacking System**.

GLASS is an astronomical image preprocessing and stacking engine for deep-sky
data. The project implements metadata scan, planning, calibration,
registration, local normalization, rejection, integration, maps, and reporting
as a staged GPU-oriented pipeline.

## Design Goals

- Process large FITS/XISF image sets without requiring all intermediate files to
  live on disk.
- Keep a scientifically readable CPU baseline for every important numeric path.
- Use CUDA as an optional backend, not as a hard install requirement.
- Prefer resident VRAM execution when the GPU has enough memory.
- Preserve restartable state through manifests, plans, run states, checksums,
  and diagnostic artifacts.
- Keep every optimization measurable through timing JSON and validation reports.

## Pipeline Shape

1. Metadata scan
2. Grouping and calibration planning
3. Master bias, dark, and flat creation
4. Light calibration
5. Quality measurement and reference selection
6. Registration and warp
7. Optional local normalization
8. Weighted integration and rejection
9. Weight, coverage, and rejection maps
10. HTML report and validation summary

## Execution Modes

- `cpu`: correctness-first baseline.
- `cuda` tile mode: CUDA pixel kernels under an out-of-core execution model.
- `cuda` resident mode: upload calibrated light frames to VRAM and keep them
  resident for registration, warp, normalization, and integration when memory
  allows.

## Current Windows User Story

The intended Windows experience is:

1. Download `GLASS-Portable-win64.zip` or `GLASS-Setup-win64.exe`.
2. Run `glass doctor`.
3. If CUDA is available, use resident GPU mode automatically or explicitly.
4. If CUDA is unavailable, run the CPU path or update the NVIDIA driver.

The CUDA Toolkit is for developers building from source. It should not be a
normal user prerequisite.
