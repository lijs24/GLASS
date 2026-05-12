# Black-box Timing Autofill Checkpoint

- Date: 2026-05-12
- Scope: Connect GPWBPP `run_timing.json` to the PixInsight/WBPP black-box handoff and finalize workflow.
- Related gates: prepares Gate 13 timing comparison.

## Completed

- `gpwbpp blackbox-package` now reads `run_timing.json` from `--gpwbpp-run` when `--gpwbpp-time-seconds` is omitted.
- `timing_template.json` records:
  - `gpwbpp_time_seconds`
  - `gpwbpp_timing_source`
  - `gpwbpp_stage_timings`
- `gpwbpp blackbox-finalize` can recover GPWBPP time from `gpwbpp_run/run_timing.json` if the template has `gpwbpp_time_seconds: null`.
- Finalize summaries now include `gpwbpp_timing_source` and `speedup_observed`.
- Added tests for explicit timing, run-timing autofill, and finalize-time recovery.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/gpwbpp/report/blackbox_package.py tests/test_blackbox_package.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_blackbox_package.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Black-box package tests: 3 passed in 0.50 s.
- Full pytest: 61 passed in 6.45 s.

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## PixInsight Status

- Local PixInsight executable located at `C:\Users\ljs\AppData\Local\Programs\PixInsight\bin\PixInsight.exe`.
- `PixInsight.exe --help` returned exit code 0 but did not print CLI help.

## Known Limitations

- The WBPP reference run is not yet automated.
- It remains necessary to discover a safe black-box PixInsight/WBPP invocation method or produce a user-generated WBPP output/log from the UI.
- Clean-room constraints still prohibit reading official WBPP/PJSR script implementation source.

## Next Step

- Probe PixInsight command-line/automation interfaces and prepare a black-box WBPP run on the existing M5/Lum subset without reading official WBPP source.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No user input directory was modified.
