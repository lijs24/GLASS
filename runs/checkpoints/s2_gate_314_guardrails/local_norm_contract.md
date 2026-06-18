# Local Normalization Contract

- Status: passed
- Passed: True
- Enabled: False
- Reference frame: F000010
- Model: None
- Coefficient field model: disabled_passthrough
- Output count: 1
- Failed output count: 0

## Checks

- PASS: local_norm_results_present - {'path': 'runs\\checkpoints\\s2_gate_314_cpu_run\\local_norm_results.json'}
- PASS: schema_version_recorded - {'schema_version': 1}
- PASS: enabled_state_recorded - {'enabled': False}
- PASS: crop_box_recorded - {'crop_box': None}
- PASS: outputs_list_recorded - {'output_count': 1}
- PASS: disabled_model_recorded - {'coefficient_field_model': 'disabled_passthrough'}
- PASS: all_outputs_are_objects - {'output_count': 1, 'object_output_count': 1}
- PASS: output_contracts_passed - {'output_count': 1, 'failed': []}

## Outputs

- PASS: F000010 status=disabled_passthrough model=None failed=[]
