# S2-Gate 435 Status: Resident StackEngine Performance And DQ Pixel Closure

## Result

Passed.

Gate435 adds a resident DQ pixel closure contract that links frame-level
admission masks to pixel-level resident DQ, geometric coverage, post-rejection
coverage, and low/high rejection sample accounting. It does not change resident
registration, warp, winsorized rejection math, or output pixels.

## Completed

- Added `src/glass/engine/resident_dq_pixel_closure.py`.
- Resident CUDA now builds, validates, writes, and links
  `resident_dq_pixel_closure.json`.
- `resident_artifacts.json` and `integration_results.json` now include the
  closure path and compact closure summary.
- Added focused tests for pass/fail closure behavior and resident CUDA artifact
  wiring.
- Updated Phase 2 documentation and algorithm source ledger.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_435_cuda_doctor.json

.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit

.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306\report.html"

.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate435_vs_gate434_compare.html" --glass-label "Gate435 dq pixel closure" --reference-label "Gate434 stack dq"

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_dq_pixel_closure.py tests\test_resident_frame_mask_contract.py tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests: `102 passed in 9.52s`.
- Full test suite: `1021 passed in 38.01s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_435_cuda_doctor.json`.

## Real 200-Light Regression

- Run directory:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306`.
- Plan:
  `C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json`.
- No explicit frame masks were supplied.
- Registration status: `192 ok`, `7 excluded`, `1 reference`.
- Frame mask summary: `193 active`, `7 masked`, `0 unaudited zero-weight`.
- Masked frame IDs: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`,
  `F000217`, `F000218`.

## Timing

- Total elapsed: `28.399995 s`.
- `master_build_or_load`: `11.412479 s`.
- `light_read_upload_calibrate`: `17.545145 s`.
- Worker FITS materialize/decode cumulative: `33.210399 s`.
- Light read overlap saved: `33.578325 s`.
- `resident_registration_warp`: `1.632386 s`.
- `resident_integration`: `0.291038 s`.
- Output write: `2.433101 s`.
- Estimated peak VRAM: `47.311736 GiB`.

Historical WBPP black-box time remains `1092.541 s`; the Gate435 runtime is
about `38.47x` faster than that recorded baseline, while preserving the Gate434
resident output exactly.

## DQ Pixel Closure

- Closure artifact:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate435_dq_pixel_closure_20260619_203306\resident_dq_pixel_closure.json`.
- Summary: passed, `1/1` groups green.
- Frame-mask active count: `193`.
- DQ provenance active count: `193`.
- Geometric warp coverage frame count: `193`.
- Rejected samples: `61,680,274`.
- Valid-sample arithmetic:
  `11,801,876,614 - 11,740,196,340 - 61,680,274 = 0`.
- DQ summary: `valid=22,720,993`, `warp_edge=1,690,704`,
  `low_rejected=12,560,911`, `high_rejected=32,082,764`.

## Numerical Comparison

- Compare target: Gate434 resident stack-DQ master.
- Shape match: true.
- Compared pixels: `61,651,200`.
- p50/p90/p99/p999 absolute delta: `0.0` / `0.0` / `0.0` / `0.0`.
- RMS delta: `0.0`.
- Relative RMS delta: `0.0`.
- Robust fit scale/offset: `1.0` / `0.0`.
- Compare report:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate435_vs_gate434_compare.html`.

## Known Limitations

- Gate435 is a validation/contract gate, not a CUDA math optimization gate.
- The resident winsorized mode is still the existing fast approximation and is
  explicitly recorded as not CPU-baseline parity.
- The largest remaining real-run wall-time buckets are cold master construction
  and the FITS decode/upload/calibration pipeline.

## Next Step

S2-Gate 436 should optimize resident cold/warm throughput: persistent
content-addressed master cache, warm-run evidence, and further reduction of
`light_read_upload_calibrate`, while preserving Gate435 DQ closure and zero
output delta unless an algorithmic change is explicitly justified.

## Clean-Room Compliance

Compliant. Gate435 used GLASS-owned artifacts, user-provided image data, and
generic DQ/count-map arithmetic. It did not inspect external proprietary
implementation source, modify input image directories, change CUDA drivers, or
touch unrelated VPN/system settings.
