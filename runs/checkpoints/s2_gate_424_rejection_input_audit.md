# Resident Rejection Input Audit

- Status: `passed`
- Passed: `True`
- Recommendation: `target_resident_registration_warp_input_parity`
- Frame count: `16`
- Evaluation region: `compare_region`

## Exact Input

- CUDA exact-input status: `completed`
- CUDA exact-input passed: `True`
- CPU replay passed: `True`

## Resident Output Delta

- Coverage abs delta: `760.0`
- Low rejection abs delta: `381.0`
- High rejection abs delta: `379.0`
- Resident output parity passed: `False`
- Attribution status: `resident_registration_warp_input_delta`

## Rejection Sample Audit

- Status: `attention_required`
- Recommendation: `rejection_sample_accounting_ready`
- Evaluation deltas: `{'coverage_sample_delta': 16, 'abs_coverage_sample_delta': 760, 'coverage_mismatch_pixels': 747, 'low_rejected_sample_delta': 1, 'abs_low_rejected_sample_delta': 381, 'low_rejection_mismatch_pixels': 378, 'high_rejected_sample_delta': -17, 'abs_high_rejected_sample_delta': 379, 'high_rejection_mismatch_pixels': 379, 'rejected_sample_delta': -16, 'abs_rejected_sample_delta': 760, 'rejection_mismatch_pixels': 747, 'pre_rejection_sample_delta': 0, 'abs_pre_rejection_sample_delta': 0, 'pre_rejection_mismatch_pixels': 0, 'same_pre_rejection_abs_rejected_sample_delta': 760, 'same_pre_rejection_rejection_mismatch_pixels': 747, 'same_post_coverage_abs_rejected_sample_delta': 0, 'same_post_coverage_rejection_mismatch_pixels': 0, 'rejection_mismatch_with_pre_rejection_mismatch_pixels': 0, 'rejection_mismatch_with_coverage_mismatch_pixels': 747, 'resident_warp_edge_rejection_mismatch_pixels': 0, 'cpu_warp_edge_rejection_mismatch_pixels': 0, 'dq_mismatch_pixels': 708}`

## Checks

- PASS: `cpu_registered_replay_matches_cpu_outputs`
- PASS: `cuda_exact_input_matches_cpu_outputs`
- PASS: `resident_rejection_delta_attributed`
