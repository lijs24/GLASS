# Optimization Goal Completion Audit: M38 resident performance path

## Objective Restatement

The active optimization goal requires GLASS to reduce the M38 200-light resident CUDA benchmark from the previous roughly 100-second class baseline, with two重点 paths:

1. Improve the I/O + upload + calibration pipeline with CPU RAM prefetch, pinned host memory, async H2D, CUDA stream scheduling, resident stack writes, and fine timing.
2. Reduce resident registration/warp orchestration and host/device round trips through resident/batched star catalog, descriptor/scoring/refine/warp scheduling, while preserving clean-room constraints.

Final acceptance requires the same M38 200-light dataset to run significantly faster than the previous `111.95 s` GLASS baseline and remain within established WBPP/current-GLASS compare tolerances.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Real M38 benchmark, at least 200 lights | `runs\benchmarks\m38_acceptance_audit_pinnedring_coarse4.md` reports `light: 200` | PASS |
| Calibration frames at least 20 each | Same audit reports `bias: 20`, `dark: 20`, `flat: 20` | PASS |
| Do not modify original data directory | All outputs written under `C:\glass_runs\final_m38_h_200\...`; no input-tree writes were used | PASS |
| Fine timing for read/decode/H2D/calibrate/store | `resident_artifacts.json` in the pinned-ring run records FITS open, materialize/decode, worker read/decode, H2D, calibrate/store, combined H2D/calibrate/store, and host copy timing | PASS |
| CPU RAM prefetch | `_LightPrefetcher` prefetches light frames with configurable `--resident-prefetch-frames` and `--resident-prefetch-workers`; M38 command used 16 slots and 8 workers | PASS |
| Pinned host memory | Native `host_pinned_empty_f32` uses `cudaHostAlloc`; pinned-ring artifact reports `prefetch_host_pinned_bytes = 3945676800` | PASS |
| Async H2D from pinned buffers | Native `calibrate_frame_host_async_timed` uses `cudaMemcpyAsync` on the calibration stream; artifact mode is `pinned_ring` and host copy is `0.0 s` | PASS |
| CUDA stream scheduling explored/used | Resident host async path records CUDA events on `calibrate_stream_`; CUDA Graphs remain a future optimization, but the requirement allowed streams or graphs | PASS |
| Synthetic/unit correctness for the new path | `test_resident_stack_host_async_calibration_accepts_pinned_host_array` compares host-async CUDA calibration against CPU | PASS |
| Full test suite remains green | Full pytest after the change: `183 passed` | PASS |
| Registration/warp resident batching | Earlier optimization gates added `star_grid_top_nms_candidates_batch`, shared-memory catalog sorting, candidate/stride controls, and resident triangle timing fields; current pinned-ring M38 run records `resident_registration_warp = 11.310889499611221 s` | PASS |
| Registration/warp CPU/GPU and astroalign behavior checks | Existing tests include resident stack warp/registration CPU references and `compare_astroalign_gpu_alignment` coverage; full pytest passed | PASS |
| Real M38 before/after speed comparison | Baseline `111.95 s`, previous pageable readprofile `37.132812800002284 s`, pinned-ring run `31.245748999994248 s` | PASS |
| WBPP black-box speed comparison | WBPP FastIntegration timing `1092.541 s`; pinned-ring speedup `34.9660685042372x` | PASS |
| Result consistency compare report | `compare_vs_wbpp_fastintegration_scaled_coverage190.html/json` exists for the pinned-ring run | PASS |
| Result within established tolerance | Acceptance audit passed: RMS `0.001558294284488301`, p99 absolute diff `0.00043095467146486016`, coverage fraction `0.9574613308418977` | PASS |
| Current GLASS parity preserved | Pinned-ring master SHA matches previous pageable readprofile master SHA: `F9F7E173B5BA7EC582DB7460B7F051E0B75B2E2A48C0ADF035940A071CD79CC2`; coverage SHA also matches | PASS |
| Per-Gate checkpoint and commit | Latest checkpoint: `runs\checkpoints\optimization_gate_11_resident_pinned_ring_status.md`; commit: `106bbc7 perf: add resident pinned ring upload path` | PASS |
| Clean-room | Checkpoints state no PixInsight/WBPP/PJSR official source was read or copied; compare consumes only user-generated WBPP black-box outputs/logs | PASS |

## Current Best M38 Result

- Run directory: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_pinnedring_coarse4`
- Total GLASS time: `31.245748999994248 s`
- Previous GLASS baseline: about `111.95 s`
- PixInsight/WBPP FastIntegration black-box time: `1092.541 s`
- Speedup vs previous GLASS baseline: about `3.58x`
- Speedup vs WBPP: `34.9660685042372x`
- Active frames: `193`
- Full pytest: `183 passed`

## Remaining Optimization Opportunities

These are not blockers for the active goal, but they are the next performance work:

- Add multiple raw-light device staging buffers to overlap H2D for frame N+1 with calibration/store for frame N.
- Bound pinned-ring depth by RAM budget automatically.
- Explore CUDA Graphs or deeper fused kernels for descriptor/scoring/refine/warp once the current stream/prefetch path is stable.

## Completion Decision

The explicit final acceptance condition is met: the same M38 200-light dataset runs significantly below the previous `111.95 s` GLASS baseline, remains within established WBPP/current-GLASS compare tolerances, has tests/checkpoints/commits, and preserves clean-room constraints.
