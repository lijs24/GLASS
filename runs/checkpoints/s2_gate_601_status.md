# S2-Gate 601 Status: Compact Hardened Count Maps

## Gate

S2-Gate 601: reduce resident hardened winsorized count-map transfer and host
memory pressure without changing rejection math.

## Completed

- Templated the resident hardened winsorized CUDA kernel count-map output type.
- Preserved the original `float32` count-map launch and direct pybind default.
- Added a native `uint16` count-map launch for coverage, low-rejection, and
  high-rejection maps.
- Added Python wrapper argument `count_map_dtype`.
- Switched resident light integration's hardened path to request
  `count_map_dtype="uint16"`.
- Recorded `count_map_dtype_requested` and actual `count_map_dtype` in
  hardened native timing artifacts.
- Added CUDA tests proving compact count maps match the float32 path.

## Commands Run

```powershell
cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && ""%CD%\.venv\Scripts\cmake.exe"" --build build --target _glass_cuda_native --config Release"

.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_matches_cpu_baseline tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_compact_count_maps_match_float_maps tests\test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_honors_rejection_guard tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-winsorized-mode hardened_cpu_parity --integration-rejection-max-fraction 0.015

.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\compare_compact_hardened_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 11.9914137 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\compare_compact_hardened_diagnostics_scaled_coverage190

.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts\manifest.json --glass-run C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\compare_compact_hardened_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\acceptance_compact_hardened_audit.json --markdown C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\acceptance_compact_hardened_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts\warp_quality_contract.json

.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Focused CUDA/resident compact-map tests: `4 passed in 2.01 s`.
- Ruff: `All checks passed!`.
- Full pytest: `1276 passed in 53.00 s`.
- Real 200-light acceptance audit: `passed`, `128` checks, `0` failures.

## Real 200-Light Result

- Run:
  `C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\real_200_hardened_compact_counts`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\compare_compact_hardened_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate601_compact_hardened_counts\acceptance_compact_hardened_audit.json`
- GLASS elapsed, shell measured: `11.9914137 s`.
- GLASS elapsed, run timing: `11.568675100104883 s`.
- Native hardened integration: `3.7782066999934614 s`.
- WBPP black-box reference elapsed: `1092.541 s`.
- Speedup vs WBPP black-box: `94.43959576581892x`.
- RMS difference vs reference: `0.0055611675566298235`.
- abs diff p99 vs reference: `0.002161672392394391`.
- Benchmark coverage check: `1.0` fraction at the configured coverage
  threshold.
- Applied guard: `rejection_min_samples=3`,
  `rejection_max_fraction=0.015`.
- Hardened count-map timing:
  - requested dtype: `uint16`;
  - actual dtype: `uint16`.

## Gate600 vs Gate601

| Metric | Gate600 | Gate601 |
| --- | ---: | ---: |
| Shell elapsed | `12.1345343 s` | `11.9914137 s` |
| Run timing | `11.703999100020155 s` | `11.568675100104883 s` |
| Native hardened integration | `3.844128599972464 s` | `3.7782066999934614 s` |
| Count-map dtype | `float32` | `uint16` |
| Speedup vs WBPP black-box | `93.34766609800222x` | `94.43959576581892x` |

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total memory visible to GLASS: `97886 MiB`.
- Native backend: available.

## Known Limits

- The performance gain is intentionally modest because hardened integration is
  still dominated by per-pixel median/IQR work and audit-map/report plumbing.
- The compact map path applies to resident light integration hardened
  winsorized mode; the calibration master-cache hardened helper still uses the
  compatibility float32 count-map return.
- Count maps are compact only while frame counts fit in `uint16`, which is
  well above the current native hardened prototype limit of `256` frames.

## Next Step

Continue with substantive resident CUDA work:

- let native DQ/count-map consumers accept compact count maps directly; or
- reduce per-pixel hardened median/IQR cost through a better resident kernel;
  or
- return to resident registration/warp orchestration if the default fast path
  is prioritized over hardened rejection promotion.

## Clean-Room Compliance

This gate changes GLASS-owned CUDA output-map dtype plumbing, wrappers, tests,
and documentation. No official PixInsight WBPP/PJSR source code was read,
copied, summarized, or reworked. User image directories were treated as
read-only.
