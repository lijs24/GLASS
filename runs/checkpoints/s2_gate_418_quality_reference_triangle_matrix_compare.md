# Resident Registration Matrix Compare

- Status: `passed`
- Passed: `True`
- Recommendation: `registration_matrices_ready`
- Next target: `continue with warp, DQ, rejection, and image parity validation`
- Baseline: `cpu_tile` `runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json`
- Candidate: `cuda_resident_triangle_quality_reference` `runs\checkpoints\s2_gate_417_quality_reference_cuda_hardened\registration_results.json`

## Summary

| Metric | Value |
| --- | ---: |
| `baseline_row_count` | 16 |
| `candidate_row_count` | 16 |
| `common_row_count` | 16 |
| `missing_frame_count` | 0 |
| `status_mismatch_count` | 0 |
| `reference_mismatch_count` | 0 |
| `translation_delta_px.max` | 0.18305392208191398 |
| `translation_delta_px.mean` | 0.16714125666991966 |
| `matrix_delta_frobenius.max` | 0.18305392208191398 |
| `matrix_delta_frobenius.mean` | 0.16714125666991966 |

## Checks

- PASS: `reference_frame_match` - {'baseline_reference_frame_id': 'F000016', 'candidate_reference_frame_id': 'F000016'}
- PASS: `row_count_match` - {'baseline_row_count': 16, 'candidate_row_count': 16}
- PASS: `missing_frame_rows` - {'missing_frame_count': 0}
- PASS: `status_rows_match` - {'status_mismatch_count': 0}
- PASS: `reference_rows_match` - {'reference_mismatch_count': 0}
- PASS: `translation_delta_within_limit` - {'max_translation_delta_px': 0.18305392208191398, 'threshold': 0.5}
- PASS: `matrix_delta_within_limit` - {'max_matrix_delta_frobenius': 0.18305392208191398, 'threshold': 0.5}

## Worst Translation Rows

| Frame | Baseline status | Candidate status | Baseline tx | Baseline ty | Candidate tx | Candidate ty | Delta px | Matrix delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `F000013` | ok | ok | 2.9999893529665655 | -0.00874004648784421 | 2.875 | 0.125 | 0.18305392208191398 | 0.18305392208191398 |
| `F000024` | ok | ok | 2.00135529484578 | -2.00867664335766 | 2.125 | -1.875 | 0.18209189463577177 | 0.18209189463577177 |
| `F000026` | ok | ok | 0.0013415540097980738 | -2.0042446745784233 | -0.125 | -1.875 | 0.18073841367150828 | 0.18073841367150828 |
| `F000018` | ok | ok | 2.9992375289487185 | -1.0058746536013246 | 2.875 | -0.875 | 0.18045259364872085 | 0.18045259364872085 |
| `F000027` | ok | ok | -0.99870567562564 | -2.002513467237115 | -1.125 | -1.875 | 0.17947128097834178 | 0.17947128097834178 |
| `F000020` | ok | ok | 1.001482614433698 | -1.0021881404596655 | 0.875 | -0.875 | 0.17937300473474568 | 0.17937300473474568 |
| `F000028` | ok | ok | 2.997876111271836 | -3.000762274540527 | 3.125 | -2.875 | 0.1788201129151236 | 0.1788201129151236 |
| `F000017` | ok | ok | -0.9975822748075416 | -0.005071361523704354 | -0.875 | 0.125 | 0.17873156740101015 | 0.17873156740101015 |
| `F000021` | ok | ok | 0.0005259830282682287 | -1.0014606036755467 | -0.125 | -0.875 | 0.17818264982089801 | 0.17818264982089801 |
| `F000014` | ok | ok | 2.000117269395446 | 0.0002545627357690705 | 1.875 | 0.125 | 0.17667980987995419 | 0.17667980987995419 |
