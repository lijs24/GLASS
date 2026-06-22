# S2-Gate 470 Status: Resident Fused Matrix Dispatch Benchmark

## Gate

- Gate: S2-Gate 470
- Scope: create a repeatable resident CUDA synthetic benchmark comparing
  chunked matrix warp plus stack integration against fused matrix-warped
  integration.
- Status: passed
- Date: 2026-06-22 local

## Completed Work

- Added `benchmarks/bench_resident_fused_matrix_dispatch.py`.
- The benchmark generates deterministic mono synthetic frames and translation
  matrices, then compares two resident CUDA dispatch routes on the same data:
  - chunked matrix warp into the resident stack followed by resident mean
    integration;
  - fused matrix integration that samples calibrated resident frames through
    the matrices and avoids registered-stack writeback.
- The benchmark records:
  - stack and fused dispatch wall-time min/median/mean/max;
  - speedup using median wall time;
  - throughput in MPix/s;
  - native timing payloads for both routes;
  - master and weight-map max-absolute and RMS differences.
- Added a CUDA benchmark smoke test in `tests/test_benchmarks.py`.
- Updated Phase 2 documentation and algorithm-source provenance.

## CUDA Status

- CUDA available: true.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Device memory: 97886 MiB.
- Multiprocessors: 188.

## Synthetic Benchmark

- Command:
  - `.\.venv\Scripts\python.exe benchmarks\bench_resident_fused_matrix_dispatch.py --out runs\checkpoints\s2_gate_470_fused_matrix_dispatch_benchmark.json --frames 32 --width 512 --height 512 --repeats 3 --warmup 1 --max-chunk-capacity-frames 8 --download-mode master_weight`
- Result:
  - frame count: `32`
  - shape: `512 x 512`
  - total pixels: `8388608`
  - interpolation: `bilinear`
  - chunk capacity: `8`
  - stack dispatch median: `0.005378499976359308 s`
  - fused matrix dispatch median: `0.0013046000385656953 s`
  - median speedup: `4.122719467548494x`
  - stack throughput median: `1559.655672933223 MPix/s`
  - fused throughput median: `6430.022805474245 MPix/s`
  - master max abs diff: `0.0`
  - master RMS diff: `0.0`
  - weight max abs diff: `0.0`
  - weight RMS diff: `0.0`
- Interpretation:
  - On synthetic resident data after upload, fused matrix integration is the
    stronger next production optimization candidate for bilinear matrix routes
    where local normalization is off and registered intermediates do not need
    to be written.

## Real 200-Light Baseline

- A new 200-light run was not launched for this gate.
- Reason: C: had about `0.143 GiB` free during validation.
- Applicable accepted real-data baseline remains S2-Gate465:
  - run:
    `C:\glass_runs\phase2_s2_gate_465_200\admission_capacity_default_parity_r3_20260622`
  - input: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat;
  - internal GLASS timing: `36.103794 s`;
  - WBPP black-box timing: `1092.541 s`;
  - speedup vs WBPP: `30.261113x`;
  - compare RMS diff: `0.00170058`;
  - P99 absolute diff: `0.000459801`;
  - coverage fraction: `0.961043`.

## Commands Run

- `.\.venv\Scripts\python.exe benchmarks\bench_resident_fused_matrix_dispatch.py --out runs\checkpoints\s2_gate_470_fused_matrix_dispatch_benchmark.json --frames 32 --width 512 --height 512 --repeats 3 --warmup 1 --max-chunk-capacity-frames 8 --download-mode master_weight`
- `.\.venv\Scripts\ruff.exe check benchmarks tests docs`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_bench_resident_fused_matrix_dispatch_outputs_agreement`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Benchmark run: passed.
- Ruff: passed.
- Focused benchmark pytest: `1 passed in 0.38 s`.
- Broader benchmark/CUDA/resident pytest: `133 passed in 13.53 s`.
- Full pytest: `1103 passed in 47.87 s`.

## Artifacts

- `runs/checkpoints/s2_gate_470_fused_matrix_dispatch_benchmark.json`
- `runs/checkpoints/s2_gate_470_status.md`

## Known Limitations

- The benchmark measures resident dispatch after frames are uploaded; it does
  not include FITS read, H2D upload, calibration, star detection, descriptor
  fitting, local normalization, or 200-light disk pressure.
- It uses synthetic translation matrices, not a real star-alignment matrix set.
- It does not change runtime defaults.

## Next Step

- After freeing C: output space, run a 200-light A/B test comparing:
  - current accepted stack/chunked route;
  - `--resident-integration-dispatch auto`;
  - explicit `--resident-integration-dispatch fused_matrix`;
  then check frame accounting, DQ maps, acceptance contract, and compare metrics.

## Clean-Room Compliance

- Compliant.
- No official PixInsight WBPP/PJSR source was read, summarized, copied, or used.
- The benchmark uses GLASS-generated synthetic arrays and GLASS-owned CUDA
  kernels only.
- User image input directories were not modified.
