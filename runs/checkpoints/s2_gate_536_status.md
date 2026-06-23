# S2-Gate 536 Status: Resident Callback Fetch Batch Prefetch-Depth Guard

## Gate

S2-Gate 536

## Completed

- Continued the Phase 2 resident CUDA scheduling hardening line.
- Tested larger resident warp/calibration scheduling probes on the real
  200-light dataset before changing defaults.
- Confirmed that a huge explicit warp chunk (`134` frames) is numerically safe
  but slower, so it was not promoted as a default.
- Found a real resident scheduling bug: callback-release calibration with
  `resident_calibration_batch_frames > resident_prefetch_frames` could request
  more pinned slots than exist and crash while fetching the batch.
- Fixed the resident engine so callback-release + pinned-ring mode clamps
  `calibration_fetch_batch_frames` to the pinned prefetch depth.
- Added artifact fields:
  - `calibration_fetch_batch_requested_frames`;
  - `calibration_fetch_batch_frames`;
  - `calibration_fetch_batch_limit_source`;
  - `calibration_fetch_batch_clamped_to_prefetch_depth`.
- Added the same scheduling fields to the resident light pipeline profile
  knobs.
- Added a regression test that runs with prefetch depth `1` and requested
  callback fetch batch `2`, proving the run completes with an effective fetch
  batch of `1`.

## Commands Run

- `.venv\Scripts\glass.exe run ... --resident-warp-chunk-capacity-frames 134`
- `.venv\Scripts\glass.exe run ... --resident-calibration-batch-frames 32`
- `.venv\Scripts\glass.exe run ... --resident-calibration-batch-frames 64`
- `python -m compileall -q src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_releases_inside_native_batch tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_clamps_fetch_batch_to_prefetch_depth tests/test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_clamps_wave_to_stream_count tests/test_resident_light_pipeline_profile.py`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate536_fetch_guard\runs_20260623_132748\batch64_clamped --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --resident-calibration-batch-frames 64 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate536_fetch_guard\runs_20260623_132829\default_rerun --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused callback/profile tests: `6 passed in 1.04s`.
- Full pytest: `1176 passed in 42.87s`.

## Real 200-Light Results

- Baseline Gate535:
  `C:\glass_runs\phase2_s2_gate535_header_spec_cache\runs_20260623_131656\gate535_spec_cache_timed`.
- Oversized callback batch validation:
  `C:\glass_runs\phase2_s2_gate536_fetch_guard\runs_20260623_132748\batch64_clamped`.
  - Shell/internal: `5.8136118 s` / `5.456099700066261 s`.
  - Requested calibration batch: `64`.
  - Requested fetch batch: `64`.
  - Effective fetch batch: `32`.
  - Clamp source: `pinned_ring_prefetch_depth`.
  - `prefetch_fill_blocked_no_slot_count=0`.
- Default rerun:
  `C:\glass_runs\phase2_s2_gate536_fetch_guard\runs_20260623_132829\default_rerun`.
  - Shell/internal: `5.4279064 s` / `5.083654500020202 s`.
  - Effective fetch batch remains `16`, with source `requested`.
- The larger batch path is stable but slower on this data, so no default
  throughput preset change was made.

## Numerical Validation

- `batch64_clamped` and `default_rerun` were compared against Gate535.
- Master, weight map, coverage map, low rejection map, high rejection map, and
  DQ map are all bitwise identical to Gate535.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Disk/Cleanup

- Removed non-final exploratory probe directories:
  - `C:\glass_runs\phase2_s2_gate536_warp_capacity_probe`;
  - `C:\glass_runs\phase2_s2_gate536_batch_probe\runs_20260623_132503\batch32_probe`.
- C: free space after cleanup: about `333.5 GB`.

## Known Limits

- This gate fixes scheduling correctness for oversized callback fetch batches;
  it does not claim a default speedup.
- The explicit 64-frame calibration batch is slower than the default 16-frame
  scheduling on the current 200-light dataset.
- Large warp chunks are numerically safe in the probe but slower than the
  default 8-frame native chunk on this dataset.

## Next

- Continue with resident light-loop orchestration and registration/warp timing,
  but promote only settings or code paths that improve the real 200-light
  default without changing outputs.

## Clean-Room

- Compliant. This gate uses GLASS code, GLASS-generated artifacts, and
  user-owned benchmark images only. It does not inspect or copy
  PixInsight/WBPP/PJSR source or modify input directories.
