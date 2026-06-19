# Resident Rejection Sample Audit

- Status: `attention_required`
- Passed: `False`
- Recommendation: `target_resident_registration_warp_input_parity`
- Evaluation region: `compare_region`
- Tile size: `2048`

## Evaluation Deltas

- Rejected sample delta: `42`
- Coverage sample delta: `-42`
- Pre-rejection sample delta: `0`
- Same-pre-rejection abs rejected delta: `1376`

## Attribution Evidence

- Rejection input audit: `runs\checkpoints\s2_gate_428_rejection_input_audit.json`
- Exact-input parity proven: `True`
- CUDA exact-input status: `completed`
- CUDA exact-input passed: `True`
- Resident input delta attributed: `True`
- Resident output attribution status: `resident_registration_warp_input_delta`

## Global Deltas

- Rejected sample delta: `93`
- Coverage sample delta: `2218`
- Pre-rejection sample delta: `2311`
- Same-pre-rejection abs rejected delta: `1444`
- Rejection mismatch pixels: `1710`
- DQ mismatch pixels: `5936`

## Compare Region

### inside_compare_region

- Rejected sample delta: `42`
- Abs rejected sample delta: `1376`
- Coverage sample delta: `-42`
- Pre-rejection sample delta: `0`
- Rejection mismatch pixels: `1349`

### outside_compare_region

- Rejected sample delta: `51`
- Abs rejected sample delta: `393`
- Coverage sample delta: `2260`
- Pre-rejection sample delta: `2311`
- Rejection mismatch pixels: `361`

## Top Tiles

| y0 | y1 | x0 | x1 | rejected delta | abs rejected | coverage delta | pre-rejection delta | mismatch px |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 512 | 0 | 512 | 93 | 1769 | 2218 | 2311 | 1710 |

## Checks

- PASS: `cpu_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\low_rejection_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\high_rejection_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_414_runtime_validation_cpu\\integration\\dq_map_H.fits', 'exists': True}}}
- PASS: `resident_maps_present` - {'maps': {'coverage': {'path_key': 'coverage_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_428_iterative_refine_refF16_cuda_hardened\\integration\\resident_coverage_map_H.fits', 'exists': True}, 'low_rejection': {'path_key': 'low_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_428_iterative_refine_refF16_cuda_hardened\\integration\\resident_low_rejection_map_H.fits', 'exists': True}, 'high_rejection': {'path_key': 'high_rejection_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_428_iterative_refine_refF16_cuda_hardened\\integration\\resident_high_rejection_map_H.fits', 'exists': True}, 'dq': {'path_key': 'dq_map_path', 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_428_iterative_refine_refF16_cuda_hardened\\integration\\resident_dq_map_H.fits', 'exists': True}}}
- PASS: `map_shapes_match` - {'shapes': {'cpu_coverage': [512, 512], 'cpu_low_rejection': [512, 512], 'cpu_high_rejection': [512, 512], 'cpu_dq': [512, 512], 'resident_coverage': [512, 512], 'resident_low_rejection': [512, 512], 'resident_high_rejection': [512, 512], 'resident_dq': [512, 512]}, 'shape_match': True, 'shape': [512, 512]}
- FAIL: `rejected_sample_delta_within_limit` - {'delta': 42, 'max_abs_delta': 0, 'evaluation_region': 'compare_region'}
- PASS: `pre_rejection_sample_delta_within_limit` - {'delta': 0, 'max_abs_delta': 0, 'evaluation_region': 'compare_region', 'note': 'pre-rejection sample delta compares coverage+low+high maps and identifies geometric/warp/DQ input-sample drift before rejection.'}
- FAIL: `same_pre_rejection_semantic_delta_within_limit` - {'abs_delta': 1376, 'max_abs_delta': 0, 'evaluation_region': 'compare_region'}
