# Resident Rejection Sample Audit

- Status: `attention_required`
- Passed: `False`
- Recommendation: `fix_resident_geometric_coverage_or_transform`
- Tile size: `64`

## Global Deltas

- Rejected sample delta: `117`
- Coverage sample delta: `10085`
- Pre-rejection sample delta: `10202`
- Same-pre-rejection abs rejected delta: `795`
- Rejection mismatch pixels: `1132`
- DQ mismatch pixels: `4375`

## Compare Region

### inside_compare_region

- Rejected sample delta: `-16`
- Abs rejected sample delta: `760`
- Coverage sample delta: `16`
- Pre-rejection sample delta: `0`
- Rejection mismatch pixels: `747`

### outside_compare_region

- Rejected sample delta: `133`
- Abs rejected sample delta: `435`
- Coverage sample delta: `10069`
- Pre-rejection sample delta: `10202`
- Rejection mismatch pixels: `385`

## Top Tiles

| y0 | y1 | x0 | x1 | rejected delta | abs rejected | coverage delta | pre-rejection delta | mismatch px |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 448 | 512 | 0 | 64 | 40 | 58 | 1017 | 1057 | 54 |
| 448 | 512 | 128 | 192 | 2 | 50 | 702 | 704 | 44 |
| 448 | 512 | 448 | 512 | 20 | 46 | 745 | 765 | 43 |
| 384 | 448 | 0 | 64 | 11 | 45 | 373 | 384 | 43 |
| 448 | 512 | 256 | 320 | 10 | 42 | 694 | 704 | 37 |
| 192 | 256 | 0 | 64 | 12 | 40 | 372 | 384 | 33 |
| 448 | 512 | 384 | 448 | 5 | 37 | 699 | 704 | 32 |
| 448 | 512 | 320 | 384 | 10 | 34 | 694 | 704 | 31 |
| 448 | 512 | 192 | 256 | 3 | 33 | 701 | 704 | 31 |
| 128 | 192 | 0 | 64 | 1 | 33 | 383 | 384 | 31 |
| 256 | 320 | 0 | 64 | -1 | 33 | 385 | 384 | 28 |
| 64 | 128 | 0 | 64 | 9 | 31 | 375 | 384 | 29 |

## Checks

- PASS: `cpu_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\low_rejection_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\high_rejection_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\dq_map_H.fits', 'exists': True}}}
- PASS: `resident_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_420_no_pixel_refine_refF16_cuda_hardened\\integration\\resident_coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_420_no_pixel_refine_refF16_cuda_hardened\\integration\\resident_low_rejection_map_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_420_no_pixel_refine_refF16_cuda_hardened\\integration\\resident_high_rejection_map_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_420_no_pixel_refine_refF16_cuda_hardened\\integration\\resident_dq_map_H.fits', 'exists': True}}}
- PASS: `map_shapes_match` - {'shapes': {'cpu_coverage': [512, 512], 'cpu_low_rejection': [512, 512], 'cpu_high_rejection': [512, 512], 'cpu_dq': [512, 512], 'resident_coverage': [512, 512], 'resident_low_rejection': [512, 512], 'resident_high_rejection': [512, 512], 'resident_dq': [512, 512]}, 'shape_match': True, 'shape': [512, 512]}
- FAIL: `rejected_sample_delta_within_limit` - {'delta': 117, 'max_abs_delta': 64}
- FAIL: `pre_rejection_sample_delta_within_limit` - {'delta': 10202, 'max_abs_delta': 0, 'note': 'pre-rejection sample delta compares coverage+low+high maps and identifies geometric/warp/DQ input-sample drift before rejection.'}
- FAIL: `same_pre_rejection_semantic_delta_within_limit` - {'abs_delta': 795, 'max_abs_delta': 16}
