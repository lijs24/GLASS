# S2-Gate 695 Status: Index-Select Reuse Probe Rejected

Gate: S2-Gate 695.

## Completed

- Added an opt-in resident CUDA reducer experiment:
  `GLASS_CUDA_UNIT_WEIGHT_INDEX_SELECT_REUSE=1`.
- Implemented indexed quartile quickselect for unit-positive mask-scan resident
  hardened winsorized integration.
- The opt-in branch mutates an `unsigned short` index scratch array while
  preserving the collected `values[]` samples in original frame-axis order.
- Reused original-order samples for winsor mean, winsor variance, reject count,
  and final accumulation.
- Added native profile fields:
  - `unit_positive_index_select_reuse_requested`;
  - `unit_positive_index_select_reuse_enabled`;
  - `unit_positive_index_select_reuse_reason`;
  - `percentile_strategy`;
  - `sample_reuse_strategy`.
- Added CUDA/CPU parity coverage for the opt-in branch.
- Ran real 200-light A/B for both:
  - opt-in index-select candidate;
  - current-code default with the opt-in branch disabled.

## Commands

```powershell
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m ruff check tests/test_cuda_resident_stack.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_index_select_reuse_matches_cpu --tb=short
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma" --tb=short
$env:GLASS_CUDA_UNIT_WEIGHT_INDEX_SELECT_REUSE='1'; try { .\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_062000\index_select_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final } finally { Remove-Item Env:\GLASS_CUDA_UNIT_WEIGHT_INDEX_SELECT_REUSE -ErrorAction SilentlyContinue }
.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate --candidate-run C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_062000\index_select_candidate --out C:\glass_runs\phase2_s2_gate695_index_select\gate695_index_select_vs_gate694_ab.json --markdown C:\glass_runs\phase2_s2_gate695_index_select\gate695_index_select_vs_gate694_ab.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_062000\index_select_candidate --out C:\glass_runs\phase2_s2_gate695_index_select\gate695_index_select_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate695_index_select\gate695_index_select_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_063000\default_after_index_code --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate694_no_reject_initial_sum\runs_20260627_050000\no_reject_initial_sum_candidate --candidate-run C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_063000\default_after_index_code --out C:\glass_runs\phase2_s2_gate695_index_select\gate695_default_after_code_vs_gate694_ab.json --markdown C:\glass_runs\phase2_s2_gate695_index_select\gate695_default_after_code_vs_gate694_ab.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_063000\default_after_index_code --out C:\glass_runs\phase2_s2_gate695_index_select\gate695_default_after_code_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate695_index_select\gate695_default_after_code_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\python.exe -m pytest -q
```

The opt-in A/B command intentionally returned failure because the component
budget caught the resident integration regression. The failure is the promotion
decision evidence for this gate, not a default-path failure.

## Test Results

- Native CUDA rebuild: passed.
- New focused opt-in CUDA parity test: `1 passed in 4.72 s`.
- Focused resident hardened winsorized tests:
  `22 passed, 57 deselected in 4.90 s`.
- Ruff: `All checks passed`.
- Full pytest: `1439 passed in 67.00 s`.

## Real 200-Light Evidence

Opt-in index-select candidate:

- Run:
  `C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_062000\index_select_candidate`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate695_index_select\gate695_index_select_mainline_audit.json`.
- A/B:
  `C:\glass_runs\phase2_s2_gate695_index_select\gate695_index_select_vs_gate694_ab.json`.
- Audit status: passed.
- A/B status: failed by component budget.
- Failed checks: `["component_ratios_within_budget"]`.
- Input lights: `200`.
- Active/masked frames: `193 / 7`.
- Tracked integration FITS maps: `6`.
- Hash mismatches: `0`.
- Component budget failures: `1`.
- Failed component: `resident_integration`.

Current-code default path:

- Run:
  `C:\glass_runs\phase2_s2_gate695_index_select\runs_20260627_063000\default_after_index_code`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate695_index_select\gate695_default_after_code_mainline_audit.json`.
- A/B:
  `C:\glass_runs\phase2_s2_gate695_index_select\gate695_default_after_code_vs_gate694_ab.json`.
- Audit status: passed.
- A/B status: passed.
- Failed checks: `[]`.
- Active/masked frames: `193 / 7`.
- Hash mismatches: `0`.
- Component budget failures: `0`.

## Timing

Gate694 baseline:

- `resident_light_read_upload_calibrate`: `3.161795800086111 s`.
- `resident_registration_warp`: `0.2603286998346448 s`.
- `resident_local_normalization`: `0.3541327000129968 s`.
- `resident_integration`: `3.261199799948372 s`.
- Native hardened kernel sync: `3.140564 s`.

Opt-in index-select candidate:

- `resident_light_read_upload_calibrate`: `3.5421303999610245 s`.
- `resident_registration_warp`: `0.28471500100567937 s`.
- `resident_local_normalization`: `0.4981502000009641 s`.
- `resident_integration`: `4.369750200072303 s`.
- Native hardened kernel sync: `4.2502007 s`.
- `percentile_strategy`:
  `indexed_quartile_quickselect_preserve_frame_axis_samples`.
- `sample_reuse_strategy`:
  `index_select_original_order_reuse_unit_positive_weights`.
- A/B elapsed ratio: `1.1383340033953708`.
- Resident integration ratio: `1.3399210315606793`, above the `1.25`
  component budget.

Current-code default path:

- `resident_light_read_upload_calibrate`: `3.676609499962069 s`.
- `resident_registration_warp`: `0.28541879972908646 s`.
- `resident_local_normalization`: `0.4431101999944076 s`.
- `resident_integration`: `3.2635820999275893 s`.
- Native hardened kernel sync: `3.1433856 s`.
- `sample_reuse_strategy`:
  `frame_mask_global_reread_unit_positive_weights`.
- A/B elapsed ratio: `1.0511052525463551`.
- Hash mismatches: `0`.

Interpretation: index-select preserves output values but is slower. The default
path is unchanged and green.

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend: available.

## Known Limits

- `GLASS_CUDA_UNIT_WEIGHT_INDEX_SELECT_REUSE=1` is diagnostic only and must not
  be promoted without new evidence.
- The opt-in branch is limited to unit-positive mask-scan resident hardened
  winsorized integration.
- The experiment shows that local/index scratch pressure can dominate any
  resident-stack reread savings on the current 200-light benchmark.
- It does not improve large active-frame-count groups or the read/upload/
  calibration stage.
- Two same-turn schedule probes were also not promoted:
  - `--resident-calibration-streams 8` did not improve light read/upload/
    calibration and reduced lane fill ratio;
  - `--resident-native-completion-wave-fill-mode multi_wait --resident-native-completion-wave-fill-us 250`
    made the light stage slower.

## Next Step

Gate696 should avoid additional small reducer scratch variants. The two best
mainline options are:

1. Native-completion read-prestart/master-overlap: start raw read workers before
   warm master load/upload and consume completed buffers afterward.
2. A more radical cooperative/segmented resident winsorized reducer that avoids
   per-thread value/index scratch pressure instead of adding more local arrays.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA kernels and wrappers, GLASS CPU
baseline tests, GLASS-generated artifacts, user-owned 200-light benchmark data,
and read-only subagent analysis of GLASS project files only. No external or
proprietary implementation source was inspected, copied, summarized, or
reworked.
