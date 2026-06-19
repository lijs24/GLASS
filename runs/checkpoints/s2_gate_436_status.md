# S2-Gate 436 Status: Resident Cold/Warm Throughput Optimization

## Result

Passed.

Gate436 hardens the resident shared master cache into a first-class auditable
artifact and verifies cold/warm 200-light behavior. It does not change
calibration math, registration, warp, rejection, frame admission, or output
pixels.

## Completed

- Added `src/glass/engine/resident_master_cache.py`.
- Resident CUDA now writes `resident_master_cache.json`.
- `resident_artifacts.json` and `integration_results.json` now link to the
  resident master-cache summary.
- Added helper tests and strengthened the shared-cache resident CUDA test.
- Ran cold and warm real M38 H 200-light benchmarks with the same shared cache.
- Updated Phase 2 documentation and algorithm source ledger.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate436_cold_shared_cache_20260619_204953" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953"

.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953"

.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate436_cold_shared_cache_20260619_204953" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate436_cold_shared_cache_20260619_204953\report.html"

.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953\report.html"

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate436_cold_shared_cache_20260619_204953\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate436_cold_vs_gate435_compare.html" --glass-label "Gate436 cold shared cache" --reference-label "Gate435 dq pixel closure"

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_vs_gate435_compare.html" --glass-label "Gate436 warm shared cache" --reference-label "Gate435 dq pixel closure"

.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_436_cuda_doctor.json

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_cache.py tests\test_resident_dq_pixel_closure.py tests\test_resident_frame_mask_contract.py tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests: `105 passed in 9.52s`.
- Full test suite: `1024 passed in 38.04s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_436_cuda_doctor.json`.

## Real 200-Light Benchmark

- Shared cache:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953`.
- Cold run:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate436_cold_shared_cache_20260619_204953`.
- Warm run:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953`.
- No explicit frame masks were supplied.
- Registration status remained `192 ok`, `7 excluded`, `1 reference`.
- Frame mask summary remained `193 active`, `7 masked`,
  `0 unaudited zero-weight`.
- DQ pixel closure passed on cold and warm runs.

## Timing

| Metric | Cold | Warm |
| --- | ---: | ---: |
| total elapsed | `29.058186 s` | `17.406804 s` |
| master build/load | `11.177422 s` | `0.396202 s` |
| light read/upload/calibrate | `17.337112 s` | `6.636808 s` |
| resident registration/warp | `1.636686 s` | `1.638581 s` |
| resident integration | `0.299385 s` | `0.294612 s` |
| output write | `2.557732 s` | `2.379084 s` |

- Warm speedup vs cold: `1.669358x`.
- Warm master build/load speedup vs cold: `28.211388x`.
- Estimated peak VRAM: `47.311736 GiB`.

## Master Cache Evidence

- Cold cache summary: `1 miss`, `0 hits`, `1 complete shared set`,
  `739,816,130` required bytes.
- Warm cache summary: `1 hit`, `0 misses`, `1 complete shared set`,
  `739,816,130` required bytes.
- Cold manifest:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate436_cold_shared_cache_20260619_204953\resident_master_cache.json`.
- Warm manifest:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953\resident_master_cache.json`.

## Numerical Comparison

Cold vs Gate435:

- Shape match: true.
- Compared pixels: `61,651,200`.
- p50/p90/p99/p999 absolute delta: `0.0` / `0.0` / `0.0` / `0.0`.
- RMS delta: `0.0`.
- Relative RMS delta: `0.0`.
- Robust fit scale/offset: `1.0` / `0.0`.

Warm vs Gate435:

- Shape match: true.
- Compared pixels: `61,651,200`.
- p50/p90/p99/p999 absolute delta: `0.0` / `0.0` / `0.0` / `0.0`.
- RMS delta: `0.0`.
- Relative RMS delta: `0.0`.
- Robust fit scale/offset: `1.0` / `0.0`.

## Known Limitations

- Gate436 optimizes repeated same-calibration runs through shared master-cache
  reuse; first cold runs still pay master construction cost.
- The remaining warm-cache bottleneck is now `light_read_upload_calibrate`.
- The resident winsorized mode remains the existing fast approximation and is
  still recorded as not CPU-baseline parity.

## Next Step

S2-Gate 437 should profile and reduce the warm-cache
`light_read_upload_calibrate` bucket while preserving Gate436 master-cache hit
evidence, DQ pixel closure, frame counts, and zero output delta.

## Clean-Room Compliance

Compliant. Gate436 used GLASS-owned cache artifacts, user-provided image data,
and generic cache-file completeness accounting. It did not inspect external
proprietary implementation source, modify input image directories, change CUDA
drivers, or touch unrelated system/VPN settings.
