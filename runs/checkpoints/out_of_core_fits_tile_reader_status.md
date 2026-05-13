# Out-of-core FITS Tile Reader Status

- Date: 2026-05-12
- Status: improved

## Completed

- Added `FitsImageReader` for raw memmapped FITS tile reads.
- `FitsImageReader` applies `BSCALE`/`BZERO` per tile.
- `FitsImageReader` maps `BLANK` pixels to `NaN`.
- Updated light calibration, warp, local normalization, and integration paths to use tile reads instead of relying on scaled `.data` fallback.
- Retained the older `open_fits_image` helper for compatibility.

## Commands Run

```powershell
.\.venv\Scripts\python -m pytest -q tests/test_fits_io.py tests/test_pipeline_fixture.py::test_pipeline_fixture_run_integration
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\glass run --plan runs\real_m5_lum_subset\processing_plan.json --out runs\real_m5_lum_subset\glass_cuda_tile_reader_manual --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 1024
.\.venv\Scripts\glass compare --glass runs\real_m5_lum_subset\glass_cuda_tile_reader_manual\integration\master_Lum.fits --reference runs\real_m5_lum_subset\glass_cuda_v2\integration\master_Lum.fits --out runs\real_m5_lum_subset\tile_reader_manual_vs_previous.html
```

## Test Result

- Focused FITS/pipeline tests: 3 passed.
- Full suite: 52 passed.
- Real M5/Lum tile-reader run: 42.051 seconds.
- Comparison with previous Astropy scaled fallback run on the same plan: `rms_diff = 0.0`, `max_abs_diff = 0.0`.

## Artifacts

- `runs\real_m5_lum_subset\glass_cuda_tile_reader_manual\integration\master_Lum.fits`
- `runs\real_m5_lum_subset\tile_reader_manual_vs_previous.html`
- `runs\real_m5_lum_subset\tile_reader_manual_vs_previous.json`

## Known Limitations

- Master bias/dark/flat generation still uses full-frame CPU arrays in the current pipeline path.
- Warp is tile-streamed but still nearest-neighbor translation only.
- A future optimization should make master frame construction fully tile streaming in the high-level pipeline.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or modified.
- Original data directories were not modified.
