# GLASS Pipeline Invariant Contract Audit

- Status: passed
- Run: `GATE293_FIXTURE\explicit_cuda_fast_path_run`

## Checks

- PASS: `integration_artifact_exists` - {'path': 'GATE293_FIXTURE\\explicit_cuda_fast_path_run\\integration_results.json'}
- PASS: `integration_outputs_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_default_engine_policy` - {'output_count': 1, 'non_resident_count': 1, 'resident_count': 0, 'top_level_present': True, 'top_level_default_ok': True, 'failed': []}
- PASS: `stack_engine_runtime_default_path` - {'master_count': 0, 'master_stack_engine_count': 0, 'master_resident_count': 0, 'legacy_master_count': 0, 'integration_output_count': 1, 'integration_stack_engine_default_count': 0, 'integration_resident_count': 0, 'explicit_cuda_fast_path_count': 1, 'failed_masters': [], 'failed_outputs': [], 'stack_result_contract_failures': [], 'resident_result_contract_failures': []}
- PASS: `integration_output_maps_available` - {'map_count': 6, 'failed': []}
- PASS: `integration_dq_contract` - {'output_count': 1, 'failed': []}
- PASS: `integration_stack_result_contract` - {'output_count': 1, 'required_count': 0, 'failed': []}
- PASS: `integration_resident_result_contract` - {'output_count': 1, 'required_count': 0, 'failed': []}
- PASS: `integration_sample_accounting_closure` - {'output_count': 1, 'present_count': 0, 'failed': []}

## Integration Engine Policy

- top-level present `True`, default `stack_engine_cpu`, non-resident outputs `1`, passed `True`
- H: mode `cuda_streaming_accumulator_fast_path`, backend `cuda`, status `explicit_cuda_fast_path`, passed `True`

## StackEngine Runtime Default Path

- status `passed`, masters `0`, master StackEngine `0`, master resident `0`, legacy masters `0`, integration outputs `1`, integration StackEngine `0`, resident outputs `0`, explicit CUDA fast paths `1`

## Integration Sample Accounting Closure

- H: status `missing`, input-valid `None`, final-valid `None`, rejected `None`, passed `True`
