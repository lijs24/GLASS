# GLASS Pipeline Invariant Contract Audit

- Status: passed
- Run: `C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle\run`

## Checks

- PASS: `integration_artifact_exists` - {'path': 'C:\\glass_runs\\phase2_s2_gate_198_guardrails_contract_bundle\\run\\integration_results.json'}
- PASS: `integration_outputs_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_output_maps_available` - {'map_count': 6, 'failed': []}
- PASS: `integration_dq_contract` - {'output_count': 1, 'failed': []}
- PASS: `integration_stack_result_contract` - {'output_count': 1, 'required_count': 1, 'failed': []}
- PASS: `integration_resident_result_contract` - {'output_count': 1, 'required_count': 0, 'failed': []}
- PASS: `integration_dq_map_pixels_match_summary` - {'verified_records': 1, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_coverage_map_pixels_match_dq` - {'verified_records': 1, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_rejection_map_pixels_match_dq` - {'verified_records': 2, 'failed': [], 'tolerance_pixels': 0}
- PASS: `warp_outputs_have_dq_and_coverage` - {'warp_output_count': 2, 'failed': []}
- PASS: `warp_skipped_frames_are_explained` - {'skipped_count': 2, 'failed': []}
- PASS: `local_normalization_contract` - {'enabled': False, 'row_count': 2, 'failed': [], 'top_level_crop_box_recorded': True}
