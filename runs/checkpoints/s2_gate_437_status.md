# S2-Gate 437 Status: Warm-Cache Light Read/Upload/Calibration Pipeline

## Result

Passed.

Gate437 adds a resident light-pipeline profile contract and uses it to diagnose
the warm-cache `light_read_upload_calibrate` bucket. The gate deliberately does
not promote a larger prefetch default because the same-window benchmark shows
that the reduced read wait is offset by higher native calibration and memory
contention.

## Completed

- Added `src/glass/engine/resident_light_pipeline_profile.py`.
- Resident CUDA now records `resident_light_pipeline_profile` in both
  `resident_artifacts.json` and `integration_results.json`.
- Added unit tests for the profile classifier.
- Extended resident CUDA artifact tests.
- Ran a real 200-light profiled warm-cache control.
- Ran a bounded prefetch experiment around Gate436/Gate437 settings.
- Updated Phase 2 documentation and algorithm source ledger.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate437_profiled_warm_v1_20260619_210732" --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953"

.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate437_profiled_warm_v1_20260619_210732" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate437_profiled_warm_v1_20260619_210732\report.html"

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate437_profiled_warm_v1_20260619_210732\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate437_profiled_warm_vs_gate436.html" --glass-label "Gate437 profiled warm" --reference-label "Gate436 warm shared cache"

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate437_pf20_w12_20260619_205936\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate436_warm_shared_cache_20260619_204953\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate437_pf20_w12_vs_gate436.html" --glass-label "Gate437 pf20_w12" --reference-label "Gate436 warm shared cache"

.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_437_cuda_doctor.json

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_light_pipeline_profile.py tests\test_resident_master_cache.py tests\test_resident_dq_pixel_closure.py tests\test_resident_frame_mask_contract.py tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q
```

The prefetch experiment also ran `pf16_w10`, `pf20_w12`, `pf16_w7`,
`pf20_w7`, and a same-window throughput-v1 control; exact run directories and
metrics are recorded in
`runs/checkpoints/s2_gate_437_light_pipeline_profile_summary.json`.

## Test Results

- Focused tests: `107 passed in 9.58s`.
- Full test suite: `1026 passed in 38.30s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_437_cuda_doctor.json`.

## Real 200-Light Profile

- Final run:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate437_profiled_warm_v1_20260619_210732`.
- Shared cache:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953`.
- Total elapsed: `17.340157 s`.
- `master_build_or_load`: `0.436499 s`.
- `light_read_upload_calibrate`: `6.557069 s`.
- `light_read_wait_wall`: `3.834345 s`.
- Native H2D+calibrate/store: `1.974900 s`.
- Light-loop unaccounted/orchestration: `0.734282 s`.
- `resident_registration_warp`: `1.637722 s`.
- `resident_integration`: `0.292218 s`.
- Output write: `2.509335 s`.

Profile classification:

- Dominant component: `consumer_read_wait`.
- Read-wait fraction: `0.584765`.
- Native H2D+calibrate/store fraction: `0.301186`.
- Unaccounted/orchestration fraction: `0.111983`.
- Overlap efficiency: `0.897575`.
- Recommendation: `increase_prefetch_supply_or_reduce_decode_cost`.

## Prefetch Experiment

Same-window throughput-v1 control:

- Total: `17.159549 s`.
- Light pipeline: `6.584007 s`.
- Read wait: `3.839804 s`.
- Native H2D+calibrate/store: `2.031307 s`.

Best light-bucket variant, `prefetch=20`, `workers=12`:

- Total: `17.433144 s`.
- Light pipeline: `5.903872 s`.
- Read wait: `1.406851 s`.
- Native H2D+calibrate/store: `3.430158 s`.
- Light bucket improved by about `10.3%`, but total runtime did not improve.

Decision: do not promote a larger prefetch default in Gate437.

## Invariants

- Shared master-cache hit: yes.
- DQ pixel closure: passed.
- Registration status: `192 ok`, `7 excluded`, `1 reference`.
- Frame mask summary: `193 active`, `7 masked`, `0 unaudited zero-weight`.
- Gate437 profiled warm vs Gate436 warm: shape match true, p50/p90/p99/p999
  absolute delta `0.0` / `0.0` / `0.0` / `0.0`, RMS `0.0`, relative RMS `0.0`.
- `pf20_w12` vs Gate436 warm also produced zero pixel delta.

## Known Limitations

- Gate437 is a profiling and scheduling-evidence gate. It does not change the
  default runtime preset because the data does not justify it.
- The remaining dominant cost is FITS materialize/decode/read wait rather than
  CUDA integration or registration.
- The resident winsorized mode remains the existing fast approximation and is
  still recorded as not CPU-baseline parity.

## Next Step

S2-Gate 438 should target FITS decode cost directly: inspect the resident
prefetch FITS read path and test a bounded alternative that reduces per-frame
materialize/decode overhead while preserving zero output delta.

## Clean-Room Compliance

Compliant. Gate437 used GLASS-owned timing/cache/DQ artifacts, GLASS-generated
run outputs, and user-provided image data. It did not inspect external
proprietary implementation source, modify input image directories, change CUDA
drivers, or touch unrelated system/VPN settings.
