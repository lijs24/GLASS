# Optimization Gate 00: Resident CUDA Fine Timing

## Gate

Optimization Gate 00.

## Completed content

- Added resident CUDA fine timing schema version 1.
- Split the previous `light_read_upload_calibrate` timing into:
  - `light_read_decode`
  - `light_h2d_calibrate_store`
  - `resident_registration_warp`
  - `resident_registration_warp_during_load`
  - `resident_registration_warp_deferred`
  - `gc`
  - `light_loop_unaccounted`
- Added nested `fine_timing` with total/min/mean/max per-frame summaries.
- Exposed the split timings in the HTML resident CUDA summary.
- Added tests for the timing schema and report columns.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\\test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\resident_cuda.py src\\glass\\report\\html_report.py tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test result

- Targeted tests: 2 passed.
- Resident CUDA run tests: 14 passed.
- Full pytest: 180 passed.
- Ruff: all checks passed.

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Known limitations

- `light_h2d_calibrate_store` is currently one Python-visible bucket because `ResidentCalibratedStack.calibrate_frame` performs upload, kernel execution, and resident-stack write behind one binding call.
- This checkpoint instruments the bottlenecks but does not yet implement pinned memory, async H2D, stream overlap, CUDA Graphs, or batched resident registration scheduling.
- Fine timing was verified on synthetic/smoke tests; the M38 200-light real benchmark still needs to be rerun to populate the new fields.

## Next step

- Run the M38 resident benchmark once with the new schema to quantify read/decode vs H2D/calibrate/store vs registration/warp.
- Then implement the first pipeline optimization: pinned host staging plus double-buffered read/upload/calibrate overlap.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No original image data directories were modified.
