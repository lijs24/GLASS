# GLASS Pipeline Invariant Contract Audit

- Status: failed
- Run: `GATE293_FIXTURE\legacy_master_run`

## Checks

- PASS: `integration_artifact_exists` - {'path': 'GATE293_FIXTURE\\legacy_master_run\\integration_results.json'}
- PASS: `integration_outputs_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_default_engine_policy` - {'output_count': 1, 'non_resident_count': 0, 'resident_count': 1, 'top_level_present': False, 'top_level_default_ok': False, 'failed': []}
- FAIL: `stack_engine_runtime_default_path` - {'master_count': 1, 'master_stack_engine_count': 0, 'master_resident_count': 0, 'legacy_master_count': 1, 'integration_output_count': 1, 'integration_stack_engine_default_count': 0, 'integration_resident_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [{'name': 'bias_legacy', 'type': 'bias', 'tile_stack_mode': 'legacy_streaming_accumulator', 'path_exists': True, 'stack_engine_enabled': False, 'contract_ok': True, 'status': 'failed', 'failures': ['master_stack_engine_not_enabled', 'legacy_master_stack_mode']}], 'failed_outputs': [], 'stack_result_contract_failures': [], 'resident_result_contract_failures': []}
- PASS: `integration_output_maps_available` - {'map_count': 6, 'failed': []}
- PASS: `integration_dq_contract` - {'output_count': 1, 'failed': []}
- PASS: `integration_stack_result_contract` - {'output_count': 1, 'required_count': 0, 'failed': []}
- PASS: `integration_resident_result_contract` - {'output_count': 1, 'required_count': 1, 'failed': []}
- PASS: `integration_sample_accounting_closure` - {'output_count': 1, 'present_count': 0, 'failed': []}
- PASS: `calibration_master_surfaces_present` - {'actual': 1, 'required_min': 1}
- PASS: `calibration_master_surface_contract` - {'master_count': 1, 'failed': []}
- PASS: `resident_calibration_surface_contract` - {'required': False, 'resident_surface_count': 0, 'failed': []}
- PASS: `calibrated_lights_present` - {'actual': 1, 'required_min': 1}
- PASS: `calibrated_light_dq_contract` - {'light_count': 1, 'failed': []}

## Integration Engine Policy

- top-level present `False`, default `None`, non-resident outputs `0`, passed `True`
- H: mode ``, backend `cuda_resident_stack`, status `resident_not_required`, passed `True`

## StackEngine Runtime Default Path

- status `failed`, masters `1`, master StackEngine `0`, master resident `0`, legacy masters `1`, integration outputs `1`, integration StackEngine `0`, resident outputs `1`, explicit CUDA fast paths `0`
- failed masters: `[{'name': 'bias_legacy', 'type': 'bias', 'tile_stack_mode': 'legacy_streaming_accumulator', 'path_exists': True, 'stack_engine_enabled': False, 'contract_ok': True, 'status': 'failed', 'failures': ['master_stack_engine_not_enabled', 'legacy_master_stack_mode']}]`

## Integration Sample Accounting Closure

- H: status `missing`, input-valid `None`, final-valid `None`, rejected `None`, passed `True`
