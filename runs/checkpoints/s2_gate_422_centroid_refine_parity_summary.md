# Resident Parity Summary

- Status: `attention_required`
- Passed: `False`
- Parity passed: `False`
- Recommendation: `fix_resident_registration_or_dq_parity`

## Runs

| label | backend | memory | elapsed s | reference | frames | rejected samples | valid pixels |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| cpu_tile | cpu | tile | 41.93859020000673 | F000016 | 16 | 14796 | 248399 |
| cuda_resident | cuda_resident_stack | resident | 80.3392214999767 | F000016 | 16 | 14811 | 244065 |

## Compare

- Shape match: `True`
- RMS diff: `0.23299911258634792`
- Relative RMS diff: `0.0010607677781668903`
- P99 abs diff: `1.0494990539550804`
- Max abs diff: `11.182052612304688`

## Deltas

- Resident/CPU elapsed ratio: `1.9156395366853274`
- Rejected sample delta: `15`
- Valid pixel delta: `-4334`

## Checks

- PASS: `cpu_run_present` - {'path': 'runs\\checkpoints\\s2_gate_414_runtime_validation_cpu'}
- PASS: `resident_run_present` - {'path': 'runs\\checkpoints\\s2_gate_422_centroid_refine_refF16_cuda_hardened'}
- PASS: `frame_count_match` - {'cpu_frame_count': 16, 'resident_frame_count': 16, 'delta': 0}
- PASS: `registration_reference_match` - {'cpu_reference_frame_id': 'F000016', 'resident_reference_frame_id': 'F000016'}
- PASS: `registration_row_count_match` - {'cpu_rows': 16, 'resident_rows': 16}
- PASS: `compare_shape_match` - {'shape_match': True}
- FAIL: `compare_rms_within_limit` - {'rms_diff': 0.23299911258634792, 'max_rms_diff': 0.1}
- FAIL: `compare_relative_rms_within_limit` - {'relative_rms_diff': 0.0010607677781668903, 'max_relative_rms_diff': 0.001}
- PASS: `rejected_sample_delta_within_limit` - {'cpu_rejected_samples': 14796, 'resident_rejected_samples': 14811, 'delta': 15, 'max_abs_delta': 64}
- PASS: `resident_result_contract_passed` - {'present': True, 'path': 'runs\\checkpoints\\s2_gate_422_centroid_refine_refF16_cuda_hardened\\resident_result_contract.json', 'status': 'passed', 'passed': True, 'failed_checks': []}
