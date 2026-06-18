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
- Pixel verify: True
- Pixel tolerance: 0
- Science residual verify: True
- Science residual reference: None
- Max science RMS: 0.0
- Max science max abs: 0.0

## Checks

- PASS: warp_results_present - {'path': 'runs\\checkpoints\\s2_gate_316_enabled_run\\warp_results.json', 'required': True}
- PASS: warp_outputs_present - {'output_count': 1}
- PASS: skipped_warp_rows_have_reasons - {'failed': []}
- PASS: warp_output_artifacts_ready - {'failed': []}
- PASS: warp_valid_fraction_meets_threshold - {'min_observed_valid_fraction': 1.0, 'min_valid_fraction': 1.0, 'failed': []}
- PASS: warp_skipped_frames_within_threshold - {'skipped_count': 2, 'max_skipped_frames': 2}
- PASS: all_accepted_registration_frames_warped - {'accepted_registration_count': 1, 'missing': [], 'registration_results_present': True}
- PASS: warp_pixel_verification_passed - {'failed': []}
- PASS: warp_science_residual_verification_passed - {'reference_frame_id': 'F000010', 'verified_count': 1, 'failed': [], 'max_rms': 0.0, 'max_abs': 0.0, 'max_rms_threshold': 0.0, 'max_abs_threshold': 0.0}

## Outputs

- PASS: F000010 model=integer_translation_nearest valid_fraction=1.0 artifact_ready=True pixel={'verified': True, 'status': 'passed', 'passed': True, 'tile_size': 8, 'tolerance': 0, 'coverage_valid_pixels': 576, 'coverage_invalid_pixels': 0, 'reported_valid_pixels': 576, 'dq_valid_pixels': 576, 'dq_warp_edge_pixels': 0, 'expected_warp_edge_pixels': 0, 'dq_summary_valid': 576, 'dq_summary_warp_edge': None, 'valid_delta': 0, 'dq_valid_delta': 0, 'summary_valid_delta': 0, 'dq_warp_edge_delta': 0, 'summary_warp_edge_delta': None, 'max_delta': 0, 'failed_checks': []} science={'verified': True, 'status': 'passed', 'passed': True, 'reference_frame_id': 'F000010', 'tile_size': 8, 'common_valid_pixels': 576, 'mean': 0.0, 'mean_abs': 0.0, 'rms': 0.0, 'max_abs': 0.0, 'max_rms_threshold': 0.0, 'max_abs_threshold': 0.0, 'failed_checks': []}

## Skipped Frames

- PASS: F000011 status=quality_rejected reason=registration did not produce an accepted transform
- PASS: F000012 status=quality_rejected reason=registration did not produce an accepted transform
