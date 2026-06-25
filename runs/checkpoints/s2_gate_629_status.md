# S2-Gate 629 Status: Unit-Positive Weight Mask-Scan Reducer Probe

## Gate

S2-Gate 629 continues the Phase 2 resident CUDA integration mainline.

## Completed

- Added an opt-in CUDA resident hardened winsorized path controlled by
  `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN=1`.
- The native wrapper detects the 0/1 positive-weight case, uploads a
  one-byte-per-frame mask, and dispatches a kernel variant that keeps
  frame-axis scan order while skipping zero-weight frames without reloading
  float weights for every pixel pass.
- Added native profile fields:
  - `unit_positive_weight_mask_requested`
  - `unit_positive_weight_mask_enabled`
  - `unit_positive_weight_mask_reason`
  - `unit_positive_weight_mask_bytes`
  - `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`
- Added a focused CUDA/CPU parity test covering zero-weight frames and a NaN
  pixel.
- Updated integration model, Phase 2 plan, algorithm source ledger, and known
  limitations.

## Code Changes

- `cpp/cuda/integration_kernels.cu`
- `cpp/src/native_bindings.cpp`
- `tests/test_cuda_resident_stack.py`
- `docs/integration_model.md`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `docs/known_limitations.md`

## Commands Run

```powershell
cmd.exe /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8"
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_default_off tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_local_reuse_matches_cpu
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate629_unit_mask_scan\real_200_mask_scan_20260625_134256 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate628_real200_default_ab\real_200_default_gate628_20260625_133115 --candidate-run C:\glass_runs\phase2_s2_gate629_unit_mask_scan\real_200_mask_scan_20260625_134256 --out C:\glass_runs\phase2_s2_gate629_unit_mask_scan\resident_regression_gate_gate629_mask_vs_gate628_default.json --markdown C:\glass_runs\phase2_s2_gate629_unit_mask_scan\resident_regression_gate_gate629_mask_vs_gate628_default.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate629_unit_mask_scan\real_200_mask_scan_20260625_134256\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate629_unit_mask_scan\gate629_resident_mask_vs_wbpp_compare.json --glass-time-seconds 10.765879800193943 --reference-time-seconds 1092.541 --glass-label GLASS_Gate629_mask_scan --reference-label WBPP_blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --diagnostics-dir C:\glass_runs\phase2_s2_gate629_unit_mask_scan\compare_diagnostics --diagnostic-max-size 1024 --hotspot-tile-size 512 --glass-coverage-map C:\glass_runs\phase2_s2_gate629_unit_mask_scan\real_200_mask_scan_20260625_134256\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate629_unit_mask_scan\real_200_mask_scan_20260625_134256 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate629_unit_mask_scan\gate629_resident_mask_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate629_unit_mask_scan\gate629_wbpp_speedup_summary.json --markdown C:\glass_runs\phase2_s2_gate629_unit_mask_scan\gate629_wbpp_speedup_summary.md --min-speedup 2
git diff --check
.\.venv\Scripts\ruff.exe check cpp src tests docs --select E,F --ignore E501
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native build: passed.
- Focused CUDA/CPU resident winsorized tests: `4 passed`.
- Ruff: `All checks passed!`
- Full pytest: `1323 passed in 57.78s`.

## Real 200-Light Validation

- Candidate run:
  `C:\glass_runs\phase2_s2_gate629_unit_mask_scan\real_200_mask_scan_20260625_134256`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate628_real200_default_ab\real_200_default_gate628_20260625_133115`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate629_unit_mask_scan\resident_regression_gate_gate629_mask_vs_gate628_default.json`
- Regression status: passed.
- Failed checks: none.
- Candidate/baseline elapsed ratio: `0.9455421703511155`.
- Baseline total elapsed: `11.385932999895886 s`.
- Candidate total elapsed: `10.765879800193943 s`.
- Active/masked frame count: `193 / 7`.
- Determinism: zero artifact differences, zero frame accounting differences,
  zero output differences, zero numerical drift.

Native profile from the candidate run:

- `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`
- `unit_positive_weight_mask_enabled=true`
- `unit_positive_weight_mask_bytes=200`
- `unit_positive_weight_frame_count=193`
- `kernel_sync_s=3.2001566`

Substage timing against Gate628:

- `resident_integration`: `3.386920899967663 s` -> `3.3294103000080213 s`
- `light_read_upload_calibrate`: `3.5380190999712795 s` -> `3.2672325000166893 s`
- `light_h2d_calibrate_store`: `2.9002926999237397 s` -> `2.619260400068015 s`
- `resident_registration_warp`: `0.300620699650608 s` -> `0.2655095000518486 s`

## WBPP Black-Box Comparison

- Speedup summary:
  `C:\glass_runs\phase2_s2_gate629_unit_mask_scan\gate629_wbpp_speedup_summary.json`
- Compare report:
  `C:\glass_runs\phase2_s2_gate629_unit_mask_scan\gate629_resident_mask_vs_wbpp_compare.html`
- GLASS elapsed: `10.765879800193943 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup vs WBPP: `101.48181293834604x`.
- Shape match: true.
- Compared pixels at coverage >= 190: `60105814`.
- Coverage fraction: `0.9749333995120938`.
- RMS difference: `0.0056241382952344435`.
- P99 absolute difference: `0.002143551869085057`.

## CUDA Availability

- CUDA available to GLASS: yes.
- Native backend: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- SM count: `188`.

## Known Limits

- The mask-scan path remains opt-in. It preserved output and improved one real
  run, but the integration-only gain was modest and should be repeat-tested
  before default promotion.
- It applies only to the unit-positive 0/1 weight case. Non-unit weighting
  keeps the generic weighted scan.
- It does not address the larger resident registration/warp orchestration and
  read/upload/calibration pipeline costs.

## Next Step

Run a repeated real 200-light matrix for default versus mask-scan to determine
whether `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN=1` should be promoted, or move to the
larger current bottleneck: resident registration/warp orchestration and
host/device coordination.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA kernels, GLASS deterministic CPU
baseline tests, GLASS-generated artifacts, and user-owned black-box timing and
reference outputs. It does not inspect external implementation source, modify
input directories, or copy external algorithms.
