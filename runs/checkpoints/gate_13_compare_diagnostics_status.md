# Gate 13 Compare Diagnostics Status

## Gate

Gate 13 support checkpoint: PixInsight/WBPP black-box comparison diagnostics.

## Completed Content

- Added optional compare diagnostics through `gpwbpp compare --diagnostics-dir`.
- The diagnostics writer uses only the Python standard library and NumPy:
  - no Pillow dependency;
  - no matplotlib dependency;
  - no CUDA dependency.
- Diagnostic outputs:
  - `gpwbpp_preview.png`;
  - `reference_preview.png`;
  - `abs_diff_preview.png`;
  - `signed_diff_preview.png`;
  - `hotspots.json`.
- Added residual hotspot ranking by tiled p99 absolute difference and RMS difference.
- Added `gpwbpp compare --ignore-border-px` to compute metrics on an inner comparison region while preserving full-frame stats.
- Added pytest coverage for FITS-to-FITS compare diagnostics.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\report\compare_report.py src\gpwbpp\cli.py tests\test_compare_report.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_report.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_diagnostics.html" --gpwbpp-time-seconds 111.94882199994754 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident CUDA triangle Lanczos3 193 WBPP-failed-excluded scaled diagnostics" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 8.764434957115609e-06 --gpwbpp-offset 0.0006274500691899127 --diagnostics-dir "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_diagnostics" --diagnostic-max-size 1200 --hotspot-tile-size 512
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_inner32.html" --gpwbpp-time-seconds 111.94882199994754 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident CUDA triangle Lanczos3 inner32 scaled" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 8.764434957115609e-06 --gpwbpp-offset 0.0006274500691899127 --ignore-border-px 32
.\.venv\Scripts\python.exe -c "<coverage hotspot audit; see checkpoint text>"
```

## Test Results

- Ruff: passed.
- Targeted tests: `8 passed in 0.29s`.
- Full test suite: `163 passed in 7.87s`.

## Real-data Diagnostic Results

- Compare report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_diagnostics.html`.
- Diagnostics directory: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_diagnostics`.
- Top residual hotspots are concentrated along the lower image edge, especially the lower-right edge tiles.
- The highest hotspot tile was:
  - `x0=9216, x1=9600, y0=6144, y1=6422`;
  - `p99_abs_diff=0.3183833146095277`;
  - `rms_diff=0.07569983121093987`;
  - `max_abs_diff=0.5095405578613281`.
- Inner 32px-border-excluded compare:
  - report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_inner32.html`;
  - compared shape: `6358 x 9536`;
  - speedup: `9.75928982978054x`;
  - RMS difference: `0.002586615126210406`;
  - absolute difference p50: `7.196736987680197e-05`;
  - absolute difference p90: `0.00013417215086519718`;
  - absolute difference p99: `0.0004922153893858194`;
  - absolute difference p99.9: `0.007113467752119362`.
- Coverage audit:
  - global coverage min/max/mean: `1.0 / 193.0 / 190.4384307861328`;
  - global coverage p1/p50: `120.0 / 192.0`;
  - the highest residual hotspot tile had coverage min `11.0`, p1 `22.0`, median `191.0`;
  - the top hotspot tiles are therefore dominated by low-coverage edge pixels rather than a full-frame alignment failure.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- Diagnostic PNGs are downsampled previews intended for audit and triage, not scientific measurement.
- Hotspot ranking uses fixed image tiles, so a boundary artifact can dominate the list if edge policies differ.
- The current compare report records diagnostic file paths in JSON, but the generic HTML report does not yet embed thumbnail images inline.

## Next Step

- Investigate whether the bottom-edge residual concentration comes from coverage/crop policy, WBPP FastIntegration boundary handling, or Lanczos clamping behavior.

## Clean-room Compliance

- Compliant. Diagnostics compare only GPWBPP output against user-generated PixInsight/WBPP black-box output.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
