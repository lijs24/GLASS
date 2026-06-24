# S2 Gate 598 Status: Resident LN Frame Accounting Closure

## Gate

- Gate: S2-Gate 598
- Title: Resident LN Frame Accounting Closure
- Date: 2026-06-24
- Status: passed

## Completed

- Fixed `frame_accounting.json` to read resident local-normalization
  per-frame rows from `groups[].frame_results`.
- Preserved legacy top-level `local_norm_results[]` support.
- Corrected resident zero-weight frame audit status from fallback
  `resident_applied` to the actual resident LN row status
  `skipped_zero_weight`.
- Added a regression test for grouped resident LN frame rows.
- Ran a real 200-light cache-hit resident CUDA validation and passed
  compare/acceptance.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_accounting.py tests\test_local_norm_contract.py`
- `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\frame_accounting.py tests\test_frame_accounting.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py::test_pipeline_contract_accepts_resident_local_norm_group_rows tests\test_resident_cuda_run.py -k "local_norm_contract or grid_local_norm" tests\test_cli_smoke.py -k "local_norm_contract or resident_local_normalization"`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 8.033185199834406 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\compare_diagnostics_scaled_coverage190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status\manifest.json --glass-run C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status\warp_quality_contract.json`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\frame_accounting.py tests\test_frame_accounting.py`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused frame-accounting/local-norm tests: `15 passed`.
- Resident local-norm/pipeline focused tests: `5 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1269 passed in 52.55 s`.

## Real 200-Light Results

- Root: `C:\glass_runs\phase2_s2_gate598_ln_frame_accounting`
- Run: `C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\real_200_cache_hit_ln_status`
- Summary: `C:\glass_runs\phase2_s2_gate598_ln_frame_accounting\gate598_summary.json`
- Total elapsed: `8.033185199834406 s`.
- Resident calibration/integration stage: `7.188936799997464 s`.
- Shared resident master cache: hit `1`, miss `0`.
- WBPP black-box reference time: `1092.541 s`.
- Speedup vs reference: `136.00346224092047x`.
- Compare RMS: `0.005316389020034645`.
- Compare p99 absolute difference: `0.002127066696993994`.
- Coverage>=190 fraction with benchmark `128 px` border ignore:
  `0.9067672428396554`.
- Acceptance audit: passed.

## Frame Accounting Evidence

- Exception frame count: `7`.
- Exception final status counts: `quality_rejected: 7`.
- Exception local-normalization status counts: `skipped_zero_weight: 7`.
- Sample frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`,
  `F000217`, `F000218`.

## CUDA

- CUDA available: yes.
- Native backend: true.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.

## Known Limitations

- This gate fixes audit/accounting state, not image math or runtime kernels.
- The real validation reused a shared resident master cache to isolate the
  frame-accounting change; cold-cache performance remains represented by
  Gate597.
- The local-normalization contract already checks resident frame-count closure;
  this gate makes frame accounting consume the same resident per-frame rows.

## Next Step

- Continue substantive Phase 2 work on resident registration/warp/LN/integration
  behavior: either improve actual resident LN/integration GPU execution or add
  a stronger numerical consistency guard that blocks real output regressions.

## Clean-Room Compliance

- This gate only changes GLASS-owned artifact/accounting code and tests.
- Real validation consumed user-owned image inputs and user-generated
  black-box reference outputs only.
- No proprietary implementation source was read, copied, summarized, or
  reworked.
- Input image directories remained read-only.
