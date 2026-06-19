# Resident Rejection Sample Audit

- Status: `attention_required`
- Passed: `False`
- Recommendation: `fix_resident_geometric_coverage_or_transform`
- Tile size: `64`

## Global Deltas

- Rejected sample delta: `15`
- Coverage sample delta: `489`
- Pre-rejection sample delta: `504`
- Same-pre-rejection abs rejected delta: `832`
- Rejection mismatch pixels: `1089`
- DQ mismatch pixels: `5388`

## Compare Region

### inside_compare_region

- Rejected sample delta: `-38`
- Abs rejected sample delta: `798`
- Coverage sample delta: `38`
- Pre-rejection sample delta: `0`
- Rejection mismatch pixels: `786`

### outside_compare_region

- Rejected sample delta: `53`
- Abs rejected sample delta: `333`
- Coverage sample delta: `451`
- Pre-rejection sample delta: `504`
- Rejection mismatch pixels: `303`

## Top Tiles

| y0 | y1 | x0 | x1 | rejected delta | abs rejected | coverage delta | pre-rejection delta | mismatch px |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 448 | 512 | 0 | 64 | 20 | 46 | 97 | 117 | 44 |
| 384 | 448 | 0 | 64 | 15 | 43 | -207 | -192 | 41 |
| 448 | 512 | 448 | 512 | -2 | 36 | 323 | 321 | 34 |
| 448 | 512 | 128 | 192 | -13 | 33 | 333 | 320 | 30 |
| 320 | 384 | 0 | 64 | 6 | 32 | -198 | -192 | 27 |
| 128 | 192 | 0 | 64 | 6 | 30 | -198 | -192 | 28 |
| 448 | 512 | 384 | 448 | -5 | 29 | 325 | 320 | 28 |
| 64 | 128 | 0 | 64 | 7 | 27 | -199 | -192 | 26 |

## Checks

- PASS: `cpu_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\low_rejection_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\high_rejection_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\dq_map_H.fits', 'exists': True}}}
- PASS: `resident_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_422_centroid_refine_refF16_cuda_hardened\\integration\\resident_coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_422_centroid_refine_refF16_cuda_hardened\\integration\\resident_low_rejection_map_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_422_centroid_refine_refF16_cuda_hardened\\integration\\resident_high_rejection_map_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_422_centroid_refine_refF16_cuda_hardened\\integration\\resident_dq_map_H.fits', 'exists': True}}}
- PASS: `map_shapes_match` - {'shapes': {'cpu_coverage': [512, 512], 'cpu_low_rejection': [512, 512], 'cpu_high_rejection': [512, 512], 'cpu_dq': [512, 512], 'resident_coverage': [512, 512], 'resident_low_rejection': [512, 512], 'resident_high_rejection': [512, 512], 'resident_dq': [512, 512]}, 'shape_match': True, 'shape': [512, 512]}
- PASS: `rejected_sample_delta_within_limit` - {'delta': 15, 'max_abs_delta': 64}
- FAIL: `pre_rejection_sample_delta_within_limit` - {'delta': 504, 'max_abs_delta': 0, 'note': 'pre-rejection sample delta compares coverage+low+high maps and identifies geometric/warp/DQ input-sample drift before rejection.'}
- FAIL: `same_pre_rejection_semantic_delta_within_limit` - {'abs_delta': 832, 'max_abs_delta': 16}
