# Resident Registration Matrix Compare

- Status: `attention_required`
- Passed: `False`
- Recommendation: `fix_resident_transform_estimation`
- Next target: `compare triangle descriptor fit and pixel-refine outputs against CPU/external matrices`
- Baseline: `cpu_tile` `runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json`
- Candidate: `cuda_resident_translation_ncc` `runs\checkpoints\s2_gate_419_translation_ncc_cuda_hardened\registration_results.json`

## Summary

| Metric | Value |
| --- | ---: |
| `baseline_row_count` | 16 |
| `candidate_row_count` | 16 |
| `common_row_count` | 16 |
| `missing_frame_count` | 0 |
| `status_mismatch_count` | 0 |
| `reference_mismatch_count` | 0 |
| `translation_delta_px.max` | 0.2562184973123085 |
| `translation_delta_px.mean` | 0.23488917697034084 |
| `matrix_delta_frobenius.max` | 0.2562184973123085 |
| `matrix_delta_frobenius.mean` | 0.23488917697034084 |

## Checks

- PASS: `reference_frame_match` - {'baseline_reference_frame_id': 'F000016', 'candidate_reference_frame_id': 'F000016'}
- PASS: `row_count_match` - {'baseline_row_count': 16, 'candidate_row_count': 16}
- PASS: `missing_frame_rows` - {'missing_frame_count': 0}
- PASS: `status_rows_match` - {'status_mismatch_count': 0}
- PASS: `reference_rows_match` - {'reference_mismatch_count': 0}
- FAIL: `translation_delta_within_limit` - {'max_translation_delta_px': 0.2562184973123085, 'threshold': 0.1}
- FAIL: `matrix_delta_within_limit` - {'max_matrix_delta_frobenius': 0.2562184973123085, 'threshold': 0.1}

## Worst Translation Rows

| Frame | Baseline status | Candidate status | Baseline tx | Baseline ty | Candidate tx | Candidate ty | Delta px | Matrix delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `F000019` | ok | ok | 1.9937828574277567 | -1.0008331969108326 | 2.25 | -1.0 | 0.2562184973123085 | 0.2562184973123085 |
| `F000018` | ok | ok | 2.9992375289487185 | -1.0058746536013246 | 3.0 | -0.75 | 0.25587578962790103 | 0.25587578962790103 |
| `F000020` | ok | ok | 1.001482614433698 | -1.0021881404596655 | 1.0 | -0.75 | 0.25219249856818304 | 0.25219249856818304 |
| `F000028` | ok | ok | 2.997876111271836 | -3.000762274540527 | 3.25 | -3.0 | 0.2521250410607538 | 0.2521250410607538 |
| `F000021` | ok | ok | 0.0005259830282682287 | -1.0014606036755467 | 0.0 | -0.75 | 0.2514611537773109 | 0.2514611537773109 |
| `F000026` | ok | ok | 0.0013415540097980738 | -2.0042446745784233 | -0.25 | -2.0 | 0.25137739364218287 | 0.25137739364218287 |
| `F000027` | ok | ok | -0.99870567562564 | -2.002513467237115 | -1.25 | -2.0 | 0.2513068940166944 | 0.2513068940166944 |
| `F000025` | ok | ok | 1.0002634187507908 | -1.9989933762887304 | 0.75 | -2.0 | 0.2502654431920831 | 0.2502654431920831 |
| `F000013` | ok | ok | 2.9999893529665655 | -0.00874004648784421 | 2.75 | 0.0 | 0.2501420896395722 | 0.2501420896395722 |
| `F000014` | ok | ok | 2.000117269395446 | 0.0002545627357690705 | 2.0 | 0.25 | 0.24974546479648638 | 0.24974546479648638 |
