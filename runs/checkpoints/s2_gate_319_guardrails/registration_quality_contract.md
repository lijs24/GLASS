# Registration Quality Contract

- Status: passed
- Passed: True
- Required: False
- Output count: 3
- Accepted count: 1
- Failed count: 2
- Max RMS px: 0.0
- Min inliers: 5
- Threshold max RMS px: None
- Threshold min inliers: None
- Require all accepted: False

## Checks

- PASS: registration_results_present - {'path': 'runs\\checkpoints\\s2_gate_316_enabled_run\\registration_results.json', 'required': False}
- PASS: registration_outputs_present - {'output_count': 3}
- PASS: accepted_registration_outputs_present - {'accepted_count': 1, 'required': False}

## Outputs

- PASS: F000010 status=reference rms=0.0 inliers=5
- FAIL: F000011 status=quality_rejected rms=None inliers=0
- FAIL: F000012 status=quality_rejected rms=None inliers=0
