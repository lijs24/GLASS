# S2 Gate 596 Status: Resident CUDA Hardened Winsorized Master Cache

## Gate

- Gate: S2-Gate 596
- Title: Resident CUDA Hardened Winsorized Master Cache
- Date: 2026-06-24
- Status: passed

## Completed

- Added a resident CUDA hardened winsorized master-cache dispatch for compatible
  `CalibrationPolicy.master_rejection=winsorized_sigma` calibration groups.
- Preserved CPUStackEngine fallback for unsupported rejection modes,
  multi-iteration policies, frame counts above `256`, unavailable CUDA/native
  methods, unsupported FITS layouts, and min-samples/max-reject-fraction policy
  guard triggers.
- Added StackEngine-compatible metrics and DQ provenance for the CUDA hardened
  master path, including native timing, raw-u16 upload bytes, result-contract
  status, and policy-guard pixel counts.
- Added tests for resident master-cache CUDA hardened dispatch and kept the
  existing CUDA hardened winsorized parity test green.
- Ran the real M38 H-alpha 200-light cold-cache benchmark with a fresh master
  cache and passed the LN-on default acceptance contract.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k hardened_winsorized_sigma`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_master_stack_engine.py`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\resident_master_cache_cuda_hardened`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 19.273372500087135 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\compare_diagnostics_scaled_coverage190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized\manifest.json --glass-run C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized\warp_quality_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused resident master-cache tests: `4 passed`.
- CUDA hardened winsorized parity focused test: `1 passed, 50 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1267 passed in 52.80s`.

## Real 200-Light Results

- Root: `C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized`
- Run: `C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\cold_default_cuda_hardened_winsorized`
- Summary: `C:\glass_runs\phase2_s2_gate596_cuda_master_winsorized\gate596_summary.json`
- Total elapsed: `19.273372500087135 s`.
- Resident calibration/integration stage: `18.418523599975742 s`.
- WBPP black-box reference time: `1092.541 s`.
- Speedup vs reference: `56.68655031676789x`.
- Compare RMS: `0.005316389020034645`.
- Compare p99 absolute difference: `0.002127066696993994`.
- Coverage>=190 fraction with benchmark `128 px` border ignore:
  `0.9067672428396554`.
- Acceptance audit: passed.

## Master Cache Dispatch

- Cache hit/miss: `0 / 1`.
- Top-level tile stack mode: `stack_engine_cuda_hardened_winsorized`.
- Master rejection requested/applied: `winsorized_sigma / winsorized_sigma`.
- Fallback reason: none.
- Bias dispatch: `resident_cuda_raw_u16_hardened_winsorized`,
  total `0.8078936000820249 s`, integrate `0.21162339998409152 s`,
  policy guard pixels `0`, result contract passed.
- Dark dispatch: `resident_cuda_raw_u16_hardened_winsorized`,
  total `1.1256047999486327 s`, integrate `0.18808859994169325 s`,
  policy guard pixels `0`, result contract passed.
- Flat dispatch: `resident_cuda_raw_u16_hardened_winsorized`,
  total `0.5301240999251604 s`, integrate `0.18525479990057647 s`,
  policy guard pixels `0`, result contract passed.

## CUDA

- CUDA available: yes.
- Native backend: true.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Multiprocessors: `188`.

## Known Limitations

- The hardened native winsorized master kernel is limited to `256` frames per
  calibration group.
- The CUDA master-cache fast path currently supports one-iteration
  `winsorized_sigma`; non-winsorized robust policies and multi-iteration
  policies fall back to CPUStackEngine.
- Policy-guard fallback is whole-master, not per-pixel repair. If a future
  dataset triggers the guard, correctness is preserved but cold-cache runtime
  may regress until segmented/batched robust CUDA reduction is implemented.

## Next Step

- Continue the Phase 2 mainline on resident default completeness and runtime:
  reduce per-frame Python orchestration in registration/warp/LN/integration,
  and broaden robust CUDA master reductions beyond the current 256-frame
  one-iteration winsorized path.

## Clean-Room Compliance

- This gate uses GLASS-owned CUDA kernels and GLASS-owned dispatch/provenance
  code.
- Real validation consumed user-owned image inputs and user-generated
  black-box reference outputs only.
- No proprietary or external implementation source was read, copied,
  summarized, or reworked.
- Input image directories remained read-only.
