# Optimization Goal Completion Audit

## Objective restatement

Active objective: reduce GPWBPP resident CUDA runtime on the real M38 200-light benchmark below the previous 111.95 s baseline, while preserving WBPP/current-GPWBPP comparison quality. The objective also calls out two optimization paths: I/O/upload/calibration overlap and resident registration/warp batching.

## Evidence inspected

- Code commits through `e11ddc6`.
- Full test command: `.\\.venv\\Scripts\\python.exe -m pytest -q`.
- Acceptance audit: `runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48.json`.
- M38 artifacts under `C:\gpwbpp_runs\final_m38_h_200`.
- Checkpoints:
  - `runs\checkpoints\optimization_gate_00_fine_timing_status.md`
  - `runs\checkpoints\optimization_gate_01_m38_fine_timing_baseline_status.md`
  - `runs\checkpoints\optimization_gate_02_resident_prefetch_status.md`
  - `runs\checkpoints\optimization_gate_02_m38_prefetch_benchmark_status.md`
  - `runs\checkpoints\optimization_gate_03_registration_component_timing_status.md`
  - `runs\checkpoints\optimization_gate_03_m38_registration_component_benchmark_status.md`
  - `runs\checkpoints\optimization_gate_04_triangle_refine_stride_control_status.md`
  - `runs\checkpoints\optimization_gate_04_m38_refine_stride_benchmark_status.md`
  - `runs\checkpoints\optimization_gate_05_m38_triangle_candidate_sweep_status.md`

## Prompt-to-artifact checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Fine timing split for read/decode/H2D/calibrate/store | `resident_artifacts.json` contains `fine_timing`, `light_read_decode`, `light_read_decode_worker`, `light_h2d_calibrate_store`, and loop accounting fields | Done |
| CPU RAM prefetch | `--resident-prefetch-frames`; best run uses `prefetch=2` | Done |
| Pinned host memory | No native pinned host buffer implementation in current resident path | Missing |
| Async H2D / CUDA stream overlap | No resident async H2D stream pipeline; `calibrate_frame` still synchronizes | Missing |
| CUDA stream/graph parallel calibration | Not implemented | Missing |
| Registration/warp component timing | `fine_timing.registration_component_seconds` reports pixel refine, catalog, descriptor fit, warp, orchestration | Done |
| Reduce registration/warp bottleneck | Best accepted run reduces registration/warp to about 21.04 s from about 58.39 s | Done |
| Batched resident star catalog/descriptor/scoring/warp scheduling | Not implemented; current improvement comes from stride/candidate controls | Missing |
| Real M38 before/after timing | Baseline 111.948822 s / fine baseline 113.246565 s; best accepted 72.988996 s | Done |
| Result consistency compare report | `compare_vs_wbpp_fastintegration_scaled_coverage190.json` for best run | Done |
| Acceptance on 200 lights and 20 calibration frames each | `m38_acceptance_audit_refinefinal8_cand48.json`: 200 light, 20 bias, 20 dark, 20 flat | Done |
| Significant speedup below 111.95 s baseline | 72.988996 s, 1.5338x faster than GPWBPP baseline and 14.9686x faster than WBPP | Done |
| CUDA available and recorded | RTX PRO 6000 Blackwell, CC 12.0, 97886 MiB | Done |
| Tests green | Full pytest: 180 passed | Done |
| Gate checkpoint and commit per increment | Commits `08bd26a`, `cb84ecf`, `a6c80bf`, `4f68b3d`, `d1a8a57`, `0817cd8`, `48ea61c`, `f4f87bb`, `e11ddc6` | Done |
| Clean-room compliance | Checkpoints state no PixInsight/WBPP/PJSR source read; only black-box outputs/logs used | Done |
| Do not modify original data | Runs write under `C:\gpwbpp_runs` and repo `runs`; source data not modified | Done |

## Best accepted result

- Run: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48`
- Runtime: 72.98899570002686 s.
- WBPP black-box runtime: 1092.541 s.
- Speedup vs WBPP: 14.968571488367497x.
- Active frames: 193.
- Coverage fraction: 0.9612716865202948.
- RMS diff: 0.0016700247556533851.
- abs diff p99: 0.0004373512882739298.
- Acceptance audit status: passed.

## Completion decision

The final benchmark acceptance condition is achieved, but the full active objective is not marked complete because several explicit implementation tactics remain missing:

- pinned host memory;
- async H2D and CUDA stream overlap;
- batched resident catalog/descriptor/scoring/warp scheduling.

The next engineering step is to either formalize these as deferred follow-up goals or implement the next missing item, most likely batched resident moving catalog generation, because it is now the largest registration component.
