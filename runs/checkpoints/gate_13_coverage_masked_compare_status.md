# Gate 13 Coverage-masked Compare Status

## Gate

Gate 13 compare diagnostics checkpoint.

## Completed Content

- Added coverage-aware comparison metrics to `glass compare`.
- New CLI options:
  - `--glass-coverage-map`;
  - `--min-coverage`.
- When a coverage map is supplied, comparison metrics and linear fits are computed only on pixels meeting the coverage threshold.
- The JSON/HTML compare report records coverage fraction, valid pixel count, coverage summary statistics, and full-frame stats for context.
- Added tests proving coverage masking can exclude low-coverage edge artifacts while preserving full-frame residual context.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\compare_report.py src\glass\cli.py tests\test_compare_report.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_report.py tests\test_cli_smoke.py
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.html" --glass-time-seconds 111.94882199994754 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA triangle Lanczos3 coverage190 scaled" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_coverage_map_H.fits" --min-coverage 190
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Targeted compare/CLI tests: `9 passed in 0.32s`.
- Full test suite: `168 passed in 7.84s`.

## Real-data Results

- Coverage-masked compare report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.html`.
- Coverage map: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_coverage_map_H.fits`.
- Minimum coverage: `190`.
- Compared pixels: `59264430`.
- Coverage fraction: `0.9612859117097478`.
- Speedup: `9.75928982978054x`.
- RMS difference: `0.0017183155193652361`.
- Absolute difference p50: `7.188005838543177e-05`.
- Absolute difference p90: `0.00013341044541448355`.
- Absolute difference p99: `0.00045279982034117025`.
- Absolute difference p99.9: `0.00448366389935935`.
- Full-frame p99/p99.9 for context: `0.0021627108892425632 / 0.20893197426822768`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- Coverage masking currently uses only the GLASS coverage map. It does not consume a reference/WBPP coverage map.
- The threshold is user-selected; defaulting or auto-selection is intentionally not hidden.
- This improves metric interpretation but does not change the generated master image.

## Next Step

- Use coverage-masked compare as the default interpretation for real WBPP parity reports, while retaining full-frame and fixed-border metrics.

## Clean-room Compliance

- Compliant. The comparison uses GLASS maps and user-generated WBPP black-box output only.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
