# S2-Gate 533 Status: Resident Prefetch Inflight Slot Guard

## Gate

S2-Gate 533

## Completed

- Returned to Phase 2 mainline performance work on the real M38 H-alpha
  200-light benchmark.
- Rejected two parameter-only high-VRAM candidates after same-window real A/B:
  `batch32/streams8/wave8` calibration and larger Lanczos3 warp chunks were
  bitwise correct but slower than the current default.
- Fixed pinned-ring prefetch capacity accounting so `_LightPrefetcher._fill()`
  uses occupied `inflight_slots` while H2D callback-release still owns popped
  futures' pinned slots.
- Added a focused regression test for that H2D window.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_light_prefetcher_counts_pinned_ring_inflight_slots`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate533_mainline_ab\runs_20260623_132500\default32_control --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe run ... --resident-calibration-batch-frames 32 --resident-calibration-streams 8 --resident-calibration-wave-frames 8`
- `.venv\Scripts\glass.exe run ... --resident-prefetch-frames 64 --resident-calibration-batch-frames 64 --resident-calibration-streams 8 --resident-calibration-wave-frames 8`
- `.venv\Scripts\glass.exe run ... --resident-warp-chunk-capacity-frames 16`
- `.venv\Scripts\glass.exe run ... --resident-warp-chunk-capacity-frames 32`
- `.venv\Scripts\glass.exe run ... --resident-warp-chunk-capacity-frames 64`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate533_prefetch_inflight_fix\runs_20260623_134500\default_after --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`

## Test Results

- Focused prefetcher regression: `1 passed in 0.58s`.
- Focused CLI/runtime smoke: `2 passed in 0.20s`.
- Focused resident CUDA native-u16 smoke: `1 passed in 0.46s`.
- Full pytest: `1175 passed in 42.69s`.

## Real 200-Light Results

- Accepted run:
  `C:\glass_runs\phase2_s2_gate533_prefetch_inflight_fix\runs_20260623_134500\default_after`.
- Before guard:
  - total elapsed `5.440552299958654 s`;
  - light loop `2.439363899989985 s`;
  - read wait `0.6564198998385109 s`;
  - `prefetch_fill_blocked_no_slot_count=31`.
- After guard:
  - shell `5.795757 s`;
  - total elapsed `5.4339563000248745 s`;
  - light loop `2.423997799982317 s`;
  - read wait `0.6388012003153563 s`;
  - `prefetch_fill_blocked_no_slot_count=0`.
- Master, weight, coverage, low rejection, high rejection, and DQ maps are
  bitwise identical to the current default baseline.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limits

- Runtime gain is small; this gate is a pinned-ring scheduling hygiene fix, not
  a headline speedup.
- Larger calibration lanes and larger warp chunks were both rejected for this
  dataset because total wall time regressed.

## Next

- Continue with substantive resident registration/warp batching or reduced
  light-loop Python orchestration.

## Clean-Room

- Compliant. The gate uses GLASS source, GLASS-generated artifacts, user-owned
  benchmark images, and user-generated WBPP black-box comparison evidence only.
  It does not inspect or copy PixInsight/WBPP/PJSR source or modify input
  directories.
