# S2-Gate 627 Status: Over-Limit Resident Winsorized Benchmark Contract

## Gate

S2-Gate 627

## Completed Content

- Added a reusable over-512-frame resident winsorized benchmark builder:
  `build_resident_winsorized_overlimit_benchmark`.
- Added `glass resident-winsorized-overlimit-benchmark`.
- Added `benchmarks/bench_resident_overlimit_winsorized.py`.
- Added CUDA-skipping tests for the over-limit benchmark and benchmark script.
- Updated Phase 2, integration, algorithm-source, and limitation docs.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check src\glass\report\resident_winsorized_benchmark.py src\glass\cli.py tests\test_resident_winsorized_overlimit_benchmark.py tests\test_benchmarks.py benchmarks\bench_resident_overlimit_winsorized.py tests\test_cli_smoke.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_overlimit_benchmark.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_bench_resident_overlimit_winsorized_outputs_required_fields tests\test_cli_smoke.py::test_cli_help_commands`
- `.venv\Scripts\python.exe benchmarks\bench_resident_overlimit_winsorized.py --out C:\glass_runs\phase2_s2_gate627_overlimit_winsorized\overlimit_545_benchmark.json --markdown C:\glass_runs\phase2_s2_gate627_overlimit_winsorized\overlimit_545_benchmark.md --frames 545 --height 32 --width 32 --tile-size 16 --fail-on-failure`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused over-limit benchmark tests: `3 passed`.
- Benchmark script plus CLI help tests: `2 passed`.
- Full pytest: `1322 passed in 60.65 s`.

## Performance And Result Evidence

- Artifact: `C:\glass_runs\phase2_s2_gate627_overlimit_winsorized\overlimit_545_benchmark.json`
- Markdown: `C:\glass_runs\phase2_s2_gate627_overlimit_winsorized\overlimit_545_benchmark.md`
- Status: passed.
- Selector: `radix_select_unbounded_positive_samples`.
- CPUStackEngine tiled baseline: `0.043547699926421046 s`.
- CUDA upload: `0.00484060007147491 s`.
- CUDA radix-select integration: `0.02139750006608665 s`.
- CUDA total with upload: `0.02623810013756156 s`.
- Speedup vs CPUStackEngine: `2.035176996935297x` excluding upload,
  `1.6597123914501593x` including upload.
- Master/weight/coverage/low-rejection/high-rejection maps matched
  CPUStackEngine exactly in this synthetic run.

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend loaded: yes.

## Known Limits

- This gate adds an evidence and benchmark surface only.
- It does not promote the opt-in radix-select over-512 reducer to the default
  resident path.
- The primary validation is synthetic and small-image; it does not replace the
  real 200-light regression benchmark.

## Next Step

Return to substantive Phase 2 mainline work: either use this over-limit
contract to optimize the scalable resident reducer, or run the next real
200-light A/B against the dominant I/O/upload/calibration and
registration/warp bottlenecks.

## Clean-Room Compliance

Compliant. The gate uses GLASS-owned CPUStackEngine semantics, GLASS-owned CUDA
wrappers/kernels, GLASS-generated synthetic data, and local benchmark artifacts.
No external proprietary source was inspected, copied, summarized, or reworked.
