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
- Added `gpwbpp blackbox-package` to export a clean-room WBPP handoff package.
- Generated a real M5/Lum handoff package with the measured GPWBPP runtime filled in.
- Added `gpwbpp subset` to select a small same-target/same-filter manifest without copying or modifying original files.
- Verified `gpwbpp subset` can recreate an executable real M5/Lum subset from the 240430 manifest.

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
.\.venv\Scripts\python -m pytest -q tests/test_blackbox_package.py
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\gpwbpp blackbox-package --manifest runs\real_m5_lum_subset\manifest.json --plan runs\real_m5_lum_subset\processing_plan.json --gpwbpp-run runs\real_m5_lum_subset\gpwbpp_cuda_v2 --gpwbpp-time-seconds 64.061 --out runs\real_m5_lum_subset\wbpp_blackbox_handoff --reference-label "PixInsight WBPP"
.\.venv\Scripts\gpwbpp subset --manifest runs\local_audit_240430\manifest.json --out runs\real_m5_lum_subset\subset_cli_manifest.json --plan-out runs\real_m5_lum_subset\subset_cli_processing_plan.json --object M5 --filter Lum --light-limit 2 --bias-limit 1 --dark-limit 1 --flat-limit 1
.\.venv\Scripts\python -m pytest -q tests/test_subset.py
```

## Handoff Artifacts

- `runs\real_m5_lum_subset\wbpp_blackbox_handoff\input_frames.csv`
- `runs\real_m5_lum_subset\wbpp_blackbox_handoff\wbpp_manual_run.md`
- `runs\real_m5_lum_subset\wbpp_blackbox_handoff\timing_template.json`
- `runs\real_m5_lum_subset\wbpp_blackbox_handoff\compare_command.ps1`
- `runs\real_m5_lum_subset\subset_cli_manifest.json`
- `runs\real_m5_lum_subset\subset_cli_processing_plan.json`

## Next Step

- Provide the PixInsight executable path, or
- run WBPP manually on `runs\real_m5_lum_subset\manifest.json` selected files and provide the WBPP output master/log, or
- install PixInsight in a known location, then rerun the black-box timing protocol.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or modified.
- The blocker is tool availability, not implementation dependence on PixInsight internals.
