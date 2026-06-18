# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 357 (green)
- Checkpoint path: runs\checkpoints\s2_gate_357_status.md

## Quality Saturation

- Quality saturation: passed passed=True
- Frames: total=2 saturated=1 saturation_rejected=0
- Saturation fraction: max=0.00878906 mean=0.00439453 policy=0.005
- Saturation threshold/source: level=5000.0 sources=['threshold']
- Worst frame: F_SAT
- Rejected frames: []

## Quality Metrics

- Quality metrics: not_available metrics=0 frames=2

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Checks

- PASS: latest_checkpoint_green - {'gate': 357, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: quality_saturation_no_rejections - {'status': 'passed', 'frame_count': 2, 'saturated_frame_count': 1, 'quality_gate_saturation_rejected_count': 0, 'max_saturation_fraction': 0.00878906, 'max_saturation_fraction_policy': 0.005, 'worst_frame_id': 'F_SAT', 'rejected_frame_ids': [], 'path': 'runs\\checkpoints\\s2_gate_356_quality_saturation_pass_frame_quality.json'}
- FAIL: quality_metric_summary_available - {'status': 'not_available', 'frame_count': 2, 'metric_count': 0, 'metrics': [], 'path': 'runs\\checkpoints\\s2_gate_356_quality_saturation_pass_frame_quality.json'}
