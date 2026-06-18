# GLASS Pipeline Invariant Contract Audit

- Status: passed
- Run: `runs\checkpoints\s2_gate_316_enabled_run`

## Checks

- PASS: `integration_artifact_exists` - {'path': 'runs\\checkpoints\\s2_gate_316_enabled_run\\integration_results.json'}
- PASS: `integration_outputs_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_default_engine_policy` - {'output_count': 1, 'non_resident_count': 1, 'resident_count': 0, 'top_level_present': True, 'top_level_default_ok': True, 'failed': []}
- PASS: `stack_engine_runtime_default_path` - {'master_count': 3, 'master_stack_engine_count': 3, 'master_resident_count': 0, 'legacy_master_count': 0, 'integration_output_count': 1, 'integration_stack_engine_default_count': 1, 'integration_resident_count': 0, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': [], 'stack_result_contract_failures': [], 'resident_result_contract_failures': []}
- PASS: `integration_output_maps_available` - {'map_count': 6, 'failed': []}
- PASS: `integration_dq_contract` - {'output_count': 1, 'failed': []}
- PASS: `integration_stack_result_contract` - {'output_count': 1, 'required_count': 1, 'failed': []}
- PASS: `integration_resident_result_contract` - {'output_count': 1, 'required_count': 0, 'failed': []}
- PASS: `integration_sample_accounting_closure` - {'output_count': 1, 'present_count': 1, 'failed': []}
- PASS: `calibration_master_surfaces_present` - {'actual': 3, 'required_min': 1}
- PASS: `calibration_master_surface_contract` - {'master_count': 3, 'failed': []}
- PASS: `resident_calibration_surface_contract` - {'required': False, 'resident_surface_count': 0, 'failed': []}
- PASS: `calibrated_lights_present` - {'actual': 3, 'required_min': 1}
- PASS: `calibrated_light_dq_contract` - {'light_count': 3, 'failed': []}
- PASS: `integration_dq_map_pixels_match_summary` - {'verified_records': 1, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_coverage_map_pixels_match_dq` - {'verified_records': 1, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_rejection_map_pixels_match_dq` - {'verified_records': 2, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_rejection_sample_counts_match_maps` - {'verified_records': 1, 'required_records': 0, 'failed': [], 'tolerance_pixels': 0}
- PASS: `warp_outputs_have_dq_and_coverage` - {'warp_output_count': 1, 'failed': []}
- PASS: `warp_skipped_frames_are_explained` - {'skipped_count': 2, 'failed': []}
- PASS: `local_normalization_contract` - {'enabled': True, 'row_count': 1, 'failed': [], 'top_level_crop_box_recorded': True}
- PASS: `local_normalization_continuous_contract_audit` - {'status': 'passed', 'artifact_type': 'local_norm_contract', 'enabled': True, 'output_count': 1, 'pipeline_row_count': 1, 'failed_output_count': 0, 'failed_checks': [], 'failed_outputs': [], 'failed_contract_rows': []}

## Integration Engine Policy

- top-level present `True`, default `stack_engine_cpu`, non-resident outputs `1`, passed `True`
- H: mode `stack_engine_cpu`, backend `cpu`, status `stack_engine_default`, passed `True`

## StackEngine Runtime Default Path

- status `passed`, masters `3`, master StackEngine `3`, master resident `0`, legacy masters `0`, integration outputs `1`, integration StackEngine `1`, resident outputs `0`, explicit CUDA fast paths `0`

## Integration Sample Accounting Closure

- H: status `passed`, input-valid `576`, final-valid `576`, rejected `0`, passed `True`
