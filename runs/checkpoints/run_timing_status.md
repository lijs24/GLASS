# Run Timing Checkpoint

- Date: 2026-05-12
- Scope: Add structured GPWBPP stage timing artifacts for future PixInsight/WBPP speed comparison.
- Related gates: strengthens Gate 12 reporting/resume diagnostics and prepares Gate 13 timing comparison.

## Completed

- Added `run_timing.json` generation for `gpwbpp run`, `gpwbpp audit`, and resumed pipeline execution.
- Added per-stage timing records with `stage`, `started_at`, `status`, `elapsed_s`, and `error` on failure.
- Timing is written after each stage so failed runs retain diagnostic timing.
- Added timing data to HTML report Runtime summary.
- Added pipeline fixture assertions for audit timing output.
- Updated completion audit evidence.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/gpwbpp/cli.py src/gpwbpp/report/html_report.py tests/test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_fixture.py tests/test_cli_smoke.py tests/test_blackbox_package.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\gpwbpp.exe run --plan runs/real_m5_lum_subset/processing_plan.json --out runs/real_m5_lum_subset/gpwbpp_cuda_timed_run --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 1024`
- `.\\.venv\\Scripts\\gpwbpp.exe report --run runs/real_m5_lum_subset/gpwbpp_cuda_timed_run --out runs/real_m5_lum_subset/gpwbpp_cuda_timed_run/report.html`

## Test Results

- Focused pipeline/CLI/blackbox tests: 15 passed in 4.98 s.
- Full pytest: 59 passed in 6.46 s.
- Real M5/Lum subset CUDA timed run completed through integration.
- Recorded GPWBPP stage timing:
  - calibration: 19.956928800034802 s
  - quality: 16.128449300013017 s
  - registration: 12.190145100001246 s
  - warp: 3.4334979000268504 s
  - local_normalization: 0.00535599997965619 s
  - integration: 5.97876670002006 s
  - total: 57.69314380007563 s

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Artifacts

- `runs/real_m5_lum_subset/gpwbpp_cuda_timed_run/run_timing.json`
- `runs/real_m5_lum_subset/gpwbpp_cuda_timed_run/report.html`
- `runs/real_m5_lum_subset/gpwbpp_cuda_timed_run/integration/master_Lum.fits`

## Known Limitations

- Timing currently measures Python stage wall time inside GPWBPP, not external process startup overhead.
- `gpwbpp report` can display existing timing data, but a manually invoked report command does not yet append its own report-stage timing into the already rendered HTML.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Use `run_timing.json` as the GPWBPP timing source when finalizing the WBPP black-box comparison package.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The real-data run used only user-provided FITS inputs and GPWBPP-generated artifacts.
- The original data directory was not modified.
