# Gate 13 Status: PixInsight/WBPP Black-box Comparison

- Gate: 13
- Date: 2026-05-12
- Status: blocked

## Completed

- Confirmed GPWBPP can run a real M5/Lum subset end to end with CUDA.
- Recorded GPWBPP elapsed time for the real subset.
- Verified `gpwbpp compare` works for CPU/CUDA synthetic masters in Gate 12.
- Documented the black-box timing protocol in `docs/pixinsight_blackbox_reference.md`.
- Added `gpwbpp compare` timing fields for GPWBPP/reference elapsed seconds and speedup reporting.

## Blocker

`PixInsight.exe` was not found in PATH, common `Program Files` locations, or a
full C:/D:/E: filename search on this workstation. No user-generated WBPP output
or log was found under `E:\摄影素材\天协远程台原始素材` by filename search. Without a
callable local PixInsight installation or a user-generated WBPP output/log for
the exact same selected subset, Gate 13 cannot produce a valid WBPP timing or
numerical comparison.

## Commands Run

```powershell
Get-Command PixInsight.exe -ErrorAction SilentlyContinue
Get-ChildItem -Path 'C:\Program Files','C:\Program Files (x86)' -Filter PixInsight.exe -Recurse -ErrorAction SilentlyContinue
Get-PSDrive -PSProvider FileSystem | ForEach-Object { Get-ChildItem -LiteralPath $_.Root -Filter PixInsight.exe -Recurse -ErrorAction SilentlyContinue }
Get-ChildItem -LiteralPath 'E:\摄影素材\天协远程台原始素材' -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'WBPP|WeightedBatch|BatchPreprocessing|PixInsight' }
.\.venv\Scripts\python -m pytest -q tests/test_compare_report.py
```

## Next Step

- Provide the PixInsight executable path, or
- run WBPP manually on `runs\real_m5_lum_subset\manifest.json` selected files and provide the WBPP output master/log, or
- install PixInsight in a known location, then rerun the black-box timing protocol.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or modified.
- The blocker is tool availability, not implementation dependence on PixInsight internals.
