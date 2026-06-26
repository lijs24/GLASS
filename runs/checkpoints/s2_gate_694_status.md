# S2-Gate 694 Status: No-Reject Initial Sum Fast Path

Gate: S2-Gate 694.

## Completed

- Added a native resident hardened winsorized CUDA fast path that accumulates
  first-pass frame-axis `sum`, `weight_sum`, and `coverage` while collecting
  samples.
- Reuses those first-pass totals when the rejection guard makes
  `allow_rejection=false`, avoiding the final no-reject resident-stack reread
  for that pixel.
- Preserved the default unit-positive mask-scan frame-axis accumulation order.
- Left the selected-buffer reuse experiment excluded from this fast path.
- Added native profile fields:
  - `no_rejection_initial_accumulation_fast_path_enabled`;
  - `no_rejection_initial_accumulation_model`.
- Added a CPU-parity CUDA test covering zero-weight frames, NaN samples, finite
  samples, and `max_reject_fraction=0.0`.
- Documented the implementation and the real-data neutral performance result.

## Commands

```powershell
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_no_reject_initial_sum_matches_cpu --tb=short
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma" --tb=short
.\.venv\Scripts\python.exe -m ruff check tests/test_cuda_resident_stack.py
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate693_component_budget\runs_20260627_040000\component_budget_candidate --candidate-run C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate --out C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\gate694_phase2_mainline_ab.json --markdown C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\gate694_phase2_mainline_ab.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate --out C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\gate694_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\gate694_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native CUDA target: up to date; `_glass_cuda_native` target available.
- New focused CUDA parity test: `1 passed in 0.18 s`.
- Focused resident hardened winsorized tests:
  `21 passed, 57 deselected in 0.31 s`.
- Ruff: `All checks passed`.
- Full pytest: `1438 passed in 67.82 s`.

## Real 200-Light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate`.
- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\gate694_phase2_mainline_audit.json`.
- Phase 2 mainline A/B:
  `C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\gate694_phase2_mainline_ab.json`.
- Audit status: passed.
- A/B status: passed.
- Input lights: `200`.
- Active/masked frames: `193 / 7`.
- Tracked integration FITS maps: `6`.
- Hash mismatches: `0`.
- Component budget failures: `0`.
- Frame-index alignment: passed.

## Timing

Gate693 baseline:

- `resident_light_read_upload_calibrate`: `3.1031843000091612 s`.
- `resident_registration_warp`: `0.2666722999420017 s`.
- `resident_local_normalization`: `0.38270870002452284 s`.
- `resident_integration`: `3.2597308000549674 s`.
- Native hardened kernel sync: `3.1401549 s`.

Gate694 candidate:

- `resident_light_read_upload_calibrate`: `3.161795800086111 s`.
- `resident_registration_warp`: `0.2603286998346448 s`.
- `resident_local_normalization`: `0.3541327000129968 s`.
- `resident_integration`: `3.261199799948372 s`.
- Native hardened kernel sync: `3.140564 s`.
- `download_s`: `0.1160999 s`.
- `weight_map_host_synthesis_s`: `0.0353835 s`.
- `sample_reuse_strategy`: `frame_mask_global_reread_unit_positive_weights`.
- `native_kernel_capacity_selector`: `small_256`.

Elapsed ratio versus Gate693: `0.9996989442544147`.

Interpretation: this is output-stable but performance-neutral on the real
200-light benchmark. It proves that final no-reject reread elimination is not
the current integration bottleneck.

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend: available.

## Known Limits

- This gate does not improve the measured 200-light resident integration time.
- It does not change percentile selection, winsorized statistics, rejection
  thresholds, DQ semantics, frame admission, registration, warp, local
  normalization, or calibration.
- It does not address larger active-frame groups above the current native
  bounded reducer capacity.
- C drive free space during the gate was about `19.91 GiB`; future large A/B
  runs should avoid unnecessary duplicate run directories.

## Next Step

Return to a larger Phase 2 mainline surface:

1. redesign the deterministic resident winsorized reducer around cooperative or
   segmented order-statistic/statistics work; or
2. improve the resident read/upload/calibration pipeline with deeper pinned
   staging and decode/H2D/calibration overlap.

Avoid spending the next gate on another narrow no-reject reread micro-change
unless a measured profile shows it is directly blocking the mainline.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA kernels and wrappers, GLASS CPU
baseline tests, GLASS-generated artifacts, and user-owned 200-light benchmark
data. No external or proprietary implementation source was inspected, copied,
summarized, or reworked.
