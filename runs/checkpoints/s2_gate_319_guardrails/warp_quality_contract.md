# Warp Quality Contract

- Status: passed
- Passed: True
- Required: True
- Output count: 1
- Skipped count: 2
- Artifact-ready count: 1
- Min valid fraction: 1.0
- Threshold min valid fraction: 1.0
- Max skipped frames: 2
- Require artifacts: True
- Require all registered: True

## Checks

- PASS: warp_results_present - {'path': 'runs\\checkpoints\\s2_gate_316_enabled_run\\warp_results.json', 'required': True}
- PASS: warp_outputs_present - {'output_count': 1}
- PASS: skipped_warp_rows_have_reasons - {'failed': []}
- PASS: warp_output_artifacts_ready - {'failed': []}
- PASS: warp_valid_fraction_meets_threshold - {'min_observed_valid_fraction': 1.0, 'min_valid_fraction': 1.0, 'failed': []}
- PASS: warp_skipped_frames_within_threshold - {'skipped_count': 2, 'max_skipped_frames': 2}
- PASS: all_accepted_registration_frames_warped - {'accepted_registration_count': 1, 'missing': [], 'registration_results_present': True}

## Outputs

- PASS: F000010 model=integer_translation_nearest valid_fraction=1.0 artifact_ready=True

## Skipped Frames

- PASS: F000011 status=quality_rejected reason=registration did not produce an accepted transform
- PASS: F000012 status=quality_rejected reason=registration did not produce an accepted transform
