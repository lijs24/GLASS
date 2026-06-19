# S2-Gate 438 Status: FITS Decode Cost Reduction Probe

## Result

Passed as a bounded probe, with no default promotion.

Gate438 adds a simple-primary FITS reader and resident CUDA read-mode switch so
the warm-cache light read/decode bucket can be tested without changing image
math. The real 200-light run proves zero output delta and a small same-code
light-pipeline improvement, but total runtime did not improve, so `astropy`
remains the conservative default reader.

## Completed

- Added `src/glass/io/fits_fast.py`.
- Added resident `--resident-fits-read-mode astropy|auto|fast`.
- Recorded `fits_read_mode`, `fits_backend_counts`, and
  `fits_fast_fallback_reason_counts` in resident I/O artifacts.
- Added tests for the fast FITS parser, BSCALE/BZERO/BLANK parity, unsupported
  FITS rejection, and resident backend-count artifacts.
- Ran real M38 H 200-light fast-auto and astropy-control warm-cache runs.
- Updated Phase 2 documentation and algorithm source ledger.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_uses_planner_matching_master_sets

.\.venv\Scripts\python.exe -m pytest -q tests\test_fits_io.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_uses_planner_matching_master_sets tests\test_resident_light_pipeline_profile.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912" --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953" --resident-fits-read-mode auto

.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\report.html"

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate437_profiled_warm_v1_20260619_210732\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\gate438_vs_gate437.html" --glass-label gate438_fastfits_auto --reference-label gate437_profiled_warm

.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148" --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\final_m38_h_200\glass_s2_gate436_shared_master_cache_20260619_204953" --resident-fits-read-mode astropy

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\gate438_fast_auto_vs_astropy_control.html" --glass-label gate438_fast_auto --reference-label gate438_astropy_control

.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\report.html"

.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_438_cuda_doctor.json

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests: `41 passed in 5.14s`.
- Full test suite: `1030 passed in 37.85s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_438_cuda_doctor.json`.

## Real 200-Light Results

Fast-auto probe:

- Run:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912`.
- Total elapsed: `17.602828 s`.
- `light_read_upload_calibrate`: `6.563764 s`.
- `light_read_wait_wall`: `3.832019 s`.
- Native H2D+calibrate/store: `2.001212 s`.
- FITS backend counts: `fast_simple=200`.
- FITS fallback counts: `{}`.

Same-code astropy control:

- Run:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148`.
- Total elapsed: `17.288359 s`.
- `light_read_upload_calibrate`: `6.624954 s`.
- `light_read_wait_wall`: `3.939295 s`.
- Native H2D+calibrate/store: `1.958448 s`.
- FITS backend counts: `astropy_scaled_memmap=200`.

Interpretation:

- Fast-auto reduced the same-code light pipeline by about `0.061190 s`.
- Fast-auto reduced consumer read wait by about `0.107277 s`.
- Fast-auto was slower in total by about `0.314469 s`.
- The measured total-runtime evidence is not strong enough to promote `auto`
  or `fast` as default.

## Invariants

- Shared master-cache hit: yes.
- DQ pixel closure: passed.
- Frame mask summary: `193 active`, `7 masked`, `0 unaudited zero-weight`.
- Fast-auto vs Gate437: shape match true, RMS `0.0`, relative RMS `0.0`,
  max absolute delta `0.0`, p99.9 absolute delta `0.0`.
- Fast-auto vs same-code astropy control: shape match true, RMS `0.0`,
  relative RMS `0.0`, max absolute delta `0.0`, p99.9 absolute delta `0.0`.

## Artifacts

- Summary JSON: `runs/checkpoints/s2_gate_438_fast_fits_summary.json`.
- CUDA doctor JSON: `runs/checkpoints/s2_gate_438_cuda_doctor.json`.
- Fast-auto report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\report.html`.
- Astropy-control report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_astropy_control_warm_20260619_213148\report.html`.
- Fast-auto vs Gate437 compare:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\gate438_vs_gate437.html`.
- Fast-auto vs astropy-control compare:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate438_fastfits_warm_20260619_212912\gate438_fast_auto_vs_astropy_control.html`.

## Known Limitations

- The fast reader supports only simple 2D uncompressed primary FITS images.
- `auto` and `fast` are explicit probes, not defaults.
- The real benchmark shows light-bucket improvement but no total-runtime
  improvement.
- The next likely optimization needs direct decode into reusable pinned host
  buffers or a native-assisted byteswap/scale/copy path.

## Next Step

S2-Gate439 should prototype a resident direct decode/upload path that reduces
host materialization and H2D staging together, preserves zero output delta, and
beats the same-code astropy default in total runtime before any default change.

## Clean-Room Compliance

Compliant. Gate438 used public FITS format semantics, GLASS-owned readers and
tests, GLASS-generated artifacts, and the user's local real benchmark data. It
did not inspect external proprietary implementation source, modify input image
directories, change registration or rejection math, modify CUDA drivers, or
touch unrelated system/VPN settings.
