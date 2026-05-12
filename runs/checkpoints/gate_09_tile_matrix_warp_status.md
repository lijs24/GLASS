# Gate 09 Increment: Tile-Streaming Matrix Bilinear Warp

Date: 2026-05-13

## Gate

Gate 09 / warp streaming increment.

## Completed Content

- Added tile-streaming bilinear matrix warp for the non-resident CPU/tile pipeline.
- `warp_registered_frames(...)` now:
  - preserves the existing integer-translation nearest-neighbor fast path;
  - uses bilinear matrix warp for fractional translation, similarity, affine, and other invertible 3x3 matrices;
  - reads only the source bounding box needed for each output tile;
  - writes registered frame and coverage maps tile by tile.
- Added `warp_model` and full `matrix` to each `warp_results.json` row.
- Added CPU tests for:
  - fractional translation matrix bilinear warp;
  - integer translation fast-path preservation.
- Updated `docs/registration_model.md` to reflect that optional astroalign similarity matrices can now flow into tile-mode warp/integration.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\warp.py tests\test_cpu_warp.py docs\registration_model.md
```

Result: `All checks passed!`

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_warp.py tests\test_cpu_registration.py tests\test_pipeline_fixture.py
```

Result: `22 passed in 3.97s`

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: `114 passed in 6.35s`

## CUDA Availability

CUDA is available, but this increment implements the CPU/tile baseline warp path.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB

## Known Limitations

- This is a CPU/tile warp baseline. GPU similarity/affine warp is still future work.
- Homography matrices are accepted only insofar as the inverse 3x3 sampling math is valid; no astrometric distortion model or Lanczos kernel is implemented yet.
- Resident high-VRAM mode still applies translation-only resident CUDA warp.
- The integer-translation fast path remains nearest-neighbor to preserve previous behavior.

## Next Step

Port the matrix bilinear warp primitive to CUDA and expose it through resident frames, then connect the open-source astroalign/star descriptor path to a GPU-owned similarity/affine estimator.

## Clean-Room Compliance

Compliant. This warp implementation is project-owned numerical code using general image resampling math. It does not read, copy, summarize, or modify PixInsight/WBPP/PJSR source code.
