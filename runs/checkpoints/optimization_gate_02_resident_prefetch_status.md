# Optimization Gate 02: Resident CPU RAM Prefetch

## Gate

Optimization Gate 02.

## Completed content

- Added `--resident-prefetch-frames` to `gpwbpp run` and `gpwbpp audit`.
- Implemented a bounded CPU RAM light-frame prefetch queue for resident CUDA runs.
- The prefetch queue starts FITS read/decode ahead of calibration and preserves ordered resident-stack writes.
- Added timing fields for both foreground wait and background read/decode work:
  - `light_read_decode`
  - `light_read_decode_worker`
  - `per_frame_read_decode_mean`
  - `per_frame_read_decode_worker_mean`
- Added `resident_io_pipeline` artifact metadata with `prefetch_frames` and `prefetch_workers`.
- Exposed prefetch metadata and worker read timing in HTML reports.
- Added tests covering the CLI option, resident artifact schema, and report columns.

## Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py src\gpwbpp\report\html_report.py src\gpwbpp\cli.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py
.\.venv\Scripts\gpwbpp.exe run --help
.\.venv\Scripts\python.exe -m pytest -q
```

## Test result

- Ruff: all checks passed.
- Targeted smoke tests: 2 passed.
- Resident CUDA run tests: 14 passed.
- Full pytest: 180 passed in 8.05 s.

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Known limitations

- This checkpoint implements Python-side CPU RAM prefetch only. It does not yet use pinned host memory or native async H2D streams.
- The queue uses one background reader to avoid hammering the external storage device. Future tests may add a worker-count option if CPU decode, not disk bandwidth, becomes limiting.
- The benefit is workload dependent and must be measured on the M38 200-light real benchmark.

## Next step

- Run M38 200-light with `--resident-prefetch-frames 2` and compare against the `prefetch=0` fine-timing baseline.
- If foreground read wait drops materially, tune depth 1/2/4. If not, move the optimization down into pinned memory and native async H2D.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No original data directory was modified.
