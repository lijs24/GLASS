# Gate 08 Increment: Resident Star-Catalog Auto Threshold

- Gate: 08
- Date: 2026-05-13
- Status: completed
- Commit: pending

## Completed

- Added resident CUDA star-catalog auto-threshold mode.
- `--resident-star-threshold 0` now derives mean-plus-sigma threshold trials
  from GPU global frame statistics, scores each star-catalog translation on the
  GPU, and selects the result with the strongest mutual-inlier support.
- Kept fixed-threshold behavior unchanged for positive
  `--resident-star-threshold` values.
- Recorded threshold mode, sigma trial list, selected threshold, and trial
  candidates in resident registration diagnostics.
- Added a two-light synthetic FITS CLI test with a known integer shift. The
  auto-threshold resident star-catalog path estimates the expected alignment
  transform and applies resident bilinear warp before integration.
- Updated CUDA and registration docs.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cuda_resident_stack.py
.\.venv\Scripts\python.exe -m pytest -q
git diff --check
```

## Test Result

- Ruff: all checks passed.
- Targeted resident CUDA tests: 18 passed.
- Full pytest: 107 passed in 5.95 s.
- `git diff --check`: no whitespace errors.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend loaded: true.

## Known Limitations

- Auto-threshold uses global mean/std trials rather than a full device-side
  percentile histogram.
- Registration remains translation-only.
- Similarity, affine, homography, star descriptors, and Lanczos warp remain
  later registration/warp work.
- CPU still orchestrates the trial loop and receives compact diagnostics, but
  full-frame pixels remain resident on the GPU during threshold scoring and
  warp.

## Next Step

- Use the auto-threshold resident star-catalog mode on a real M38 subset and
  compare it against the existing resident NCC/astroalign timing artifacts.
- Then promote the best resident registration mode into the 200-light full
  comparison run.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- The implementation is based on project-owned CUDA/Python code and synthetic
  FITS tests.
- Input data directories were not modified.
