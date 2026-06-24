# S2-Gate 613 Status: Resident Grid-LN Batched Statistics

## Gate

S2-Gate 613

## Completed

- Added a resident CUDA batched grid local-normalization statistics kernel over
  source frame x grid tile.
- Added the native/Python API
  `ResidentCalibratedStack.frame_pair_grid_stats_batch(...)`.
- Updated resident `grid_mean_std` local normalization so active non-reference
  frame-pair stats are computed in one batch when the native method is
  available.
- Preserved the per-frame stats fallback for older native builds.
- Recorded batch evidence in `local_norm_results.json` and
  `resident_artifacts.json`:
  - per-frame `grid_coefficients.stats_source`;
  - group/resident `grid_stats.batched`;
  - source count, grid shape, transferred bytes, and timing.
- Updated docs:
  - `docs/local_normalization_model.md`;
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/algorithm_sources.md`;
  - `docs/known_limitations.md`.

## Commands

- `cmd.exe /d /s /c "<VS vcvars64.bat> && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "grid"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "ncc_subpixel_registration_smoke"`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate613_ln_batch_stats\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- Gate612/Gate613 FITS hash and pixel parity script.
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_local_norm_vs_cpu.py tests\test_cuda_resident_stack.py -k "grid or local_norm"`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native CUDA rebuild: passed.
- Focused resident stack grid tests: `5 passed, 50 deselected`.
- Focused resident CLI grid-LN smoke: `1 passed, 114 deselected`.
- Focused GPU/CPU local-normalization and resident grid tests:
  `10 passed, 50 deselected`.
- Ruff: `All checks passed!`
- Full pytest: `1290 passed in 52.24s`.

## Real 200-Light Regression

- Run:
  `C:\glass_runs\phase2_s2_gate613_ln_batch_stats\real_200_default_regression`
- Comparison:
  `C:\glass_runs\phase2_s2_gate613_ln_batch_stats\real_200_vs_gate612_compare.json`
- Tracked outputs compared:
  - `resident_master_H.fits`;
  - `resident_weight_map_H.fits`;
  - `resident_coverage_map_H.fits`;
  - `resident_dq_map_H.fits`;
  - `resident_low_rejection_map_H.fits`;
  - `resident_high_rejection_map_H.fits`.
- Result: all six outputs are SHA256-identical to Gate612 and have zero
  differing pixels.
- Batch grid stats:
  - `source_count=192`;
  - `grid_rows=26`;
  - `grid_cols=38`;
  - `grid_count=988`;
  - `download_bytes=7587840`;
  - `index_bytes=768`;
  - batch stats `total_s=0.080022`.
- Local-normalization group timing:
  - Gate612: `0.5070594000862911 s`;
  - Gate613: `0.42897249991074204 s`.
- Total internal run timing:
  - Gate612: `11.157036500168033 s`;
  - Gate613: `11.212513899896294 s`.

## CUDA

- CUDA available: yes.
- Device:
  - `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`;
  - compute capability `12.0`;
  - total memory `97886 MiB`;
  - multiprocessors `188`;
  - driver version `596.21`.

## Known Limitations

- Gate613 batches the grid statistics phase, but coefficient construction and
  the in-place apply calls are still orchestrated per normalized frame.
- End-to-end timing showed a small total-run noise regression of about
  `0.055 s` even though the targeted LN group timing improved by about
  `0.078 s`.
- Larger future wins are still expected from resident registration/warp
  orchestration and a scalable hardened winsorized reducer.

## Next Step

Return to the main Phase 2 performance path:

- either fuse/batch more of resident LN coefficient generation and application;
- or target the larger default-route bottlenecks in resident registration/warp
  orchestration and hardened winsorized integration.

## Clean-Room Compliance

This gate uses GLASS-owned CUDA kernels, GLASS-owned resident artifact
contracts, GLASS tests, and user-owned benchmark artifacts. No external or
proprietary implementation source was inspected, copied, summarized, or
reworked.
