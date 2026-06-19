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

- Coverage abs delta: `798.0`
- Low rejection abs delta: `402.0`
- High rejection abs delta: `396.0`
- Resident output parity passed: `False`
- Attribution status: `resident_registration_warp_input_delta`

## Rejection Sample Audit

- Status: `attention_required`
- Recommendation: `target_resident_registration_warp_input_parity`
- Raw sample recommendation: `fix_resident_winsorized_rejection_semantics`
- Evaluation deltas: `{'coverage_sample_delta': 38, 'abs_coverage_sample_delta': 798, 'coverage_mismatch_pixels': 786, 'low_rejected_sample_delta': -16, 'abs_low_rejected_sample_delta': 402, 'low_rejection_mismatch_pixels': 400, 'high_rejected_sample_delta': -22, 'abs_high_rejected_sample_delta': 396, 'high_rejection_mismatch_pixels': 396, 'rejected_sample_delta': -38, 'abs_rejected_sample_delta': 798, 'rejection_mismatch_pixels': 786, 'pre_rejection_sample_delta': 0, 'abs_pre_rejection_sample_delta': 0, 'pre_rejection_mismatch_pixels': 0, 'same_pre_rejection_abs_rejected_sample_delta': 798, 'same_pre_rejection_rejection_mismatch_pixels': 786, 'same_post_coverage_abs_rejected_sample_delta': 0, 'same_post_coverage_rejection_mismatch_pixels': 0, 'rejection_mismatch_with_pre_rejection_mismatch_pixels': 0, 'rejection_mismatch_with_coverage_mismatch_pixels': 786, 'resident_warp_edge_rejection_mismatch_pixels': 0, 'cpu_warp_edge_rejection_mismatch_pixels': 0, 'dq_mismatch_pixels': 741}`

## Checks

- PASS: `cpu_registered_replay_matches_cpu_outputs`
- PASS: `cuda_exact_input_matches_cpu_outputs`
- PASS: `resident_rejection_delta_attributed`
