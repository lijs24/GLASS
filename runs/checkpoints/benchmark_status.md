# Benchmark Status

- Date: 2026-05-12
- Status: baseline benchmark scripts implemented

## Completed

- Replaced placeholder benchmark scripts with runnable JSON-output benchmarks.
- Implemented common timing/result schema in `benchmarks/common.py`.
- Implemented:
  - `benchmarks/bench_scan.py`
  - `benchmarks/bench_cpu_calibration.py`
  - `benchmarks/bench_gpu_calibration.py`
  - `benchmarks/bench_gpu_integration.py`
  - `benchmarks/bench_io_streaming.py`
  - `benchmarks/bench_end_to_end.py`
- Added benchmark tests for scan and end-to-end CPU paths.

## Required Fields Covered

- frame count
- image shape
- total pixels
- backend
- elapsed seconds
- peak Python traced RAM
- current NVIDIA used VRAM when `nvidia-smi` is available
- total VRAM when `gpwbpp_cuda` can list devices
- throughput in MPix/s
- output path

## Commands Run

```powershell
.\.venv\Scripts\python -m pytest -q tests/test_benchmarks.py
.\.venv\Scripts\python benchmarks\bench_end_to_end.py --out runs\benchmarks\bench_end_to_end_cuda_v2.json --frames 4 --width 48 --height 48 --tile-size 12 --backend cuda
.\.venv\Scripts\python -m pytest -q
```

## Results

- Benchmark tests: 2 passed.
- Full suite: 45 passed.
- Sample CUDA end-to-end benchmark output: `runs\benchmarks\bench_end_to_end_cuda_v2.json`.
- Sample benchmark measured backend: cuda.
- Sample benchmark total VRAM: 97886 MiB.

## Known Limitations

- Peak RAM is Python `tracemalloc` peak, not whole-process RSS.
- Peak VRAM is sampled through `nvidia-smi`, not a synchronized high-water mark.
- Benchmarks default to tiny synthetic data to avoid accidental large real-data runs.
- PixInsight/WBPP timing still requires a black-box WBPP executable or user-generated WBPP output/log.

## Clean-room Compliance

- Benchmarks do not read PixInsight/WBPP/PJSR source.
- Benchmarks do not modify input directories.
