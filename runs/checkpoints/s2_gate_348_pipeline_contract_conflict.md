# GLASS Pipeline Invariant Contract Audit

- Status: failed
- Run: `runs\checkpoints\s2_gate_348_controlled_admission_conflict_run`

## Checks

- PASS: `integration_artifact_exists` - {'path': 'runs\\checkpoints\\s2_gate_348_controlled_admission_conflict_run\\integration_results.json'}
- PASS: `integration_outputs_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_default_engine_policy` - {'output_count': 1, 'non_resident_count': 0, 'resident_count': 1, 'top_level_present': False, 'top_level_default_ok': False, 'failed': []}
- PASS: `stack_engine_runtime_default_path` - {'master_count': 0, 'master_stack_engine_count': 0, 'master_resident_count': 0, 'legacy_master_count': 0, 'integration_output_count': 1, 'integration_stack_engine_default_count': 0, 'integration_resident_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': [], 'stack_result_contract_failures': [], 'resident_result_contract_failures': []}
- PASS: `integration_output_maps_available` - {'map_count': 6, 'failed': []}
- PASS: `integration_dq_contract` - {'output_count': 1, 'failed': []}
- PASS: `integration_stack_result_contract` - {'output_count': 1, 'required_count': 0, 'failed': []}
- PASS: `integration_resident_result_contract` - {'output_count': 1, 'required_count': 1, 'failed': []}
- PASS: `integration_sample_accounting_closure` - {'output_count': 1, 'present_count': 0, 'failed': []}
- FAIL: `frame_accounting_no_integration_conflicts` - {'present': True, 'status': 'failed', 'frame_count': 3, 'integration_conflict_frames': 1, 'conflicts': [{'frame_id': 'L0000', 'final_status': 'integration_conflict', 'integration_status': 'used', 'integration_weight': 1.0, 'quality_gate_status': 'rejected', 'registration_status': 'quality_rejected', 'warp_status': 'skipped', 'local_norm_status': 'not_run', 'integration_conflict_count': 3, 'integration_conflicts': [{'reason': 'positive integration weight for quality-rejected frame', 'stage': 'quality', 'status': 'rejected'}, {'reason': 'positive integration weight for non-accepted registration frame', 'stage': 'registration', 'status': 'quality_rejected'}, {'reason': 'positive integration weight for non-warped frame', 'stage': 'warp', 'status': 'skipped'}]}]}

## Integration Engine Policy

- top-level present `False`, default `None`, non-resident outputs `0`, passed `True`
- H: mode ``, backend `cuda_resident_stack`, status `resident_not_required`, passed `True`

## StackEngine Runtime Default Path

- status `passed`, masters `0`, master StackEngine `0`, master resident `0`, legacy masters `0`, integration outputs `1`, integration StackEngine `0`, resident outputs `1`, explicit CUDA fast paths `0`

## Integration Sample Accounting Closure

- H: status `missing`, input-valid `None`, final-valid `None`, rejected `None`, passed `True`

## Frame Admission Accounting

- present `True`, status `failed`, frames `3`, integrated `2`, zero-weight `0`, integration conflicts `1`
- L0000: status `integration_conflict`, weight `1.0`, conflicts `[{'reason': 'positive integration weight for quality-rejected frame', 'stage': 'quality', 'status': 'rejected'}, {'reason': 'positive integration weight for non-accepted registration frame', 'stage': 'registration', 'status': 'quality_rejected'}, {'reason': 'positive integration weight for non-warped frame', 'stage': 'warp', 'status': 'skipped'}]`
