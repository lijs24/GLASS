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

- Coverage abs delta: `706.0`
- Low rejection abs delta: `356.0`
- High rejection abs delta: `350.0`
- Resident output parity passed: `False`
- Attribution status: `resident_registration_warp_input_delta`

## Rejection Sample Audit

- Status: `attention_required`
- Recommendation: `target_resident_registration_warp_input_parity`
- Raw sample recommendation: `fix_resident_winsorized_rejection_semantics`
- Evaluation deltas: `{'coverage_sample_delta': 28, 'abs_coverage_sample_delta': 706, 'coverage_mismatch_pixels': 694, 'low_rejected_sample_delta': 4, 'abs_low_rejected_sample_delta': 356, 'low_rejection_mismatch_pixels': 353, 'high_rejected_sample_delta': -32, 'abs_high_rejected_sample_delta': 350, 'high_rejection_mismatch_pixels': 350, 'rejected_sample_delta': -28, 'abs_rejected_sample_delta': 706, 'rejection_mismatch_pixels': 694, 'pre_rejection_sample_delta': 0, 'abs_pre_rejection_sample_delta': 0, 'pre_rejection_mismatch_pixels': 0, 'same_pre_rejection_abs_rejected_sample_delta': 706, 'same_pre_rejection_rejection_mismatch_pixels': 694, 'same_post_coverage_abs_rejected_sample_delta': 0, 'same_post_coverage_rejection_mismatch_pixels': 0, 'rejection_mismatch_with_pre_rejection_mismatch_pixels': 0, 'rejection_mismatch_with_coverage_mismatch_pixels': 694, 'resident_warp_edge_rejection_mismatch_pixels': 0, 'cpu_warp_edge_rejection_mismatch_pixels': 0, 'dq_mismatch_pixels': 659}`

## Checks

- PASS: `cpu_registered_replay_matches_cpu_outputs`
- PASS: `cuda_exact_input_matches_cpu_outputs`
- PASS: `resident_rejection_delta_attributed`
