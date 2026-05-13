# Optimization Gate 08: Resident Prefetch Worker Control

## Gate

Optimization Gate 08

## Completed

- Added configurable resident light-frame prefetch worker count.
- Extended `_LightPrefetcher` from a fixed single-worker prefetcher to a multi-worker prefetcher while preserving ordered frame consumption.
- Added CLI flags for both `run` and `audit`:
  - `--resident-prefetch-workers`
- Recorded the configured worker count in `resident_artifacts.json` under `resident_io_pipeline.prefetch_workers`.
- Updated resident CUDA smoke coverage to exercise `--resident-prefetch-workers 2`.

## Commands Run

- `.venv\Scripts\ruff.exe check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_cli_smoke.py`
- `.venv\Scripts\glass.exe run --help`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Targeted CLI/resident tests: `5 passed`.
- Full pytest: `181 passed in 7.93s`.

## CUDA Status

CUDA is available through the native backend.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native backend: true

## Known Limitations

- This gate adds CPU RAM prefetch concurrency control, but does not yet add pinned host buffers or asynchronous H2D copies.
- Increasing workers can improve decode overlap on fast storage but may hurt on slow external disks; it must be benchmarked per dataset/storage layout.
- Resident H2D/calibration remains synchronous per frame.

## Next Step

Sweep M38 resident runs with shared-sort registration using different `--resident-prefetch-frames` and `--resident-prefetch-workers` values, then select the fastest setting that keeps output byte-identical or WBPP-accepted.

## Clean-room Compliance

Compliant. This gate only changed GLASS-owned Python code and tests. It did not read, copy, summarize, or modify PixInsight/WBPP/PJSR official source code, and it did not touch original image data.
