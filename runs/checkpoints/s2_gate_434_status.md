# S2-Gate 434 Status

## Gate

S2-Gate 434: StackEngine Resident Default, DQ Mask Contract, And 200-Light Regression.

## Completed Work

- Added `src/glass/engine/resident_frame_mask.py`.
- Resident CUDA now builds a frame-level mask admission contract after registration,
  weighting, and local normalization, but before resident StackEngine integration.
- Any resident frame with zero or non-finite integration weight must have an
  auditable reason before integration starts.
- New run artifact: `resident_frame_masks.json`.
- `integration_results.json` now links the resident frame-mask contract summary.
- `resident_artifacts.json` now links each group's frame-mask contract summary.
- `frame_accounting.json` now reads `resident_frame_masks.json`, promotes
  registration-quality masks to `quality_rejected`, and reports resident mask
  active/masked/unaudited counts.
- Updated `docs/algorithm_sources.md` and `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_frame_mask_contract.py tests\test_resident_registration_quality.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_frame_mask_contract.py tests\test_resident_registration_quality.py tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_434_cuda_doctor.json
.\.venv\Scripts\python.exe -m glass.cli run --plan "C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit
.\.venv\Scripts\python.exe -m glass.cli report --run "C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619\report.html"
.\.venv\Scripts\python.exe -m glass.cli compare --glass "C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619\integration\resident_master_H.fits" --out "C:\glass_runs\final_m38_h_200\glass_s2_gate434_vs_gate433_compare.html" --glass-label "Gate434 stack dq" --reference-label "Gate433 auto quality"
.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_accounting.py tests\test_resident_frame_mask_contract.py tests\test_resident_registration_quality.py tests\test_resident_cuda_run.py tests\test_resident_result_contract.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- New focused resident mask and quality tests: `10 passed in 0.07s`.
- Focused resident/frame-accounting/CLI regression: `108 passed in 9.59s`.
- Full test suite: `1017 passed in 37.96s`.

## Real 200-Light Regression

- Run directory:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619`.
- Baseline:
  `C:\glass_runs\final_m38_h_200\glass_s2_gate433_auto_quality_20260619`.
- No explicit `--exclude-frame-id` masks were used.
- Resident dispatch: StackEngine `stack`.
- Frame counts: `192 ok`, `7 excluded`, `1 reference`.
- Frame-mask contract: `193 active`, `7 masked`, `0 unaudited zero-weight`.
- Frame accounting: `193 integrated`, `7 quality_rejected`.
- Rejected frame ids:
  `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`,
  `F000218`.

## Timing

- Total elapsed: `28.035511 s`.
- `light_read_upload_calibrate`: `17.176694 s`.
- `resident_registration_warp`: `1.632852 s`.
- `resident_integration`: `0.290809 s`.
- `output_write`: `2.623330 s`.
- Estimated peak VRAM: `47.311736 GiB`.

## Numerical Comparison

Gate434 output compared with Gate433 auto-quality output:

- Shape match: true.
- p50/p90/p99 absolute difference: `0.0 / 0.0 / 0.0`.
- RMS difference: `0.0`.
- Relative RMS difference: `0.0`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Doctor artifact: `runs/checkpoints/s2_gate_434_cuda_doctor.json`.

## Artifacts

- `runs/checkpoints/s2_gate_434_stack_dq_summary.json`.
- `runs/checkpoints/s2_gate_434_cuda_doctor.json`.
- `C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619\resident_frame_masks.json`.
- `C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619\frame_accounting.json`.
- `C:\glass_runs\final_m38_h_200\glass_s2_gate434_stack_dq_20260619\report.html`.
- `C:\glass_runs\final_m38_h_200\glass_s2_gate434_vs_gate433_compare.html`.
- `C:\glass_runs\final_m38_h_200\glass_s2_gate434_vs_gate433_compare.json`.

## Known Limitations

- The new contract is frame-level. Pixel-level invalid warp footprints and
  low/high rejection masks remain represented by DQ and count maps.
- Resident winsorized sigma remains the existing fast approximation unless the
  opt-in hardened mode is selected.
- The dominant runtime cost remains read/decode/upload/calibration and output
  writing, not integration math.

## Next Step

S2-Gate 435 should optimize resident StackEngine runtime and tighten DQ pixel
closure against geometric warp coverage, post-rejection coverage, and low/high
rejection maps while preserving the Gate434 accepted-frame set.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned code, GLASS-generated artifacts, and the
user-provided real dataset as runtime input. It did not inspect external
implementation source, proprietary code, package contents, or modify input image
directories.
