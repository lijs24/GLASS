# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 359 (green)
- Checkpoint path: runs\checkpoints\s2_gate_359_status.md

## Quality Metrics Compare

- Quality metrics compare: passed passed=True
- Metric counts: baseline=7 candidate=7 rows=7
- Failed checks: count=0 names=[]
- Threshold failures: count=0 items=[]

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
- PASS: quality_metrics_compare_passed - {'status': 'passed', 'check_count': 3, 'failed_check_count': 0, 'failed_checks': [], 'baseline_metric_count': 7, 'candidate_metric_count': 7, 'threshold_failure_count': 0, 'path': 'runs\\checkpoints\\s2_gate_360_quality_metrics_compare_pass.json'}
