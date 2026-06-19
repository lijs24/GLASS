# Resident Rejection Sample Audit

- Status: `attention_required`
- Passed: `False`
- Recommendation: `fix_resident_winsorized_rejection_semantics`
- Evaluation region: `compare_region`
- Tile size: `2048`

## Evaluation Deltas

- Rejected sample delta: `-28`
- Coverage sample delta: `28`
- Pre-rejection sample delta: `0`
- Same-pre-rejection abs rejected delta: `706`

## Attribution Evidence

- Rejection input audit: `runs\checkpoints\s2_gate_429_global_mean_rejection_input_audit.json`
- Exact-input parity proven: `False`
- CUDA exact-input status: `None`
- CUDA exact-input passed: `None`
- Resident input delta attributed: `None`
- Resident output attribution status: `None`

## Global Deltas

- Rejected sample delta: `3`
- Coverage sample delta: `1524`
- Pre-rejection sample delta: `1527`
- Same-pre-rejection abs rejected delta: `738`
- Rejection mismatch pixels: `943`
- DQ mismatch pixels: `5796`

## Compare Region

### inside_compare_region

- Rejected sample delta: `-28`
- Abs rejected sample delta: `706`
- Coverage sample delta: `28`
- Pre-rejection sample delta: `0`
- Rejection mismatch pixels: `694`

### outside_compare_region

- Rejected sample delta: `31`
- Abs rejected sample delta: `269`
- Coverage sample delta: `1496`
- Pre-rejection sample delta: `1527`
- Rejection mismatch pixels: `249`

## Top Tiles

| y0 | y1 | x0 | x1 | rejected delta | abs rejected | coverage delta | pre-rejection delta | mismatch px |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 512 | 0 | 512 | 3 | 975 | 1524 | 1527 | 943 |

## Checks

- PASS: `cpu_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\low_rejection_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\high_rejection_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\dq_map_H.fits', 'exists': True}}}
- PASS: `resident_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_429_global_mean_centroid_refF16_cuda_hardened\\integration\\resident_coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_429_global_mean_centroid_refF16_cuda_hardened\\integration\\resident_low_rejection_map_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_429_global_mean_centroid_refF16_cuda_hardened\\integration\\resident_high_rejection_map_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_429_global_mean_centroid_refF16_cuda_hardened\\integration\\resident_dq_map_H.fits', 'exists': True}}}
- PASS: `map_shapes_match` - {'shapes': {'cpu_coverage': [512, 512], 'cpu_low_rejection': [512, 512], 'cpu_high_rejection': [512, 512], 'cpu_dq': [512, 512], 'resident_coverage': [512, 512], 'resident_low_rejection': [512, 512], 'resident_high_rejection': [512, 512], 'resident_dq': [512, 512]}, 'shape_match': True, 'shape': [512, 512]}
- FAIL: `rejected_sample_delta_within_limit` - {'delta': -28, 'max_abs_delta': 0, 'evaluation_region': 'compare_region'}
- PASS: `pre_rejection_sample_delta_within_limit` - {'delta': 0, 'max_abs_delta': 0, 'evaluation_region': 'compare_region', 'note': 'pre-rejection sample delta compares coverage+low+high maps and identifies geometric/warp/DQ input-sample drift before rejection.'}
- FAIL: `same_pre_rejection_semantic_delta_within_limit` - {'abs_delta': 706, 'max_abs_delta': 0, 'evaluation_region': 'compare_region'}
