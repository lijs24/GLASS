# Gate 01 Increment: FITS PIERSIDE Metadata Summary

## Gate

Gate 01 - Metadata scan + plan + report.

## Completed Content

- Added `PIERSIDE`, `OBJCTROT`, and `ROTATOR` to FITS `header_summary`.
- Updated the small FITS fixture to include `PIERSIDE=West` and `OBJCTROT=92.0` on the light frame.
- Added metadata test assertions so orientation metadata remains visible in manifests and processing plans.
- This supports Gate 08 resident CUDA `auto_pierside` registration without relying on per-frame fallback FITS header reads for newly scanned data.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_fits_metadata.py tests/test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Targeted tests: `13 passed in 0.76s`
- Full suite: `151 passed in 7.50s`

## CUDA Availability

- CUDA is available.
- This metadata change is CPU-only and remains usable when CUDA is unavailable.

## Known Limitations

- Existing manifests/plans generated before this change still lack `PIERSIDE` unless they already carried it; resident CUDA keeps a metadata-only FITS header fallback for those older artifacts.
- XISF orientation metadata is not expanded in this increment.

## Next Step

Regenerate future real-data manifests/plans so `PIERSIDE` is captured in `header_summary`, then run a mixed pier-side real subset and the full 200-light timing comparison.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read or modified.
- Only FITS header metadata was added to the open GLASS scan summary.
- Input data directories were not modified.
