# S2-Gate 686 Status: Hardened Rejection Guard Early-Disallow

## Gate

- Gate: S2-Gate 686
- Theme: resident hardened winsorized CUDA reducer optimization
- Status: green

## Completed

- Added an exact early-disallow break to the resident hardened winsorized CUDA
  rejection-counting pass.
- The kernel now stops counting candidate low/high rejections once the partial
  count already violates the existing `min_samples` or
  `max_reject_fraction` guard.
- Preserved scientific behavior: when the guard is already impossible to pass,
  final accumulation uses the same no-rejection path that a full count would
  have selected.
- Added native profile fields:
  - `rejection_guard_early_disallow_enabled`;
  - `rejection_guard_early_disallow_model`.
- Added focused CUDA test assertions for the profile and guard-disallow parity.
- Ran a real 200-light resident CUDA A/B against Gate685.

## Commands

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && ".venv\Scripts\cmake.exe" --build build --target _glass_cuda_native --config Release'`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma"`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_minimal_output_master_only`
- `.venv\Scripts\python.exe -m ruff check tests/test_cuda_resident_stack.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.venv\Scripts\glass.exe resident-runtime-compare --run gate685_overlap=C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics --run gate686_early_disallow=C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow --baseline-label gate685_overlap --out C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\gate686_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\gate686_runtime_compare.md`
- `.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics --candidate-run C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow --out C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\gate686_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\gate686_regression_gate.md --max-elapsed-ratio 1.10 --min-active-frame-count 193 --max-masked-frame-count 7 --fail-on-failure`
- `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow --out C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\gate686_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\gate686_mainline_audit.md --min-lights 200 --min-active-frames 193 --max-masked-frames 7 --fail-on-not-green`

## Test Results

- Native CUDA rebuild: passed.
- Focused CUDA hardened winsorized tests:
  `20 passed, 57 deselected in 4.04 s`.
- Focused resident CLI hardened tests:
  `2 passed in 4.42 s`.
- Ruff: passed.
- Full pytest: `1426 passed in 66.19 s`.
- Real 200-light regression gate: passed, failed checks `[]`.
- Phase 2 mainline audit: passed, failed checks `[]`.
- Output comparison versus Gate685:
  - direct SHA256: all six integration FITS outputs identical;
  - array compare: all six integration FITS outputs array-identical with
    `max_abs=0.0` and `rms=0.0`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA Toolkit used for native rebuild: 13.2.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow`
- Gate685 baseline elapsed: `12.43947100022342 s`.
- Gate686 elapsed: `12.344183000386693 s`.
- Elapsed ratio: `0.9923398671989334`.
- Active/masked frames: `193 / 7`.
- Gate685 resident integration: `3.3138477000175044 s`.
- Gate686 resident integration: `3.2561724999686703 s`.
- Gate685 native kernel sync: `3.1937153 s`.
- Gate686 native kernel sync: `3.1232872 s`.
- Native profile:
  - `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`;
  - `rejection_guard_early_disallow_enabled=true`;
  - `rejection_guard_early_disallow_model=break_reject_count_when_fraction_or_min_samples_already_fails`.

## Known Limits

- The observed speedup is modest and single-run storage/GPU scheduling variance
  remains present.
- The optimization helps only pixels where candidate low/high rejections exceed
  the guard before the full frame-axis count finishes.
- The dominant median/IQR selection and repeated frame-axis passes remain; a
  cooperative or segmented deterministic reducer is still the larger target.

## Next Step

- Continue resident integration work by designing a deterministic cooperative
  or segmented order-statistic reducer, or shift to the native
  H2D/calibrate/store wall-time slice if reducer redesign is too large for the
  next gate.

## Clean-Room Compliance

- Uses only GLASS-owned CUDA kernels, GLASS CPU/GPU rejection semantics,
  GLASS tests, and user-owned benchmark artifacts.
- Does not inspect external implementation source.
- Does not modify input image directories.
- Does not change output image pixels.
