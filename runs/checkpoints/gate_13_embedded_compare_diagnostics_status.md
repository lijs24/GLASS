# Gate 13 Embedded Compare Diagnostics Status

## Gate

Gate 13 compare/report checkpoint.

## Completed Content

- Replaced the generic compare HTML output with a dedicated compare report.
- Embedded diagnostic PNG previews directly in the compare HTML when `--diagnostics-dir` is used:
  - GPWBPP preview;
  - reference preview;
  - absolute difference preview;
  - signed difference preview.
- Added a residual hotspot table to compare HTML.
- Added timing, speedup, border-aware comparison region, transform, linear-fit, robust-fit, and clean-room note sections.
- Extended tests to assert diagnostic images are linked from the generated HTML.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\report\compare_report.py tests\test_compare_report.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_report.py tests\test_cli_smoke.py
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_diagnostics_embedded.html" --gpwbpp-time-seconds 111.94882199994754 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident CUDA triangle Lanczos3 193 WBPP-failed-excluded scaled diagnostics embedded" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 8.764434957115609e-06 --gpwbpp-offset 0.0006274500691899127 --diagnostics-dir "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_diagnostics_embedded" --diagnostic-max-size 1200 --hotspot-tile-size 512 --ignore-border-px 32
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Targeted compare/CLI tests: `8 passed in 0.27s`.
- Full test suite: `167 passed in 7.46s`.

## Real-data Artifact

- Compare report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_diagnostics_embedded.html`.
- Diagnostics directory: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_diagnostics_embedded`.
- The HTML contains relative image links such as `compare_diagnostics_embedded/signed_diff_preview.png`.
- The report records:
  - speedup: `9.75928982978x`;
  - ignore border: `32 px`;
  - compared shape: `6358 x 9536`;
  - p99 absolute difference: `0.000492215389386`;
  - p99.9 absolute difference: `0.00711346775212`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- Diagnostic images are downsampled previews, not measurement-grade data.
- The compare HTML embeds links to local artifact files; moving the HTML without its diagnostics directory will break image links.
- The report highlights residual hotspots but does not automatically classify their cause.

## Next Step

- Add optional coverage-aware compare masking so low-coverage edge regions can be excluded by map rather than by a fixed border.

## Clean-room Compliance

- Compliant. The report compares GPWBPP output to user-generated PixInsight/WBPP black-box artifacts only.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
