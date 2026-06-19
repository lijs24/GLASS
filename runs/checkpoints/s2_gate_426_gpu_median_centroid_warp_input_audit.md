# Resident Warp Input Audit

- Status: `passed`
- Passed: `True`
- Recommendation: `target_resident_registration_matrix_precision`
- Frame count: `8`
- Interpolation: `bilinear`

## Summary

- CPU-matrix resident warp RMS: `{'count': 8, 'max': 0.0002643936071558697, 'mean': 0.00019183110707193216}`
- Resident-matrix resident warp RMS: `{'count': 8, 'max': 0.16830002181892761, 'mean': 0.1065692309624858}`
- Matrix translation delta px: `{'count': 8, 'max': 0.009531948948220055, 'mean': 0.005459747234037016}`
- Resident matrix warp parity passed: `False`

## Checks

- PASS: `frame_inputs_present` - {'selected_frame_count': 8}
- PASS: `cuda_warp_replay_completed` - {'statuses': ['completed']}
- PASS: `cpu_matrix_resident_warp_matches_cpu_registered` - {'max_rms': 0.0002643936071558697, 'tolerance': 0.0005}
- PASS: `resident_matrix_warp_delta_attributed` - {'max_rms': 0.16830002181892761, 'tolerance': 0.1, 'resident_matrix_warp_parity_passed': False, 'matrix_translation_delta_px_max': 0.009531948948220055}

## Worst Frames

| frame | matrix delta px | cpu-matrix RMS | resident-matrix RMS |
| --- | ---: | ---: | ---: |
| `F000018` | 0.009531948948220055 | 0.0002265175756782982 | 0.16830002181892761 |
| `F000017` | 0.008213492368537937 | 0.00017397212154547965 | 0.14949062560160825 |
| `F000019` | 0.007249896009405508 | 0.00021056776303832303 | 0.13798819700641035 |
| `F000015` | 0.005969417460587713 | 0.00021212413677696638 | 0.1237187787675965 |
| `F000013` | 0.0060150607185387285 | 0.0002643936071558697 | 0.12057100411494474 |
| `F000014` | 0.004637696804565078 | 0.00018421133289196341 | 0.10774770762352881 |
| `F000020` | 0.002060465562441113 | 0.000262862319488557 | 0.04473751276687002 |
| `F000016` | 0.0 | 0.0 | 0.0 |
