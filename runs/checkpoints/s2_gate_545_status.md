# S2-Gate 545 Status: Opt-In Native Raw FITS Completion Queue

## Gate

- Gate: S2-Gate 545
- Status: green
- Theme: resident CUDA I/O/upload/calibration mainline
- Checkpoint summary: `runs/checkpoints/s2_gate_545_native_queue_read_summary.json`

## Completed

- Added native pybind class `RawFitsReadQueue`.
- The queue owns C++ worker threads, reads simple FITS byte ranges into
  caller-provided pinned `uint8` buffers, and exposes per-frame completions.
- Added `glass_cuda.raw_fits_read_queue_available()` and
  `glass_cuda.create_raw_fits_read_queue()`.
- Integrated the queue into resident CUDA pinned-ring prefetch behind
  `GLASS_RESIDENT_NATIVE_QUEUE_READ=1`.
- Preserved ready-first scheduling with per-frame completions.
- Recorded native queue candidate/requested/available/enabled state, submit
  count, completion count, worker count, cumulative native read time, and
  completion wait time in resident artifacts and resident light pipeline
  profiles.
- Kept default resident behavior unchanged.

## Commands Run

- Release native build:
  `VsDevCmd.bat -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe -S . -B build -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_CUDA_ALLOW_UNSUPPORTED_COMPILER=ON -Dpybind11_DIR=<venv pybind11 cmake dir> -DCMAKE_BUILD_TYPE=Release && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release`
- Queue focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_fits_io.py::test_native_u16_raw_fits_queue_reads_into_pinned_outputs tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_queue_read_is_opt_in`
- Default/batch/queue focused regression tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_batch_read_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_queue_read_is_opt_in tests/test_fits_io.py::test_native_u16_raw_fits_batch_reader_reads_into_pinned_outputs tests/test_fits_io.py::test_native_u16_raw_fits_queue_reads_into_pinned_outputs`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Queue 200-light run:
  `GLASS_RESIDENT_NATIVE_QUEUE_READ=1 glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate545_native_queue_read\runs_20260623_153000\native_queue_optin_release --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Fresh default 200-light run:
  `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate545_native_queue_read\runs_20260623_153000\default_fresh_release ...`

## Test Results

- Queue focused tests: `2 passed in 0.91s`
- Focused regression tests: `5 passed in 0.72s`
- Full pytest: `1183 passed in 43.31s`

## CUDA

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: available
- Raw FITS read queue binding: available

## Real 200-Light Evidence

- Same-session default:
  `C:\glass_runs\phase2_s2_gate545_native_queue_read\runs_20260623_153000\default_fresh_release`
- Same-session queue opt-in:
  `C:\glass_runs\phase2_s2_gate545_native_queue_read\runs_20260623_153000\native_queue_optin_release`
- Default shell/internal elapsed:
  `5.50113 s` / `5.1318423000047915 s`
- Queue shell/internal elapsed:
  `5.378282 s` / `5.01306339999428 s`
- Queue versus fresh default:
  `1.0228414947375388x`, `0.12284800000000029 s` faster
- Queue versus recorded WBPP black-box elapsed `1092.541 s`:
  `203.139403995551x`

## Queue Artifact Evidence

- Effective FITS mode: `native_u16_gpu`
- Backend counts: `native_u16be_raw_queue: 200`
- Native queue:
  candidate `true`, available `true`, requested `true`, enabled `true`,
  policy `env_enabled`
- Queue submits/completions/workers: `200` / `200` / `16`
- Queue cumulative native read time: `25.481368400000004 s`
- Stage timings:
  light read/upload/calibrate `2.5739439000026323 s`,
  light read wait `1.184200199204497 s`,
  worker native FITS cumulative `25.3398809 s`,
  ready queue wait `1.1806699999724515 s`,
  registration/warp `0.25813750020461157 s`,
  integration `0.30349709995789453 s`,
  output write `0.2879365000408143 s`
- Ready queue callbacks: `200`
- Out-of-order consumed frames: `78`

## Numerical Validation

- Queue opt-in master, weight map, coverage map, low/high rejection maps, and
  DQ map are SHA256-identical to the fresh default run.
- The same outputs match the Gate544 default hashes through the comparison
  chain.
- Same-session hash report:
  `C:\glass_runs\phase2_s2_gate545_native_queue_read\hash_compare_default_vs_queue.json`
- Gate544 hash report:
  `C:\glass_runs\phase2_s2_gate545_native_queue_read\hash_compare_gate544_default.json`
- WBPP comparison is inherited through bitwise output identity:
  RMS `0.0004279821839256963`, p99 abs diff
  `0.0001313822576776147`, robust-fit RMS
  `4.2529498303511286e-05`, coverage fraction
  `0.9892770479074376`, compared pixels `56997300`.

## Known Limitations

- Native queue read is opt-in and not promoted to default.
- Same-session improvement is modest and still below the best historical
  warm-cache default runs from Gate542/Gate543.
- The current implementation still has a Python drain/cache handoff between
  native queue completion and H2D/calibration scheduling.
- Fast path eligibility is limited to simple `BITPIX=16`, `BSCALE=1`,
  `BZERO=32768` primary-image FITS payloads without unsupported blank-value
  semantics.

## Next Step

- Feed native queue completions directly into H2D/calibration wave scheduling,
  reducing the Python drain/cache handoff while preserving ready-first
  scheduling.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS code, public FITS byte layout rules, user image data,
  GLASS artifacts, and user-generated timing/reference outputs.
- It does not inspect external implementation source, does not modify raw input
  directories, and does not change calibration, registration, warp, rejection,
  DQ, integration, accepted frames, or output pixels.
