# Resident Warp Input Audit

- Status: `passed`
- Passed: `True`
- Recommendation: `target_resident_registration_matrix_precision`
- Frame count: `8`
- Interpolation: `bilinear`

## Summary

- CPU-matrix resident warp RMS: `{'count': 8, 'max': 0.0002643936071558697, 'mean': 0.00019183110707193216}`
- Resident-matrix resident warp RMS: `{'count': 8, 'max': 0.15866161883969132, 'mean': 0.07399732349415561}`
- Matrix translation delta px: `{'count': 8, 'max': 0.007707665637643805, 'mean': 0.0035659634102593804}`
- Resident matrix warp parity passed: `False`

## Checks

- PASS: `frame_inputs_present` - {'selected_frame_count': 8}
- PASS: `cuda_warp_replay_completed` - {'statuses': ['completed']}
- PASS: `cpu_matrix_resident_warp_matches_cpu_registered` - {'max_rms': 0.0002643936071558697, 'tolerance': 0.0005}
- PASS: `resident_matrix_warp_delta_attributed` - {'max_rms': 0.15866161883969132, 'tolerance': 0.1, 'resident_matrix_warp_parity_passed': False, 'matrix_translation_delta_px_max': 0.007707665637643805}

## Worst Frames

| frame | matrix delta px | cpu-matrix RMS | resident-matrix RMS |
| --- | ---: | ---: | ---: |
| `F000013` | 0.007707665637643805 | 0.0002643936071558697 | 0.15866161883969132 |
| `F000014` | 0.005898063933990233 | 0.00018421133289196341 | 0.1332950163094695 |
| `F000018` | 0.005104828736889345 | 0.0002265175756782982 | 0.1102879726559501 |
| `F000017` | 0.0040095624646595785 | 0.00017397212154547965 | 0.08151853799556133 |
| `F000019` | 0.0034828640675653136 | 0.00021056776303832303 | 0.06367764502019464 |
| `F000020` | 0.0016940883521812226 | 0.000262862319488557 | 0.03247177842962697 |
| `F000015` | 0.0006306340891455485 | 0.00021212413677696638 | 0.012066018702750963 |
| `F000016` | 0.0 | 0.0 | 0.0 |
