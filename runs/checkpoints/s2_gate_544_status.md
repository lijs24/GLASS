# S2-Gate 544 Status: Opt-In Native Raw FITS Batch Read

## Gate

- Gate: S2-Gate 544
- Status: green
- Theme: resident CUDA I/O/upload/calibration mainline
- Checkpoint summary: `runs/checkpoints/s2_gate_544_native_batch_read_summary.json`

## Completed

- Added native C++/pybind API `read_simple_fits_raw_batch_into_u8` for
  multi-file simple FITS raw byte-range reads into caller-provided `uint8`
  buffers.
- Added Python capability checks and wrapper functions in `glass_cuda`.
- Added `read_simple_fits_u16be_raw_batch_timed` in the FITS fast-I/O layer.
- Integrated native batch reads into the resident CUDA pinned-ring prefetcher
  behind `GLASS_RESIDENT_NATIVE_BATCH_READ=1`.
- Recorded resident artifact/profile fields for native batch read candidate,
  policy, requested, available, enabled, submit count, frame count, worker
  count, wall time, and cumulative time.
- Kept default resident behavior on per-frame native `u16` raw reads because the
  opt-in batch probe did not show a robust speed improvement and removed
  ready-first out-of-order scheduling.

## Commands Run

- Release native build through Visual Studio Build Tools, CMake/Ninja, and CUDA:
  `VsDevCmd.bat -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe -S . -B build -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_CUDA_ALLOW_UNSUPPORTED_COMPILER=ON -Dpybind11_DIR=<venv pybind11 cmake dir> -DCMAKE_BUILD_TYPE=Release && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release`
- Focused tests:
  `.venv\Scripts\python.exe -m pytest -q tests/test_fits_io.py::test_native_u16_raw_fits_batch_reader_reads_into_pinned_outputs tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_batch_read_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto`
- Full tests:
  `.venv\Scripts\python.exe -m pytest -q`
- Real default postpatch 200-light run:
  `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate544_native_batch_read\runs_20260623_151200\default_batch_disabled_release_postpatch --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- Real opt-in 200-light probe:
  `GLASS_RESIDENT_NATIVE_BATCH_READ=1 glass run ... --out C:\glass_runs\phase2_s2_gate544_native_batch_read\runs_20260623_150008\optin_batch_release ...`
- Hash compare:
  compared six Gate544 output maps against Gate543 with SHA256.
- Diff check:
  `git diff --check` for Gate544 touched files.

## Test Results

- Focused tests: `3 passed in 0.69s`
- Full pytest: `1181 passed in 43.12s`
- Diff check: passed; only Git line-ending warnings were printed.

## CUDA

- CUDA available: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: available
- Native batch read binding: available

## Real 200-Light Evidence

- Default postpatch run:
  `C:\glass_runs\phase2_s2_gate544_native_batch_read\runs_20260623_151200\default_batch_disabled_release_postpatch`
- Shell/internal elapsed: `5.4165 s` / `5.05357400001958 s`
- Effective FITS read mode: `native_u16_gpu`
- Native batch read fields:
  candidate `true`, available `true`, requested `false`, enabled `false`,
  policy `env_disabled_default`
- Key stage timings:
  light read/upload/calibrate `2.5875532999634743 s`,
  light read wait `1.1672238007886335 s`,
  worker native FITS cumulative `25.1334456 s`,
  registration/warp `0.2566100999247283 s`,
  integration `0.30122170003596693 s`,
  output write `0.25494139996590093 s`
- Speedup versus recorded WBPP black-box elapsed `1092.541 s`:
  `201.70608326410041x`

## Opt-In Probe

- Opt-in run:
  `C:\glass_runs\phase2_s2_gate544_native_batch_read\runs_20260623_150008\optin_batch_release`
- Enabled with `GLASS_RESIDENT_NATIVE_BATCH_READ=1`
- Shell/internal elapsed: `5.417102 s` / `5.041782399988733 s`
- Native batch read:
  candidate `true`, available `true`, requested `true`, enabled `true`,
  policy `env_enabled`
- Batch submits/frames/workers: `50` / `200` / `4`
- Batch wall/cumulative read time:
  `6.926075100000002 s` / `25.1844458 s`
- Out-of-order consumed frames: `0`
- Interpretation: usable infrastructure, not a default-worthy speed win.

## Numerical Validation

- Default postpatch master, weight map, coverage map, low/high rejection maps,
  and DQ map are SHA256-identical to Gate543.
- Opt-in Release run produced the same six SHA256 hashes as Gate543.
- Postpatch hash report:
  `C:\glass_runs\phase2_s2_gate544_native_batch_read\hash_compare_gate543_postpatch.json`
- WBPP comparison is inherited through bitwise output identity:
  RMS `0.0004279821839256963`, p99 abs diff
  `0.0001313822576776147`, robust-fit RMS
  `4.2529498303511286e-05`, coverage fraction
  `0.9892770479074376`, compared pixels `56997300`.

## Known Limitations

- Native batch read is opt-in and not promoted to default.
- The first integration is a coarse batch-future model; it does not preserve the
  ready-first scheduling freedom that the per-frame path uses.
- Eligible inputs are currently simple `BITPIX=16`, `BSCALE=1`, `BZERO=32768`
  primary-image FITS files without unsupported blank-value semantics.
- Debug native builds are not performance evidence.

## Next Step

- Build a streaming native per-frame completion queue or direct native
  read-to-calibration stream feeder so multi-file native I/O reduces Python
  orchestration without collapsing ready-first scheduling.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS source code, public FITS byte layout rules, user image
  data, GLASS artifacts, and user-generated timing/reference outputs.
- It does not inspect external implementation source, does not modify raw input
  directories, and does not change calibration, registration, warp, rejection,
  DQ, integration, accepted frames, or output pixels.
