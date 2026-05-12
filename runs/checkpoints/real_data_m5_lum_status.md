# Real Data Status: M5 Lum Subset

- Date: 2026-05-12
- Status: GPWBPP real-data CUDA smoke completed

## Input

- Source root: `E:\摄影素材\天协远程台原始素材\远程台240430`
- Selected target/filter: M5 / Lum
- Selection method: manifest-only subset referencing original files without copying or modifying them
- Frames:
  - 1 bias
  - 1 dark, 600 s
  - 1 Lum flat
  - 2 Lum lights, 600 s

## Commands Run

```powershell
.\.venv\Scripts\gpwbpp plan --manifest runs\real_m5_lum_subset\manifest.json --out runs\real_m5_lum_subset\processing_plan.json
.\.venv\Scripts\gpwbpp run --plan runs\real_m5_lum_subset\processing_plan.json --out runs\real_m5_lum_subset\gpwbpp_cuda_v2 --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 1024
.\.venv\Scripts\gpwbpp report --run runs\real_m5_lum_subset\gpwbpp_cuda_v2 --manifest runs\real_m5_lum_subset\manifest.json --plan runs\real_m5_lum_subset\processing_plan.json --out runs\real_m5_lum_subset\gpwbpp_cuda_v2\report.html
.\.venv\Scripts\python -m pytest -q
```

## Result

- Processing plan executable: true.
- `gpwbpp subset` reproduced an executable 5-frame M5/Lum manifest from the full 240430 manifest.
- GPWBPP CUDA elapsed time: 64.061 seconds.
- GPWBPP CUDA tile-reader repeat on the same plan: 42.051 seconds.
- Tile-reader repeat compared against the previous run with `rms_diff = 0.0` and `max_abs_diff = 0.0`.
- Integration backend: cuda.
- Integration tiles: 70.
- Final master: `runs\real_m5_lum_subset\gpwbpp_cuda_v2\integration\master_Lum.fits`.
- Report: `runs\real_m5_lum_subset\gpwbpp_cuda_v2\report.html`.
- Full test suite after scaled-FITS fix: 40 passed.

## Real Data Issue Found

The first real-data attempt failed because the input FITS files contain
`BZERO/BSCALE/BLANK` scaling keywords. Astropy does not allow direct memmap
access to scaled `.data`. GPWBPP first used a `memmap=False` fallback, then
added `FitsImageReader` to apply scaling per tile for light calibration, warp,
local normalization, and integration.

## Known Limitations

- Master calibration frame construction still uses full-frame CPU arrays.
- This is not yet a PixInsight/WBPP timing comparison.
- The subset is intentionally tiny and is only a real-data smoke test.

## Clean-room Compliance

- Original data directories were not modified.
- No official PixInsight WBPP/PJSR source was read, copied, summarized, or modified.
