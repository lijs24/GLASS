# Resident Registration Matrix Compare

- Status: `passed`
- Passed: `True`
- Recommendation: `registration_matrices_ready`
- Next target: `continue with warp, DQ, rejection, and image parity validation`
- Baseline: `cpu_tile` `runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json`
- Candidate: `cuda_resident_triangle_no_pixel_refine_refF16` `runs\checkpoints\s2_gate_420_no_pixel_refine_refF16_cuda_hardened\registration_results.json`

## Summary

| Metric | Value |
| --- | ---: |
| `baseline_row_count` | 16 |
| `candidate_row_count` | 16 |
| `common_row_count` | 16 |
| `missing_frame_count` | 0 |
| `status_mismatch_count` | 0 |
| `reference_mismatch_count` | 0 |
| `translation_delta_px.max` | 0.008781854250385976 |
| `translation_delta_px.mean` | 0.0039021745376517335 |
| `matrix_delta_frobenius.max` | 0.008781854250385976 |
| `matrix_delta_frobenius.mean` | 0.0039021745376517335 |

## Checks

- PASS: `reference_frame_match` - {'baseline_reference_frame_id': 'F000016', 'candidate_reference_frame_id': 'F000016'}
- PASS: `row_count_match` - {'baseline_row_count': 16, 'candidate_row_count': 16}
- PASS: `missing_frame_rows` - {'missing_frame_count': 0}
- PASS: `status_rows_match` - {'status_mismatch_count': 0}
- PASS: `reference_rows_match` - {'reference_mismatch_count': 0}
- PASS: `translation_delta_within_limit` - {'max_translation_delta_px': 0.008781854250385976, 'threshold': 0.1}
- PASS: `matrix_delta_within_limit` - {'max_matrix_delta_frobenius': 0.008781854250385976, 'threshold': 0.1}

## Worst Translation Rows

| Frame | Baseline status | Candidate status | Baseline tx | Baseline ty | Candidate tx | Candidate ty | Delta px | Matrix delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `F000024` | ok | ok | 2.00135529484578 | -2.00867664335766 | 2.0 | -2.0 | 0.008781854250385976 | 0.008781854250385976 |
| `F000013` | ok | ok | 2.9999893529665655 | -0.00874004648784421 | 3.0 | 0.0 | 0.008740052972894322 | 0.008740052972894322 |
| `F000023` | ok | ok | 3.0057964306162717 | -2.0040055775341443 | 3.0 | -2.0 | 0.007045797277192498 | 0.007045797277192498 |
| `F000019` | ok | ok | 1.9937828574277567 | -1.0008331969108326 | 2.0 | -1.0 | 0.006272724994435877 | 0.006272724994435877 |
| `F000018` | ok | ok | 2.9992375289487185 | -1.0058746536013246 | 3.0 | -1.0 | 0.0059239275012104775 | 0.0059239275012104775 |
| `F000017` | ok | ok | -0.9975822748075416 | -0.005071361523704354 | -1.0 | 0.0 | 0.005618193909999641 | 0.005618193909999641 |
| `F000026` | ok | ok | 0.0013415540097980738 | -2.0042446745784233 | -2.842170943040401e-14 | -2.0 | 0.00445163222178048 | 0.00445163222178048 |
| `F000022` | ok | ok | -1.0019108026609658 | -0.9967875957707761 | -1.0 | -1.0 | 0.0037377409943827357 | 0.0037377409943827357 |
| `F000027` | ok | ok | -0.99870567562564 | -2.002513467237115 | -1.0 | -2.0 | 0.002827152832464814 | 0.002827152832464814 |
| `F000020` | ok | ok | 1.001482614433698 | -1.0021881404596655 | 1.0 | -1.0 | 0.002643123952869908 | 0.002643123952869908 |
