# S2-Gate 265 Status

- Gate: S2-Gate 265
- Scope: Resident Winsorized Microbenchmark Artifact
- Status: green
- Date: 2026-06-18

## Completed

- Added `glass resident-winsorized-benchmark`.
- Added a deterministic synthetic stack generator with gradients, frame variation, non-uniform weights, and low/high outliers.
- The benchmark compares three paths:
  - CPU `weighted_integrate_stack(..., rejection="winsorized_sigma")` baseline.
  - Resident CUDA fast winsorized approximation.
  - Resident CUDA hardened CPU-parity winsorized path.
- The JSON artifact records config, timings, hardened-vs-CPU map differences, fast-vs-CPU context, checks, failed checks, and limitations.
- The command can write optional Markdown.
- CUDA-unavailable environments produce a clear `cuda_unavailable` artifact instead of breaking CPU-only imports.
- Added CPU-only unavailable-path tests, CUDA benchmark tests, CLI artifact tests, and help-list coverage.
- Wrote a small benchmark artifact under `runs/checkpoints/`.
- Updated Phase 2 planning docs and the algorithm source ledger.

## Commands

- `.\.venv\Scripts\ruff.exe check src\glass\report\resident_winsorized_benchmark.py src\glass\cli.py tests\test_resident_winsorized_benchmark.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_benchmark.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_benchmark.py tests\test_cli_smoke.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m glass.cli resident-winsorized-benchmark --frames 8 --height 16 --width 16 --seed 265 --out runs\checkpoints\s2_gate_265_resident_winsorized_benchmark.json --markdown runs\checkpoints\s2_gate_265_resident_winsorized_benchmark.md --fail-on-failure`
- CUDA probe via `glass_cuda.cuda_available()`, `glass_cuda.list_devices()`, and timed method availability checks.

## Test Results

- Ruff check: passed.
- New benchmark tests: 3 passed.
- Benchmark/CLI/CUDA resident stack tests: 57 passed.
- Full pytest: 602 passed.
- Microbenchmark command: passed.

## Microbenchmark Artifact

- JSON: `runs/checkpoints/s2_gate_265_resident_winsorized_benchmark.json`
- Markdown: `runs/checkpoints/s2_gate_265_resident_winsorized_benchmark.md`
- Frames: 8.
- Shape: 16x16.
- CPU baseline: 0.014615500003856141 s.
- CUDA fast approximation: 0.0008526000019628555 s.
- CUDA hardened: 0.000185800003237091 s.
- Hardened master vs CPU RMS: 5.781343294611998e-06.
- Hardened master vs CPU max abs: 1.52587890625e-05.
- Fast approximation master vs CPU RMS: 0.566935986706338.

## CUDA

- CUDA available: true.
- Native backend loaded: true.
- Timed hardened resident method available: true.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.

## Known Limitations

- This is a synthetic microbenchmark and does not replace the 200-light real-data benchmark.
- The CPU baseline timing is for the small synthetic stack only and is not a throughput claim.
- The fast approximation path is included for context and is not required to match CPU parity.
- No CUDA kernel optimization, fused-matrix hardened parity, tile-local hardened parity, package build/upload, release update, or default switch was performed in this gate.

## Next Step

- Use the microbenchmark artifact and timing surface to design the next hardened CUDA optimization gate, then validate on progressively larger representative stacks before any 200-light default-path experiment.

## Clean-Room Compliance

- Compliant.
- This gate uses deterministic GLASS-generated arrays and GLASS CPU/CUDA code only.
- No user image directories, PixInsight/WBPP/PJSR source code, or proprietary implementation details were read, copied, summarized, or reworked.
