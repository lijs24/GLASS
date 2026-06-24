# S2-Gate 602 Status: Native DQ Compact Count-Map Consumption

## Gate

S2-Gate 602: keep resident compact count maps compact through native DQ
generation and make the dtype contract auditable.

## Completed

- Added a native `HostCount2D` view for DQ/count-map inputs.
- `resident_dq_map_count_maps_i16` now accepts `float32`, `int16`, and
  `uint16` C-contiguous count maps without force-casting compact maps to
  float32.
- The Python `glass_cuda.resident_dq_map_count_maps_i16` wrapper now preserves
  count-map dtypes while still converting the master image to float32.
- Resident outputs and artifacts now record `dq_map_count_input_dtypes`.
- Added native compact DQ tests proving `uint16` count maps match the Python DQ
  baseline.

## Commands Run

```powershell
cmd /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat"" -arch=x64 -host_arch=x64 && ""%CD%\.venv\Scripts\cmake.exe"" --build build --target _glass_cuda_native --config Release"

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_dq_map_count_maps_native_matches_fast_python_when_available tests\test_resident_cuda_run.py::test_resident_dq_map_count_maps_native_accepts_compact_uint16_maps tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-winsorized-mode hardened_cpu_parity --integration-rejection-max-fraction 0.015

.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\compare_native_dq_compact_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 11.9861992 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\compare_native_dq_compact_diagnostics_scaled_coverage190

.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final\manifest.json --glass-run C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\compare_native_dq_compact_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\acceptance_native_dq_compact_audit.json --markdown C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\acceptance_native_dq_compact_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final\warp_quality_contract.json
```

## Test Result

- Focused native DQ compact tests: `3 passed in 0.94 s`.
- Ruff: `All checks passed!`.
- Full pytest: `1277 passed in 52.15 s`.
- Real 200-light acceptance audit: `passed`, `128` checks, `0` failures.

## Real 200-Light Result

- Run:
  `C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\real_200_hardened_native_dq_compact_final`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\compare_native_dq_compact_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate602_native_dq_compact_counts\acceptance_native_dq_compact_audit.json`
- GLASS elapsed, shell measured: `11.9861992 s`.
- GLASS elapsed, run timing: `11.474401000072248 s`.
- Native hardened integration: `3.7188648000592366 s`.
- WBPP black-box reference elapsed: `1092.541 s`.
- Speedup vs WBPP black-box: `95.21551495307867x`.
- RMS difference vs reference: `0.0055611675566298235`.
- abs diff p99 vs reference: `0.002161672392394391`.
- Benchmark coverage check: `1.0` fraction at the configured coverage
  threshold.
- DQ native path:
  - backend: `native_host_fast_count_maps`;
  - method: `resident_dq_map_count_maps_i16`;
  - thread count: `16`;
  - input dtypes:
    `coverage=uint16`, `low_rejection=uint16`,
    `high_rejection=uint16`, `geometric_warp_coverage=float32`.

## Gate601 vs Gate602

| Metric | Gate601 | Gate602 |
| --- | ---: | ---: |
| Shell elapsed | `11.9914137 s` | `11.9861992 s` |
| Run timing | `11.568675100104883 s` | `11.474401000072248 s` |
| Native hardened integration | `3.7782066999934614 s` | `3.7188648000592366 s` |
| DQ count-map input dtypes | not recorded | `uint16/uint16/uint16/float32` |
| Speedup vs WBPP black-box | `94.43959576581892x` | `95.21551495307867x` |

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total memory visible to GLASS: `97886 MiB`.
- Native backend: available.

## Known Limits

- This gate improves DQ/mask dtype plumbing and auditability; it is not a large
  compute-kernel redesign.
- Geometric warp coverage remains float32 because it is produced by the warp
  coverage surface, not the hardened count-map kernel.
- The next larger runtime gains should come from resident hardened median/IQR
  kernel work or registration/warp orchestration.

## Next Step

Return to a larger compute lever:

- optimize resident hardened median/IQR kernel cost; or
- reduce resident registration/warp orchestration; or
- strengthen default-path quality/reference selection so the resident default
  path can be run safely without explicit reference metadata.

## Clean-Room Compliance

This gate changes GLASS-owned native DQ/count-map ingestion, wrappers, tests,
artifacts, and documentation. No official PixInsight WBPP/PJSR source code was
read, copied, summarized, or reworked. User image directories were treated as
read-only.
