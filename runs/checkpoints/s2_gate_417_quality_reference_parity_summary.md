# Resident Parity Summary

- Status: `attention_required`
- Passed: `False`
- Parity passed: `False`
- Recommendation: `fix_resident_registration_or_dq_parity`

## Runs

| label | backend | memory | elapsed s | reference | frames | rejected samples | valid pixels |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| cpu_tile | cpu | tile | 41.93859020000673 | F000016 | 16 | 14796 | 248399 |
| cuda_resident_triangle_quality_reference | cuda_resident_stack | resident | 80.44664629999897 | F000016 | 16 | 16376 | 242227 |

## Compare

- Shape match: `True`
- RMS diff: `2.568470708484397`
- Relative RMS diff: `0.011678744811104374`
- P99 abs diff: `2.059838104248047`
- Max abs diff: `151.3243408203125`

## Deltas

- Resident/CPU elapsed ratio: `1.9182010152545867`
- Rejected sample delta: `1580`
- Valid pixel delta: `-6172`

## Checks

- PASS: `cpu_run_present` - {'path': 'runs\\checkpoints\\s2_gate_414_runtime_validation_cpu'}
- PASS: `resident_run_present` - {'path': 'runs\\checkpoints\\s2_gate_417_quality_reference_cuda_hardened'}
- PASS: `frame_count_match` - {'cpu_frame_count': 16, 'resident_frame_count': 16, 'delta': 0}
- PASS: `registration_reference_match` - {'cpu_reference_frame_id': 'F000016', 'resident_reference_frame_id': 'F000016'}
- PASS: `registration_row_count_match` - {'cpu_rows': 16, 'resident_rows': 16}
- PASS: `compare_shape_match` - {'shape_match': True}
- FAIL: `compare_rms_within_limit` - {'rms_diff': 2.568470708484397, 'max_rms_diff': 0.1}
- FAIL: `compare_relative_rms_within_limit` - {'relative_rms_diff': 0.011678744811104374, 'max_relative_rms_diff': 0.001}
- FAIL: `rejected_sample_delta_within_limit` - {'cpu_rejected_samples': 14796, 'resident_rejected_samples': 16376, 'delta': 1580, 'max_abs_delta': 64}
- PASS: `resident_result_contract_passed` - {'present': True, 'path': 'runs\\checkpoints\\s2_gate_417_quality_reference_cuda_hardened\\resident_result_contract.json', 'status': 'passed', 'passed': True, 'failed_checks': []}
