# Local Normalization Contract

- Status: passed
- Passed: True
- Enabled: True
- Reference frame: L1
- Model: continuous_grid_mean_std_v1
- Coefficient field model: bilinear_tile_center_v1
- Output count: 1
- Failed output count: 0

## Checks

- PASS: local_norm_results_present - {'path': 'runs\\checkpoints\\s2_gate_313_local_norm_contract_fixture_run\\local_norm_results.json'}
- PASS: schema_version_recorded - {'schema_version': 1}
- PASS: enabled_state_recorded - {'enabled': True}
- PASS: crop_box_recorded - {'crop_box': None}
- PASS: outputs_list_recorded - {'output_count': 1}
- PASS: reference_frame_id_recorded - {'reference_frame_id': 'L1'}
- PASS: model_is_continuous - {'model': 'continuous_grid_mean_std_v1'}
- PASS: coefficient_field_model_is_bilinear - {'coefficient_field_model': 'bilinear_tile_center_v1'}
- PASS: enabled_outputs_present - {'output_count': 1}
- PASS: all_outputs_are_objects - {'output_count': 1, 'object_output_count': 1}
- PASS: output_contracts_passed - {'output_count': 1, 'failed': []}

## Outputs

- PASS: L1 status=reference model=continuous_grid_mean_std_v1 failed=[]
