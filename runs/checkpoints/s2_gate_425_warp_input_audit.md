# Resident Warp Input Audit

- Status: `passed`
- Passed: `True`
- Recommendation: `target_resident_registration_matrix_precision`
- Frame count: `16`
- Interpolation: `bilinear`

## Summary

- CPU-matrix resident warp RMS: `{'count': 16, 'max': 0.0002772813662932653, 'mean': 0.000191432803370453}`
- Resident-matrix resident warp RMS: `{'count': 16, 'max': 0.19260848801144254, 'mean': 0.08695099070490556}`
- Matrix translation delta px: `{'count': 16, 'max': 0.008781854250385976, 'mean': 0.0039021745376517994}`
- Resident matrix warp parity passed: `False`

## Checks

- PASS: `frame_inputs_present` - {'selected_frame_count': 16}
- PASS: `cuda_warp_replay_completed` - {'statuses': ['completed']}
- PASS: `cpu_matrix_resident_warp_matches_cpu_registered` - {'max_rms': 0.0002772813662932653, 'tolerance': 0.0005}
- PASS: `resident_matrix_warp_delta_attributed` - {'max_rms': 0.19260848801144254, 'tolerance': 0.1, 'resident_matrix_warp_parity_passed': False, 'matrix_translation_delta_px_max': 0.008781854250385976}

## Worst Frames

| frame | matrix delta px | cpu-matrix RMS | resident-matrix RMS |
| --- | ---: | ---: | ---: |
| `F000024` | 0.008781854250385976 | 0.00026435671217016853 | 0.19260848801144254 |
| `F000013` | 0.008740052972894322 | 0.0002643936071558697 | 0.18657174565052745 |
| `F000023` | 0.007045797277192498 | 0.00014746459667049744 | 0.16288839493579732 |
| `F000019` | 0.006272724994435877 | 0.00021056776303832303 | 0.1368675766370895 |
| `F000018` | 0.0059239275012104775 | 0.0002265175756782982 | 0.12933050826733228 |
| `F000017` | 0.005618193909999641 | 0.00017397212154547965 | 0.1281721062880393 |
| `F000026` | 0.004451632221771915 | 5.983631352514058e-05 | 0.09983811909695402 |
| `F000022` | 0.0037377409943827357 | 0.00023832726292830178 | 0.08613427137959165 |
| `F000027` | 0.002827152832464814 | 0.0002772813662932653 | 0.06481836596426467 |
| `F000020` | 0.002643123952869908 | 0.000262862319488557 | 0.06109519222980453 |
