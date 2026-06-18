# Resident Winsorized Benchmark Audit

- Status: `passed`
- Passed: `True`
- Contract: `s2_gate_266_default_resident_winsorized_microbenchmark`
- Benchmark: `runs\checkpoints\s2_gate_265_resident_winsorized_benchmark.json`
- Frames: `8`
- Shape: `[16, 16]`
- Hardened master RMS: `5.781343294611998e-06`
- Hardened master max abs: `1.52587890625e-05`
- Fast approximation master RMS: `0.566935986706338`

## Checks

| check | passed | note |
| --- | ---: | --- |
| artifact_type_matches | `True` |  |
| benchmark_passed | `True` |  |
| cuda_available | `True` |  |
| config_frame_count_matches_contract | `True` |  |
| config_height_matches_contract | `True` |  |
| config_high_sigma_matches_contract | `True` |  |
| config_low_sigma_matches_contract | `True` |  |
| config_seed_matches_contract | `True` |  |
| config_width_matches_contract | `True` |  |
| hardened_master_rms_within_contract | `True` |  |
| hardened_master_max_abs_within_contract | `True` |  |
| hardened_weight_max_abs_within_contract | `True` |  |
| hardened_coverage_max_abs_within_contract | `True` |  |
| hardened_low_rejection_max_abs_within_contract | `True` |  |
| hardened_high_rejection_max_abs_within_contract | `True` |  |
| timing_cpu_baseline_present | `True` |  |
| timing_cuda_fast_approx_present | `True` |  |
| timing_cuda_hardened_present | `True` |  |
| hardened_timing_mode_matches_contract | `True` |  |
| hardened_native_method_matches_contract | `True` |  |
| fast_approx_context_present | `True` | Fast approximation is context only and is not required to match CPU parity. |

## Failed Checks

- none
