# Resident Registration Matrix Compare

- Status: `passed`
- Passed: `True`
- Recommendation: `registration_matrices_ready`
- Next target: `continue with warp, DQ, rejection, and image parity validation`
- Baseline: `baseline` `runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json`
- Candidate: `candidate` `runs\checkpoints\s2_gate_422_centroid_refine_refF16_cuda_hardened\registration_results.json`

## Summary

| Metric | Value |
| --- | ---: |
| `baseline_row_count` | 16 |
| `candidate_row_count` | 16 |
| `common_row_count` | 16 |
| `missing_frame_count` | 0 |
| `status_mismatch_count` | 0 |
| `reference_mismatch_count` | 0 |
| `translation_delta_px.max` | 0.010876804100490163 |
| `translation_delta_px.mean` | 0.0056985537704908155 |
| `matrix_delta_frobenius.max` | 0.010876804100490163 |
| `matrix_delta_frobenius.mean` | 0.0056985537704908155 |

## Checks

- PASS: `reference_frame_match` - {'baseline_reference_frame_id': 'F000016', 'candidate_reference_frame_id': 'F000016'}
- PASS: `row_count_match` - {'baseline_row_count': 16, 'candidate_row_count': 16}
- PASS: `missing_frame_rows` - {'missing_frame_count': 0}
- PASS: `status_rows_match` - {'status_mismatch_count': 0}
- PASS: `reference_rows_match` - {'reference_mismatch_count': 0}
- PASS: `translation_delta_within_limit` - {'max_translation_delta_px': 0.010876804100490163, 'threshold': 0.05}
- PASS: `matrix_delta_within_limit` - {'max_matrix_delta_frobenius': 0.010876804100490163, 'threshold': 0.05}

## Worst Translation Rows

| Frame | Baseline status | Candidate status | Baseline tx | Baseline ty | Candidate tx | Candidate ty | Delta px | Matrix delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `F000024` | ok | ok | 2.00135529484578 | -2.00867664335766 | 2.0011043548583984 | -1.997802734375 | 0.010876804100490163 | 0.010876804100490163 |
| `F000018` | ok | ok | 2.9992375289487185 | -1.0058746536013246 | 3.0033035278320312 | -0.99725341796875 | 0.009531948948220055 | 0.009531948948220055 |
| `F000026` | ok | ok | 0.0013415540097980738 | -2.0042446745784233 | -0.0020294189453125 | -1.995452880859375 | 0.009415895892711607 | 0.009415895892711607 |
| `F000023` | ok | ok | 3.0057964306162717 | -2.0040055775341443 | 3.0022659301757812 | -1.9958877563476562 | 0.008852313492872788 | 0.008852313492872788 |
| `F000017` | ok | ok | -0.9975822748075416 | -0.005071361523704354 | -0.9995956420898438 | 0.00289154052734375 | 0.008213492368537937 | 0.008213492368537937 |
| `F000019` | ok | ok | 1.9937828574277567 | -1.0008331969108326 | 1.9993972778320312 | -0.996246337890625 | 0.007249896009405508 | 0.007249896009405508 |
| `F000028` | ok | ok | 2.997876111271836 | -3.000762274540527 | 3.0046653747558594 | -2.9983482360839844 | 0.0072056700122307285 | 0.0072056700122307285 |
| `F000013` | ok | ok | 2.9999893529665655 | -0.00874004648784421 | 3.001922607421875 | -0.00304412841796875 | 0.0060150607185387285 | 0.0060150607185387285 |
| `F000015` | ok | ok | 0.9987398822904368 | 8.278444315124034e-05 | 1.0019798278808594 | 0.005096435546875 | 0.005969417460587713 | 0.005969417460587713 |
| `F000022` | ok | ok | -1.0019108026609658 | -0.9967875957707761 | -0.998931884765625 | -1.0016021728515625 | 0.0056616344189655025 | 0.0056616344189655025 |
