# S2-Gate 668 Status: Default Unit-Positive Mask-Scan Winsorized Integration

## Gate

- Gate: S2-Gate 668
- Status: green checkpoint
- Scope: resident CUDA hardened winsorized integration default execution path
- Branch: `main`

## Completed Work

- Promoted the resident native unit-positive 0/1 weight mask-scan path from an
  environment-only experiment into the default admission policy when
  `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN` is unset.
- The promotion applies only when all finite positive integration weights are
  exactly `1.0`; the current real 200-light default group has `193` active
  positive-weight frames and `7` zero-weight frames.
- Preserved escape hatches and precedence:
  - `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN=0/false/no/off` restores the generic
    `global_reread_weighted_samples` route.
  - explicit true values still enable the same mask-scan route with
    `environment_enabled` provenance.
  - invalid values such as `auto` remain ignored.
  - active-index, local-reuse, and radix-select routes still take precedence.
- Native profiles now record:
  - `unit_positive_weight_mask_policy_source`
  - `unit_positive_weight_mask_default_enabled`
  - existing mask-scan reason/enabled/bytes fields.
- Updated Phase 2, validation, integration model, known limitations, and
  algorithm source ledger documentation.

## Commands Run

- Pre-change current-HEAD default 200-light run:
  `python -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --out C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default`
- Pre-change explicit mask-scan 200-light run:
  `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN=1 python -m glass.cli run ... --out C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\mask_optin`
- Pre-change A/B regression:
  `python -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default --candidate-run C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\mask_optin --out C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\mask_optin_vs_default_regression.json --markdown C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\mask_optin_vs_default_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Native rebuild:
  `cmd.exe /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8"`
- Focused CUDA tests:
  `python -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_default_uses_mask_scan tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_auto_is_not_enabled tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_mask_scan_can_be_disabled tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_matches_cpu tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_local_reuse_matches_cpu`
- Post-change default 200-light run:
  `python -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --out C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted`
- Post-change default versus old default regression:
  `python -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default --candidate-run C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted --out C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted_vs_old_default_regression.json --markdown C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted_vs_old_default_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Post-change default versus explicit mask regression:
  `python -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\mask_optin --candidate-run C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted --out C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted_vs_mask_optin_regression.json --markdown C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted_vs_mask_optin_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Ruff:
  `.\.venv\Scripts\ruff.exe check tests\test_cuda_resident_stack.py`
- Diff check:
  `git diff --check`
- Full test suite:
  `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native rebuild: passed.
- Focused CUDA tests: `6 passed in 0.21s`.
- Ruff: passed.
- `git diff --check`: passed; only Windows line-ending warnings were printed.
- Full pytest: `1409 passed in 62.76s`.

## Real 200-Light Evidence

- Evidence root:
  `C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500`
- Old default run:
  `C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default`
- Explicit mask opt-in run:
  `C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\mask_optin`
- Promoted no-env default run:
  `C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted`

Regression gates:

- Explicit mask versus old default:
  `mask_optin_vs_default_regression.json`, passed, elapsed ratio
  `0.9952617617554094`, failed checks `[]`.
- Promoted default versus old default:
  `default_promoted_vs_old_default_regression.json`, passed, elapsed ratio
  `0.9889873813782383`, failed checks `[]`.
- Promoted default versus explicit mask:
  `default_promoted_vs_mask_optin_regression.json`, passed, elapsed ratio
  `0.9936957485776359`, failed checks `[]`.

Runtime snapshot:

- Old default total elapsed: `11.220837099594064 s`.
- Promoted default total elapsed: `11.097266299999319 s`.
- Speedup versus WBPP black-box `1092.541 s`: `98.45136364800645x`.
- Old default resident integration: `3.3021216000197455 s`.
- Promoted default resident integration: `3.270653699990362 s`.
- Old default native kernel sync: `3.1814066 s`.
- Promoted default native kernel sync: `3.1429195 s`.

Promoted native profile:

- `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`
- `unit_positive_weight_mask_enabled=true`
- `unit_positive_weight_mask_reason=default_unit_positive_weight_mask_scan`
- `unit_positive_weight_mask_policy_source=default_unit_positive_weight_mask_scan`
- `unit_positive_weight_mask_default_enabled=true`
- `unit_positive_weight_mask_bytes=200`
- `unit_positive_weight_frame_count=193`

## CUDA

- CUDA available: yes.
- Native backend: available.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- SM count: `188`.
- Driver: `596.21`.
- Local build used CUDA Toolkit `13.2`.

## Known Limitations

- This is a narrow default admission improvement, not the final scalable
  order-statistic reducer.
- Gate630 remains valid: mask-scan should not be advertised as a major kernel
  speed breakthrough. Gate668 promotes it because it is low-risk, auditable,
  tiny in memory, and did not regress the current 200-light default path.
- Groups with non-unit positive weights keep the generic weighted scan unless
  another explicit/native route applies.
- Resident registration/warp orchestration and I/O/upload/calibration overlap
  remain larger Phase 2 optimization targets.

## Next Step

- Return to a larger mainline target: resident registration/warp batching and
  host/device orchestration reduction, or a redesigned scalable CUDA
  order-statistic reducer with lower per-pixel cost.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned CUDA/C++/Python code, GLASS CPU baseline
tests, GLASS regression gates, and user-owned real benchmark outputs. It did
not inspect, copy, summarize, or rework external proprietary implementation
source, and it did not modify input directories.
