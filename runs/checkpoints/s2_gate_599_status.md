# S2 Gate 599 Status: Resident Winsorized Auto Parity Guard

## Gate

- Gate: S2-Gate 599
- Title: Resident Winsorized Auto Parity Guard
- Date: 2026-06-24
- Status: passed

## Completed

- Added `auto` as the default `--resident-winsorized-mode` for `glass run`
  and `glass audit`.
- Added a per-group resident winsorized runtime resolver that records:
  requested mode, effective mode, resolution reason, output-map policy, native
  method availability, default-auto frame limit, and explicit hardened native
  limit.
- Default `auto` now selects `hardened_cpu_parity` only for small resident
  stack groups with diagnostic output maps and at most 64 frames.
- Explicit `hardened_cpu_parity` remains available up to the native 256-frame
  prototype limit.
- Default `auto` falls back to `fast_approx` with a recorded reason for
  200-frame groups, minimal output maps, unsupported dispatch, tile-local apply
  mode, missing hardened methods, or older CUDA builds.
- Updated integration/limitations/algorithm-source/Phase 2 docs.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_rejects_over_limit tests\test_resident_cuda_run.py::test_resident_fast_winsorized_contract_does_not_apply_hardened_limit tests\test_resident_cuda_run.py::test_resident_auto_winsorized_contract_selects_hardened_within_limit tests\test_resident_cuda_run.py::test_resident_auto_winsorized_contract_falls_back_over_default_limit tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py tests\test_pipeline_contract.py tests\test_resident_result_contract.py tests\test_resident_cuda_run.py tests\test_resident_master_stack_engine.py tests\test_cuda_resident_stack.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\rejection.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 12.1214938 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\compare_diagnostics_scaled_coverage190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened\manifest.json --glass-run C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened\warp_quality_contract.json`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\compare_guarded_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 8.4704067 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\compare_guarded_diagnostics_scaled_coverage190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded\manifest.json --glass-run C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\compare_guarded_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\acceptance_guarded_audit.json --markdown C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\acceptance_guarded_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded\warp_quality_contract.json`

## Test Results

- Focused resident winsorized contract/default tests: `4 passed`.
- Resident/CLI/pipeline-contract focused suite: `299 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1272 passed in 52.49 s`.

## Real 200-Light Results

- Root: `C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto`
- Summary: `C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\gate599_summary.json`

### Guarded Default Auto

- Run: `C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_guarded`
- Requested winsorized mode: `auto`.
- Effective winsorized mode: `fast_approx`.
- Resolution reason: `auto_fast_frame_count_exceeds_default_hardened_limit:200>64`.
- Measured elapsed: `8.4704067 s`.
- Acceptance audit: passed.
- Speedup vs WBPP black-box reference: `135.91670629995298x`.
- Compare RMS: `0.005316389020034645`.
- Compare p99 absolute difference: `0.002127066696993994`.
- Coverage>=190 fraction: `0.9067672428396554`.
- Resident integration time: `0.315859799971804 s`.

### Diagnostic 200-Frame Hardened Run

- Run: `C:\glass_runs\phase2_s2_gate599_resident_winsorized_auto\real_200_default_auto_hardened`
- Requested winsorized mode: `auto`.
- Effective winsorized mode during diagnostic run: `hardened_cpu_parity`.
- Resolution reason: `auto_hardened_frame_count_within_limit` from the
  pre-guard implementation.
- Measured elapsed: `12.1214938 s`.
- Acceptance audit: failed.
- Failure reason: post-rejection coverage fraction below benchmark contract.
- Coverage>=190 fraction: `0.8482880808476888`, required `0.9`.
- Compare RMS: `0.00524339222673736`.
- Compare p99 absolute difference: `0.002134429450961769`.
- Resident hardened winsorized native integration time:
  `3.883661299943924 s`.

## CUDA

- CUDA available: yes.
- Native backend: true.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.

## Known Limitations

- The 200-frame hardened diagnostic improved RMS slightly but rejected too many
  samples under the current post-rejection coverage benchmark.
- Default `auto` is therefore intentionally conservative for large groups and
  keeps the 200-light benchmark green via `fast_approx`.
- The next rejection-focused gate should tune hardened coverage semantics or
  add a segmented/coverage-preserving hardened path before raising the default
  auto frame threshold.

## Next Step

- Return to the resident CUDA integration/rejection mainline: make the hardened
  winsorized path preserve benchmark coverage on the real 200-light dataset, or
  add a formal coverage-aware rejection guard that can promote hardened safely.

## Clean-Room Compliance

- This gate only changes GLASS-owned runtime policy, descriptors, tests, and
  documentation over GLASS-owned CPU/CUDA winsorized implementations.
- Real validation consumed user-owned image inputs and user-generated black-box
  reference outputs only.
- No proprietary implementation source was read, copied, summarized, or
  reworked.
- Input image directories remained read-only.
