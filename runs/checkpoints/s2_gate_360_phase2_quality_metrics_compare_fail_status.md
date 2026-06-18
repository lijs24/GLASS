# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 359 (green)
- Checkpoint path: runs\checkpoints\s2_gate_359_status.md

## Quality Metrics Compare

- Quality metrics compare: failed passed=False
- Metric counts: baseline=7 candidate=7 rows=7
- Failed checks: count=1 names=['bad_median_ratio_within_limit']
- Threshold failures: count=6 items=[{'bad_median_ratio': 1.4, 'baseline_median': 2.5, 'candidate_median': 3.5, 'metric': 'fwhm_px'}, {'bad_median_ratio': 1.4, 'baseline_median': 0.4, 'candidate_median': 0.56, 'metric': 'eccentricity'}, {'bad_median_ratio': 1.4, 'baseline_median': 25.0, 'candidate_median': 35.0, 'metric': 'background_rms'}, {'bad_median_ratio': 1.4, 'baseline_median': 45.0, 'candidate_median': 32.142857, 'metric': 'snr'}, {'bad_median_ratio': 1.4, 'baseline_median': 800.0, 'candidate_median': 571.428571, 'metric': 'quality_score'}, {'bad_median_ratio': 1.399999, 'baseline_median': 0.8, 'candidate_median': 0.571429, 'metric': 'weight'}]

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Checks

- PASS: latest_checkpoint_green - {'gate': 359, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- FAIL: quality_metrics_compare_passed - {'status': 'failed', 'check_count': 4, 'failed_check_count': 1, 'failed_checks': ['bad_median_ratio_within_limit'], 'baseline_metric_count': 7, 'candidate_metric_count': 7, 'threshold_failure_count': 6, 'path': 'runs\\checkpoints\\s2_gate_359_quality_metrics_compare.json'}
