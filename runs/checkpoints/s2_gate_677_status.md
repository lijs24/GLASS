# S2-Gate 677 Status: Skip Unused Unit-Weight Device Buffer

## Gate

- Gate: S2-Gate 677
- Date: 2026-06-26
- Status: passed

## Completed Work

- Removed an unused device `float32` weight-buffer allocation/upload from resident hardened winsorized integration when the selected native route is unit-positive active-index or unit-positive mask-scan.
- Kept the device weight buffer for radix-select, local-reuse, generic weighted scans, non-unit weights, and explicitly disabled mask-scan routes.
- Added native profile fields:
  - `native_weight_buffer_required`
  - `native_weight_buffer_device_materialized`
  - `native_weight_buffer_upload_skipped`
  - `native_weight_buffer_uploaded_bytes`
- Added CUDA tests covering skip/keep behavior across active-index, default mask-scan, explicit mask-scan, disabled mask/generic weighted scan, and local-reuse routes.
- Updated integration, Phase 2 hardening, validation, and algorithm-source documentation.

## Commands Run

```powershell
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_default_uses_mask_scan tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_can_be_disabled tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_local_reuse_matches_cpu
.\.venv\Scripts\python.exe -m glass.cli run --plan 'C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json' --out 'C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights' --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir 'C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final'
.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run 'C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights' --out 'C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\gate677_phase2_mainline_audit.json' --markdown 'C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\gate677_phase2_mainline_audit.md' --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run 'C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll' --candidate-run 'C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights' --out 'C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\gate677_vs_gate676_regression.json' --markdown 'C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\gate677_vs_gate676_regression.md' --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native CUDA rebuild: passed.
- Focused resident hardened CUDA tests: `5 passed in 0.45s`.
- Full pytest: `1419 passed in 73.56s`.
- Phase 2 mainline audit: passed, failed checks `[]`.
- Gate676 regression gate: passed, failed checks `[]`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.
- Build environment: Visual Studio BuildTools with CUDA Toolkit 13.2.

## Real 200-Light Validation

- Run: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights`
- Plan: `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json`
- Input lights: 200.
- Active frames: 193.
- Masked frames: 7.
- Mainline route: resident CUDA, resident memory mode, local normalization on, similarity CUDA triangle registration, Lanczos3 warp, winsorized sigma integration.
- Mainline audit total elapsed: `12.292424599989317 s`.
- Component timings:
  - light read/upload/calibrate: `3.6955355999525636 s`
  - resident registration/warp: `0.2948965997202322 s`
  - resident integration: `3.3727147999452427 s`
  - output write: `0.23347520001698285 s`

## Native Profile Evidence

- `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`
- `native_weight_buffer_required=false`
- `native_weight_buffer_device_materialized=false`
- `native_weight_buffer_upload_skipped=true`
- `native_weight_buffer_uploaded_bytes=0`
- `unit_positive_weight_mask_bytes=200`
- `unit_positive_weight_map_from_coverage=true`
- `downloaded_bytes=616512000`

## Gate676 Regression Summary

- Baseline: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll`
- Candidate: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights`
- Determinism differences: 0 output differences, 0 artifact differences, 0 frame-accounting differences, 0 registration differences.
- Elapsed ratio: `1.0394643023337526`.
- Light read/upload/calibrate ratio: `1.1926249339499422`.
- Resident integration ratio: `1.000482336722995`.
- Interpretation: total runtime was slower because surrounding light read/upload/calibrate timing regressed in this run; resident integration stayed effectively flat and the output regression gate passed with zero drift.

## Artifacts

- Run directory: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights`
- Mainline audit: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\gate677_phase2_mainline_audit.json`
- Regression gate: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\gate677_vs_gate676_regression.json`
- Master: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights\integration\resident_master_H.fits`
- Weight map: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights\integration\resident_weight_map_H.fits`
- Coverage map: `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights\integration\resident_coverage_map_H.fits`
- Low/high rejection maps and DQ map: present in the same integration directory.

## Known Limitations

- This gate removes an unused wrapper allocation/upload only; it does not change the hardened reducer algorithm.
- The real 200-light timing improvement is not claimed because surrounding light read/upload/calibrate variance was larger than the removed transfer.
- The next real performance target remains a larger resident reducer redesign or deeper H2D/calibration overlap.
- The current real benchmark still has no positive source-DQ sidecar/inline invalid samples, so nonzero source-DQ stress remains a separate mainline target.

## Next Step

- Continue with a substantive resident execution gate: either redesign the hardened order-statistic reducer beyond the bounded per-thread local array family, or improve native read/H2D/calibration overlap with evidence from the real 200-light benchmark.

## Clean-Room Compliance

- Compliant.
- No external/proprietary implementation source was inspected, summarized, copied, or reworked.
- Validation used GLASS-owned code/tests/artifacts and user-owned 200-light benchmark data only.
- Input image directories were treated as read-only.
