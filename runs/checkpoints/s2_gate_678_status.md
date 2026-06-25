# S2-Gate 678 Status: Selected-Buffer Reuse Probe

## Gate

S2-Gate 678 - resident hardened winsorized selected-buffer reuse probe.

## Completed

- Added opt-in native/CUDA reducer branch controlled by
  `GLASS_CUDA_UNIT_WEIGHT_SELECTED_REUSE=1`.
- The branch is admitted only for the existing unit-positive mask-scan family
  and never changes the default route.
- Native profiles now record:
  - `unit_positive_selected_reuse_requested`
  - `unit_positive_selected_reuse_enabled`
  - `unit_positive_selected_reuse_reason`
  - `sample_reuse_strategy=selected_buffer_reuse_unit_positive_weights`
- Added focused CUDA/CPU parity coverage for the selected-buffer route.
- Ran current-HEAD default and selected-buffer 200-light A/B on the real M38 H
  dataset.
- Documented the branch as a negative optimization result: correct as an
  opt-in diagnostic path, but not deterministic against the default and slower
  on the 200-light benchmark.

## Commands

- `cmake --build build --config Release --target _glass_cuda_native`
  through the VS BuildTools environment.
- `python -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma_unit_weight_default_uses_mask_scan or hardened_winsorized_sigma_unit_weight_selected_reuse_matches_cpu or hardened_winsorized_sigma_unit_weight_mask_scan_matches_cpu or hardened_winsorized_sigma_unit_weight_local_reuse_matches_cpu or hardened_winsorized_sigma_unit_weight_map_from_coverage"`
- `python -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\default_head --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `GLASS_CUDA_UNIT_WEIGHT_SELECTED_REUSE=1 python -m glass.cli run ... --out C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\selected_reuse`
- `python -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\selected_reuse --out C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\gate678_selected_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\gate678_selected_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green`
- `python -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights --candidate-run C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\default_head --out C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\gate678_default_vs_gate677_regression.json --markdown C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\gate678_default_vs_gate677_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `python -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\default_head --candidate-run C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\selected_reuse --out C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\gate678_selected_vs_default_regression.json --markdown C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\gate678_selected_vs_default_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `python -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\selected_reuse\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\default_head\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\gate678_selected_vs_default_master.html --glass-coverage-map C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\selected_reuse\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-label selected_reuse --reference-label default_head`
- `python -m pytest -q`

## Test Results

- Native CUDA rebuild: passed.
  - Environment: VS BuildTools + CUDA 13.2.
  - Warnings: existing CUDA/MSVC codepage warnings and existing C4389
    signed/unsigned warning.
- Focused CUDA resident hardened tests: `5 passed, 72 deselected`.
- Full pytest: `1420 passed in 63.63s`.

## Real 200-Light Results

- Default current-HEAD run:
  `C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\default_head`
- Selected-buffer candidate:
  `C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\selected_reuse`
- Selected-buffer candidate mainline audit:
  - Status: passed
  - Failed checks: `[]`
  - Input lights: `200`
  - Active frames: `193`
- Default current-HEAD regression against Gate677:
  - Status: passed
  - Failed checks: `[]`
  - Elapsed ratio: `0.9913605001863092`
- Selected-buffer regression against default:
  - Status: failed
  - Failed checks: `resident_determinism_passed`
  - All contract/frame-mask/DQ/master-cache/memory-lifecycle checks passed
  - Elapsed ratio: `1.0094310426288307`
- Timing:
  - Default resident integration: `3.3610659999540076 s`
  - Selected resident integration: `3.4472310000564903 s`
  - Default native kernel sync: `3.2432453 s`
  - Selected native kernel sync: `3.3259804 s`
- Master compare selected vs default at coverage >= `190`:
  - Shape match: true
  - Coverage fraction: `0.9749333995120938`
  - RMS diff: `0.000560800848695079`
  - Relative RMS diff: `1.7645079997153338e-06`
  - P99 absolute diff: `3.814697265625e-05`

## CUDA Availability

CUDA is available on this machine. Native CUDA extension rebuilt and CUDA tests
executed. The build used CUDA Toolkit 13.2.

## Known Limits

- `GLASS_CUDA_UNIT_WEIGHT_SELECTED_REUSE=1` is not promoted. It changes strict
  resident determinism versus the default because quickselect partitions the
  sample buffer before later accumulation passes.
- The selected-buffer candidate is slower on the real 200-light benchmark.
- This gate does not implement the future deterministic cooperative/segmented
  reducer and does not improve H2D/read/calibration overlap.

## Next Step

Return to a larger mainline lever:

- deterministic cooperative/segmented hardened reducer that preserves default
  accumulation semantics; or
- resident read/H2D/calibration pipeline overlap and buffering.

Avoid spending more gates on per-thread local-array reuse unless a new design
preserves strict determinism and wins a real 200-light A/B.

## Clean-Room

Compliant. This gate uses GLASS-owned CUDA kernels/wrappers, GLASS CPU baseline
tests, GLASS-generated artifacts, and user-owned benchmark data. It does not
inspect external/proprietary implementation source, does not modify input
directories, and does not copy external algorithms.
