# Resident Parity Summary

- Status: `attention_required`
- Passed: `False`
- Parity passed: `False`
- Recommendation: `fix_resident_registration_or_dq_parity`

## Runs

| label | backend | memory | elapsed s | reference | frames | rejected samples | valid pixels |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| cpu_tile | cpu | tile | 41.93859020000673 | F000016 | 16 | 14796 | 248399 |
| cuda_resident_triangle_hardened | cuda_resident_stack | resident | 126.06726049998542 | F000013 | 16 | 17463 | 241923 |

## Compare

- Shape match: `True`
- RMS diff: `40.91291220023316`
- Relative RMS diff: `0.18602955427418083`
- P99 abs diff: `8.442821502685554`
- Max abs diff: `1839.6277465820312`

## Deltas

- Resident/CPU elapsed ratio: `3.0059966226514976`
- Rejected sample delta: `2667`
- Valid pixel delta: `-6476`

## Checks

- PASS: `cpu_run_present` - {'path': 'runs\\checkpoints\\s2_gate_414_runtime_validation_cpu'}
- PASS: `resident_run_present` - {'path': 'runs\\checkpoints\\s2_gate_414_runtime_validation_cuda_hardened'}
- PASS: `frame_count_match` - {'cpu_frame_count': 16, 'resident_frame_count': 16, 'delta': 0}
- FAIL: `registration_reference_match` - {'cpu_reference_frame_id': 'F000016', 'resident_reference_frame_id': 'F000013'}
- PASS: `registration_row_count_match` - {'cpu_rows': 16, 'resident_rows': 16}
- PASS: `compare_shape_match` - {'shape_match': True}
- FAIL: `compare_rms_within_limit` - {'rms_diff': 40.91291220023316, 'max_rms_diff': 0.1}
- FAIL: `compare_relative_rms_within_limit` - {'relative_rms_diff': 0.18602955427418083, 'max_relative_rms_diff': 0.001}
- FAIL: `rejected_sample_delta_within_limit` - {'cpu_rejected_samples': 14796, 'resident_rejected_samples': 17463, 'delta': 2667, 'max_abs_delta': 64}
- FAIL: `resident_result_contract_passed` - {'present': True, 'path': 'runs\\checkpoints\\s2_gate_414_runtime_validation_cuda_hardened\\resident_result_contract.json', 'status': 'failed', 'passed': False, 'failed_checks': ['resident_outputs_pass_contract']}
