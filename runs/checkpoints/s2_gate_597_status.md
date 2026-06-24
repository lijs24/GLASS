# S2 Gate 597 Status: Async Resident Master-Cache Persistence

## Gate

- Gate: S2-Gate 597
- Title: Async Resident Master-Cache Persistence
- Date: 2026-06-24
- Status: passed

## Completed

- Added a single-writer resident master-cache persistence queue.
- The resident CUDA matching-master path now returns freshly built master
  arrays immediately and writes cache `.npy` files in the background.
- Cache correctness is preserved by writing the stats JSON after required
  master arrays are present; `resident_master_cache.json` is validated only
  after the background writer is joined.
- Added resident artifact/profile fields for async cache-write wait, total
  write time, hidden write time, and written bytes.
- Added unit coverage for async cache persistence and profile reporting.
- Ran the real M38 H-alpha 200-light cold-cache benchmark and passed the
  LN-on default acceptance contract.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py`
- `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_cache.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_shared_master_cache_reuses_across_runs tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_master_cache_reuses_output_parent_cache tests\test_resident_cuda_run.py::test_cli_resident_cuda_master_cache_policy_run_keeps_run_local_cache`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_light_pipeline_profile.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py tests\test_resident_light_pipeline_profile.py tests\test_resident_master_cache.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py tests\test_resident_master_stack_engine.py tests\test_resident_light_pipeline_profile.py`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate597_async_master_cache\compare_vs_wbpp_fastintegration_scaled_coverage190_final.html --glass-time-seconds 16.86062809964642 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\compare_diagnostics_scaled_coverage190_final`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final\manifest.json --glass-run C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate597_async_master_cache\compare_vs_wbpp_fastintegration_scaled_coverage190_final.json --out C:\glass_runs\phase2_s2_gate597_async_master_cache\acceptance_audit_final.json --markdown C:\glass_runs\phase2_s2_gate597_async_master_cache\acceptance_audit_final.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final\warp_quality_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused resident master/profile/cache tests: `11 passed`.
- Resident CUDA shared/auto/run master-cache CLI tests: `6 passed`.
- Ruff on changed files: `All checks passed`.
- Full pytest: `1268 passed in 52.23 s`.

## Real 200-Light Results

- Root: `C:\glass_runs\phase2_s2_gate597_async_master_cache`
- Run: `C:\glass_runs\phase2_s2_gate597_async_master_cache\cold_default_async_master_cache_final`
- Summary: `C:\glass_runs\phase2_s2_gate597_async_master_cache\gate597_summary.json`
- Total elapsed: `16.86062809964642 s`.
- Resident calibration/integration stage: `16.02315390005242 s`.
- WBPP black-box reference time: `1092.541 s`.
- Speedup vs reference: `64.79835706849565x`.
- Improvement vs Gate596 total elapsed: `2.4127444004407153 s`
  (`12.518537689394044%`).
- Compare RMS: `0.005316389020034645`.
- Compare p99 absolute difference: `0.002127066696993994`.
- Coverage>=190 fraction with benchmark `128 px` border ignore:
  `0.9067672428396554`.
- Acceptance audit: passed.

## Async Cache-Write Profile

- Cache hit/miss: `0 / 1`.
- Required cache bytes: `739890155`.
- Background write elapsed: `3.6264531000051647 s`.
- Wait before `resident_master_cache.json`: `0.000014399993233382702 s`.
- Hidden write time: `3.6264387000119314 s`.
- Master build/load bucket: `9.484477099962533 s`.
- Light read/upload/calibrate bucket: `11.7089263999369 s`.

## CUDA

- CUDA available: yes.
- Native backend: true.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Multiprocessors: `188`.
- Driver version: `596.21`.

## Known Limitations

- The async writer overlaps cache persistence but does not remove master-cache
  computation/read cost; `master_build_or_load` remains the dominant cold-cache
  bucket.
- Cache stats JSON is still the completion marker. A process crash before
  stats write leaves arrays that will be ignored/rebuilt on the next run.
- The resident CUDA hardened winsorized master kernel remains limited to
  compatible one-iteration `winsorized_sigma` policies and calibration groups
  within the current native frame-count limits.
- Multiple light groups that independently need the same not-yet-persisted
  cache key in the same process may still rebuild that cache; the real
  200-light H-alpha benchmark uses one matching master set.

## Next Step

- Return to Phase 2 substantive runtime/science work: resident
  registration/warp batching, LN/integration default completeness, and
  numerical consistency guardrails. Avoid more release/default-promotion or
  report-only gates unless they directly block those targets.

## Clean-Room Compliance

- This gate uses GLASS-owned Python scheduling/provenance code and existing
  GLASS-owned CUDA kernels.
- Real validation consumed user-owned image inputs and user-generated
  black-box reference outputs only.
- No proprietary implementation source was read, copied, summarized, or
  reworked.
- Input image directories remained read-only.
