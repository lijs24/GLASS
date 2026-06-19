# Resident Parity Summary

- Status: `attention_required`
- Passed: `False`
- Parity passed: `True`
- Recommendation: `fix_resident_result_contract`

## Runs

| label | backend | memory | elapsed s | reference | frames | rejected samples | valid pixels |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| cpu_tile | cpu | tile | 41.93859020000673 | F000016 | 16 | 14796 | 248399 |
| cuda_resident_external_cpu_transform | cuda_resident_stack | resident | 0.2904634000151418 | F000016 | 16 | 14777 | 243098 |

## Compare

- Shape match: `True`
- RMS diff: `0.06858672377130552`
- Relative RMS diff: `0.0003118613896233379`
- P99 abs diff: `0.1982856750488282`
- Max abs diff: `2.6473541259765625`

## Deltas

- Resident/CPU elapsed ratio: `0.006925921892698606`
- Rejected sample delta: `-19`
- Valid pixel delta: `-5301`

## Checks

- PASS: `cpu_run_present` - {'path': 'runs\\checkpoints\\s2_gate_414_runtime_validation_cpu'}
- PASS: `resident_run_present` - {'path': 'runs\\checkpoints\\s2_gate_415_runtime_validation_cuda_external_cpu_transform'}
- PASS: `frame_count_match` - {'cpu_frame_count': 16, 'resident_frame_count': 16, 'delta': 0}
- PASS: `registration_reference_match` - {'cpu_reference_frame_id': 'F000016', 'resident_reference_frame_id': 'F000016'}
- PASS: `registration_row_count_match` - {'cpu_rows': 16, 'resident_rows': 16}
- PASS: `compare_shape_match` - {'shape_match': True}
- PASS: `compare_rms_within_limit` - {'rms_diff': 0.06858672377130552, 'max_rms_diff': 0.1}
- PASS: `compare_relative_rms_within_limit` - {'relative_rms_diff': 0.0003118613896233379, 'max_relative_rms_diff': 0.001}
- PASS: `rejected_sample_delta_within_limit` - {'cpu_rejected_samples': 14796, 'resident_rejected_samples': 14777, 'delta': -19, 'max_abs_delta': 64}
- FAIL: `resident_result_contract_passed` - {'present': True, 'path': 'runs\\checkpoints\\s2_gate_415_runtime_validation_cuda_external_cpu_transform\\resident_result_contract.json', 'status': 'failed', 'passed': False, 'failed_checks': ['resident_outputs_pass_contract']}
