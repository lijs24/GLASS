# Resident Parity Summary

- Status: `passed`
- Passed: `True`
- Parity passed: `True`
- Recommendation: `parity_and_contract_ready`

## Runs

| label | backend | memory | elapsed s | reference | frames | rejected samples | valid pixels |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| cpu_tile | cpu | tile | 41.93859020000673 | F000016 | 16 | 14796 | 248399 |
| cuda_resident | cuda_resident_stack | resident | 80.36748310000985 | F000016 | 16 | 14876 | 245018 |

## Compare

- Shape match: `True`
- RMS diff: `0.0996942253107213`
- Relative RMS diff: `0.00045330609093521205`
- P99 abs diff: `0.22672576904296893`
- Max abs diff: `3.08880615234375`

## Deltas

- Resident/CPU elapsed ratio: `1.9163134172306286`
- Rejected sample delta: `80`
- Valid pixel delta: `-3381`

## Checks

- PASS: `cpu_run_present` - {'path': 'runs\\checkpoints\\s2_gate_414_runtime_validation_cpu'}
- PASS: `resident_run_present` - {'path': 'runs\\checkpoints\\s2_gate_423_common_footprint_refF16_cuda_hardened'}
- PASS: `frame_count_match` - {'cpu_frame_count': 16, 'resident_frame_count': 16, 'delta': 0}
- PASS: `registration_reference_match` - {'cpu_reference_frame_id': 'F000016', 'resident_reference_frame_id': 'F000016'}
- PASS: `registration_row_count_match` - {'cpu_rows': 16, 'resident_rows': 16}
- PASS: `compare_shape_match` - {'shape_match': True}
- PASS: `compare_rms_within_limit` - {'rms_diff': 0.0996942253107213, 'max_rms_diff': 0.1}
- PASS: `compare_relative_rms_within_limit` - {'relative_rms_diff': 0.00045330609093521205, 'max_relative_rms_diff': 0.001}
- PASS: `rejected_sample_delta_within_limit` - {'cpu_rejected_samples': 14796, 'resident_rejected_samples': 14876, 'delta': 80, 'max_abs_delta': 128}
- PASS: `resident_result_contract_passed` - {'present': True, 'path': 'runs\\checkpoints\\s2_gate_423_common_footprint_refF16_cuda_hardened\\resident_result_contract.json', 'status': 'passed', 'passed': True, 'failed_checks': []}
