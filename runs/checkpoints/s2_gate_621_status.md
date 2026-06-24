# S2-Gate 621 Status: Guarded Unit-Weight Active-Index Integration Probe

## Gate

S2-Gate 621.

## Completed Work

- Added an opt-in active-frame-index traversal path for native resident
  hardened winsorized integration.
- The path is enabled only when all positive finite weights are exactly `1.0`
  and `GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX=1` is set.
- Default resident hardened integration remains the Gate620 global reread path.
- Native profiles now record:
  - `unit_positive_weights_detected`
  - `unit_positive_weights_fast_path`
  - `unit_positive_active_frame_count`
  - `unit_positive_active_index_env_enabled`
  - `sample_reuse_strategy`
- Added focused CUDA tests for both opt-in and default-off unit-weight behavior.
- Updated Phase 2, integration model, and algorithm-source documentation.

## Commands Run

- Native CUDA rebuild:
  `cmake --build build --config Release --target _glass_cuda_native -j 8`
  through the Visual Studio developer environment.
- Focused CUDA tests:
  `python -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"`
- Focused resident CLI hardened tests:
  `python -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_minimal_output_master_only`
- Ruff:
  `python -m ruff check tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- Default 200-light candidate run:
  `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_default_audit_guarded_20260625_022933 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- Default 200-light regression gate:
  `glass resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate620_quartile_scheduler\real_200_default_audit --candidate-run C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_default_audit_guarded_20260625_022933 --out C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\resident_regression_gate_vs_gate620_default.json --markdown C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\resident_regression_gate_vs_gate620_default.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Opt-in active-index 200-light probe:
  `GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX=1 glass run ... --out C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_active_index_optin_20260625_023010`
- Opt-in active-index regression gate:
  `glass resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_default_audit_guarded_20260625_022933 --candidate-run C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_active_index_optin_20260625_023010 --out C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\resident_regression_gate_optin_vs_default.json --markdown C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\resident_regression_gate_optin_vs_default.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Full test suite:
  `python -m pytest -q`
- Diff check:
  `git diff --check`

## Test Results

- Focused hardened resident-stack tests: `8 passed, 52 deselected`.
- Focused resident CLI hardened tests: `2 passed`.
- Ruff: passed.
- Full pytest: `1307 passed in 53.17s`.
- `git diff --check`: passed; only Git line-ending warnings were printed.

## Real 200-Light Evidence

Default guarded candidate versus Gate620:

- Regression gate:
  `C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\resident_regression_gate_vs_gate620_default.json`
- Status: passed.
- Elapsed ratio: `0.9906823627742244`.
- Active/masked frames: `193 / 7`.
- Determinism drift: none reported by the regression gate.
- Default profile:
  - `resident_integration_s=3.2403203999856487`
  - `hardened_total_s=3.2401886000297964`
  - `kernel_sync_s=3.1234866`
  - `unit_positive_weights_detected=true`
  - `unit_positive_weights_fast_path=false`
  - `sample_reuse_strategy=global_reread_weighted_samples`

Opt-in active-index probe versus default guarded candidate:

- Regression gate:
  `C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\resident_regression_gate_optin_vs_default.json`
- Status: passed.
- Elapsed ratio: `1.0140944010581754`.
- Active-index profile:
  - `resident_integration_s=3.447554200072773`
  - `hardened_total_s=3.4474944999674335`
  - `kernel_sync_s=3.3214407`
  - `unit_positive_weights_fast_path=true`
  - `unit_positive_active_frame_count=193`
  - `sample_reuse_strategy=active_index_global_reread_unit_positive_weights`

Conclusion: active-index traversal is correct and auditable but slower on this
real 200-light benchmark, so it remains opt-in and is not promoted to default.

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Native backend: available
- CUDA Toolkit used by local build: CUDA 13.2

## Known Limitations

- The active-index path did not improve the default 200-light benchmark.
- The native hardened winsorized reducer is still bounded to 512 resident
  frames.
- The main remaining performance opportunities are resident registration/warp
  orchestration and a redesigned order-statistic reducer with lower per-pixel
  cost.
- MSVC still reports an existing signed/unsigned warning in
  `native_bindings.cpp`; this gate did not address it.

## Next Step

Return to the Phase 2 mainline with a substantive gate targeting either:

- resident registration/warp orchestration and host/device round-trip reduction;
  or
- a higher-leverage hardened reducer redesign that reduces median/IQR
  order-statistic cost without increasing local-memory pressure.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned source, GLASS tests, and user-owned
benchmark outputs only. It did not inspect, copy, summarize, or rework external
implementation source.
