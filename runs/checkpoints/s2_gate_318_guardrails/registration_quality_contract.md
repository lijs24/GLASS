# Registration Quality Contract

- Status: passed
- Passed: True
- Required: True
- Output count: 3
- Accepted count: 1
- Failed count: 2
- Max RMS px: 0.0
- Min inliers: 5
- Threshold max RMS px: 0.1
- Threshold min inliers: 5
- Require all accepted: False

## Checks

- PASS: registration_results_present - {'path': 'runs\\checkpoints\\s2_gate_316_enabled_run\\registration_results.json', 'required': True}
- PASS: registration_outputs_present - {'output_count': 3}
- PASS: accepted_registration_outputs_present - {'accepted_count': 1, 'required': True}
- PASS: accepted_registration_rms_within_threshold - {'max_observed_rms_px': 0.0, 'max_rms_px': 0.1, 'failed': []}
- PASS: accepted_registration_inliers_meet_threshold - {'min_observed_inliers': 5, 'min_inliers': 5, 'failed': []}

## Outputs

- PASS: F000010 status=reference rms=0.0 inliers=5
- FAIL: F000011 status=quality_rejected rms=None inliers=0
- FAIL: F000012 status=quality_rejected rms=None inliers=0
