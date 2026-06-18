# GLASS Pipeline Invariant Contract Audit

- Status: passed
- Run: `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident`

## Checks

- PASS: `integration_artifact_exists` - {'path': 'C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\integration_results.json'}
- PASS: `integration_outputs_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_default_engine_policy` - {'output_count': 1, 'non_resident_count': 0, 'resident_count': 1, 'top_level_present': False, 'top_level_default_ok': False, 'failed': []}
- PASS: `stack_engine_runtime_default_path` - {'master_count': 0, 'master_stack_engine_count': 0, 'master_resident_count': 0, 'legacy_master_count': 0, 'integration_output_count': 1, 'integration_stack_engine_default_count': 0, 'integration_resident_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': [], 'stack_result_contract_failures': [], 'resident_result_contract_failures': []}
- PASS: `integration_output_maps_available` - {'map_count': 6, 'failed': []}
- PASS: `integration_dq_contract` - {'output_count': 1, 'failed': []}
- PASS: `integration_stack_result_contract` - {'output_count': 1, 'required_count': 0, 'failed': []}
- PASS: `integration_resident_result_contract` - {'output_count': 1, 'required_count': 1, 'failed': []}
- PASS: `integration_sample_accounting_closure` - {'output_count': 1, 'present_count': 0, 'failed': []}
- PASS: `integration_dq_map_pixels_match_summary` - {'verified_records': 1, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_coverage_map_pixels_match_dq` - {'verified_records': 1, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_rejection_map_pixels_match_dq` - {'verified_records': 2, 'failed': [], 'tolerance_pixels': 0}
- PASS: `integration_rejection_sample_counts_match_maps` - {'verified_records': 1, 'required_records': 1, 'failed': [], 'tolerance_pixels': 0}
- PASS: `local_normalization_contract` - {'enabled': False, 'row_count': 0, 'failed': [], 'top_level_crop_box_recorded': True}

## Integration Engine Policy

- top-level present `False`, default `None`, non-resident outputs `0`, passed `True`
- H: mode ``, backend `cuda_resident_stack`, status `resident_not_required`, passed `True`

## StackEngine Runtime Default Path

- status `passed`, masters `0`, master StackEngine `0`, master resident `0`, legacy masters `0`, integration outputs `1`, integration StackEngine `0`, resident outputs `1`, explicit CUDA fast paths `0`

## Integration Sample Accounting Closure

- H: status `missing`, input-valid `None`, final-valid `None`, rejected `None`, passed `True`
