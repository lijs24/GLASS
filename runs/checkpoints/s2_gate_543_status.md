# S2-Gate 543 Status: Resident Prefetch Completion Queue

## Gate

- Gate: S2-Gate 543
- Date: 2026-06-23
- Scope: CUDA resident prefetch/ready-first scheduler hardening on the real 200-light benchmark.

## Completed

- Added a callback-backed ready queue to `_LightPrefetcher`.
- Replaced ready-first candidate scanning plus `concurrent.futures.wait()` with a condition-variable completion queue.
- Preserved pinned-ring release semantics and original resident frame-index storage.
- Recorded completion-queue counters in resident I/O artifacts and the resident light pipeline profile:
  - `prefetch_ready_queue_callback_count`
  - `prefetch_ready_queue_wait_count`
  - `prefetch_ready_queue_wait_s`
- Ran a real 200-light prefetch-depth probe after Gate542 ready-first.
- Kept default prefetch depth at 24 because the probe did not show an end-to-end win from deeper prefetch.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_light_prefetcher_ready_index_selects_completed_candidate tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto`
- `.venv\Scripts\python.exe -m pytest -q`
- Real prefetch probe for depths `16`, `24`, `32`, and `48` under `C:\glass_runs\phase2_s2_gate543_ready_prefetch_probe\runs_20260623_142849`.
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `Get-FileHash` SHA256 comparison for master, weight, coverage, low/high rejection, and DQ maps versus Gate542.
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 5.257148 --reference-time-seconds 1092.541 --glass-label "GLASS Gate543 completion-queue resident" --reference-label "WBPP black-box fastIntegration" --glass-scale=1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default\integration\resident_coverage_map_H.fits --min-coverage 190`

## Test Results

- Focused pytest: passed.
- Full pytest: `1179 passed in 42.69s`.
- `git diff --check`: no whitespace errors; only expected Windows LF-to-CRLF warnings.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real Prefetch Probe

- Probe root: `C:\glass_runs\phase2_s2_gate543_ready_prefetch_probe\runs_20260623_142849`.
- Results:
  - prefetch 16: shell `5.446844 s`, internal `5.06957490002969 s`;
  - prefetch 24: shell `5.337614 s`, internal `4.98283779999474 s`;
  - prefetch 32: shell `5.363577 s`, internal `4.9905124999932 s`;
  - prefetch 48: shell `5.714103 s`, internal `5.33984980004607 s`.
- Decision: keep the default at prefetch depth 24.

## Real 200-Light Result

- Run path: `C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default`.
- Shell elapsed: `5.257148 s`.
- Internal elapsed: `4.8933528999914415 s`.
- Calibration order mode: `ready_first_single_master_group`.
- Ready-order enabled: true.
- Out-of-order consumed frames: `71`.
- Ready-selection wait included in read wait: `1.1693598999991082 s`.
- Prefetch ready queue callbacks: `200`.
- Prefetch ready queue wait count: `90`.
- Prefetch ready queue wait time: `1.1662104998831637 s`.
- Light read/upload/calibrate: `2.5817079999833368 s`.
- Resident registration/warp: `0.25297270010923967 s`.
- Resident integration: `0.30424030002905056 s`.
- Output write: `0.22156090004136786 s`.
- FITS read mode: `native_u16_gpu`.
- FITS spec cache hits: `200`.

## Numerical Validation

- SHA256 bitwise equality versus Gate542 for:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`
  - `resident_dq_map_H.fits`
- WBPP compare:
  - speedup versus WBPP FastIntegration timing: `207.82009561077604x`;
  - compared pixels: `56997300`;
  - coverage fraction: `0.9892770479074376`;
  - RMS diff: `0.0004279821839256963`;
  - p99 abs diff: `0.0001313822576776147`;
  - robust-fit RMS diff on fit pixels: `4.2529498303511286e-05`.

## Artifacts

- Summary JSON: `runs/checkpoints/s2_gate_543_completion_queue_summary.json`.
- Prefetch probe: `C:\glass_runs\phase2_s2_gate543_ready_prefetch_probe\runs_20260623_142849\prefetch_probe_summary.json`.
- Real run: `C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default`.
- Hash comparison: `C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default\hash_compare_gate542.json`.
- WBPP compare JSON/HTML:
  - `C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
  - `C:\glass_runs\phase2_s2_gate543_completion_queue\runs_20260623_143136\completion_queue_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html`

## Known Limitations

- This gate is scheduler hardening and observability, not a speed win.
- The default run is slightly slower than Gate542 on the warm-cache benchmark.
- Python still owns one future per frame; the next meaningful optimization should move multi-file raw FITS queueing into native code.

## Next Step

- Implement a native multi-file raw FITS queue or native read-to-calibration stream feeder so Python no longer orchestrates individual frame reads.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned scheduler logic, GLASS artifacts, FITS headers/data, and user-generated benchmark/reference outputs only.
- No external proprietary implementation source was read, copied, summarized, or reworked.
