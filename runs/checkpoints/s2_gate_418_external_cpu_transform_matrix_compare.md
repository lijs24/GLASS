# Resident Registration Matrix Compare

- Status: `passed`
- Passed: `True`
- Recommendation: `registration_matrices_ready`
- Next target: `continue with warp, DQ, rejection, and image parity validation`
- Baseline: `cpu_tile` `runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json`
- Candidate: `cuda_resident_external_cpu_transform` `runs\checkpoints\s2_gate_415_runtime_validation_cuda_external_cpu_transform\registration_results.json`

## Summary

| Metric | Value |
| --- | ---: |
| `baseline_row_count` | 16 |
| `candidate_row_count` | 16 |
| `common_row_count` | 16 |
| `missing_frame_count` | 0 |
| `status_mismatch_count` | 0 |
| `reference_mismatch_count` | 0 |
| `translation_delta_px.max` | 0.0 |
| `translation_delta_px.mean` | 0.0 |
| `matrix_delta_frobenius.max` | 0.0 |
| `matrix_delta_frobenius.mean` | 0.0 |

## Checks

- PASS: `reference_frame_match` - {'baseline_reference_frame_id': 'F000016', 'candidate_reference_frame_id': 'F000016'}
- PASS: `row_count_match` - {'baseline_row_count': 16, 'candidate_row_count': 16}
- PASS: `missing_frame_rows` - {'missing_frame_count': 0}
- PASS: `status_rows_match` - {'status_mismatch_count': 0}
- PASS: `reference_rows_match` - {'reference_mismatch_count': 0}
- PASS: `translation_delta_within_limit` - {'max_translation_delta_px': 0.0, 'threshold': 0.001}
- PASS: `matrix_delta_within_limit` - {'max_matrix_delta_frobenius': 0.0, 'threshold': 0.001}

## Worst Translation Rows

| Frame | Baseline status | Candidate status | Baseline tx | Baseline ty | Candidate tx | Candidate ty | Delta px | Matrix delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `F000013` | ok | ok | 2.9999893529665655 | -0.00874004648784421 | 2.9999893529665655 | -0.00874004648784421 | 0.0 | 0.0 |
| `F000014` | ok | ok | 2.000117269395446 | 0.0002545627357690705 | 2.000117269395446 | 0.0002545627357690705 | 0.0 | 0.0 |
| `F000015` | ok | ok | 0.9987398822904368 | 8.278444315124034e-05 | 0.9987398822904368 | 8.278444315124034e-05 | 0.0 | 0.0 |
| `F000016` | reference | reference | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| `F000017` | ok | ok | -0.9975822748075416 | -0.005071361523704354 | -0.9975822748075416 | -0.005071361523704354 | 0.0 | 0.0 |
| `F000018` | ok | ok | 2.9992375289487185 | -1.0058746536013246 | 2.9992375289487185 | -1.0058746536013246 | 0.0 | 0.0 |
| `F000019` | ok | ok | 1.9937828574277567 | -1.0008331969108326 | 1.9937828574277567 | -1.0008331969108326 | 0.0 | 0.0 |
| `F000020` | ok | ok | 1.001482614433698 | -1.0021881404596655 | 1.001482614433698 | -1.0021881404596655 | 0.0 | 0.0 |
| `F000021` | ok | ok | 0.0005259830282682287 | -1.0014606036755467 | 0.0005259830282682287 | -1.0014606036755467 | 0.0 | 0.0 |
| `F000022` | ok | ok | -1.0019108026609658 | -0.9967875957707761 | -1.0019108026609658 | -0.9967875957707761 | 0.0 | 0.0 |
