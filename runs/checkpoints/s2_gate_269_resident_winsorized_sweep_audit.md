# Resident Winsorized Sweep Audit

- Status: `passed`
- Passed: `True`
- Contract: `s2_gate_269_default_resident_winsorized_sweep`
- Sweep: `runs\checkpoints\s2_gate_268_resident_winsorized_sweep.json`
- Frame counts: `[8, 32, 128, 200]`
- Required frame count: `200`
- Required frame RMS: `2.3066304440398834e-05`
- Required frame max abs: `6.103515625e-05`
- Required frame CPU s: `0.01229839999723481`
- Required frame hardened CUDA s: `0.0012743999977828935`
- Max hardened master RMS: `2.3066304440398834e-05`

## Checks

| check | passed | note |
| --- | ---: | --- |
| artifact_type_matches | `True` |  |
| sweep_passed | `True` |  |
| config_frame_counts_matches_contract | `True` |  |
| config_height_matches_contract | `True` |  |
| config_high_sigma_matches_contract | `True` |  |
| config_low_sigma_matches_contract | `True` |  |
| config_required_frame_count_matches_contract | `True` |  |
| config_seed_base_matches_contract | `True` |  |
| config_tolerance_max_abs_matches_contract | `True` |  |
| config_tolerance_rms_matches_contract | `True` |  |
| config_width_matches_contract | `True` |  |
| run_frame_counts_match_contract | `True` |  |
| all_runs_passed | `True` |  |
| required_frame_count_present | `True` |  |
| required_frame_count_passed | `True` |  |
| frame_200_hardened_master_rms_within_contract | `True` |  |
| frame_200_hardened_master_max_abs_within_contract | `True` |  |
| frame_200_hardened_weight_max_abs_within_contract | `True` |  |
| frame_200_hardened_coverage_max_abs_within_contract | `True` |  |
| frame_200_hardened_low_rejection_max_abs_within_contract | `True` |  |
| frame_200_hardened_high_rejection_max_abs_within_contract | `True` |  |
| max_hardened_master_rms_within_contract | `True` |  |
| frame_200_timing_cpu_baseline_present | `True` |  |
| frame_200_timing_cuda_fast_approx_present | `True` |  |
| frame_200_timing_cuda_hardened_present | `True` |  |
| required_frame_hardened_timing_mode_matches_contract | `True` |  |
| required_frame_hardened_native_method_matches_contract | `True` |  |

## Failed Checks

- none
