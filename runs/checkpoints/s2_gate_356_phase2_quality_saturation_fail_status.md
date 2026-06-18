# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 355 (green)
- Checkpoint path: runs\checkpoints\s2_gate_355_status.md

## Quality Saturation

- Quality saturation: attention_required passed=False
- Frames: total=2 saturated=1 saturation_rejected=1
- Saturation fraction: max=0.00878906 mean=0.00439453 policy=0.005
- Saturation threshold/source: level=5000.0 sources=['threshold']
- Worst frame: bad
- Rejected frames: ['bad']

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Checks

- PASS: latest_checkpoint_green - {'gate': 355, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- FAIL: quality_saturation_no_rejections - {'status': 'attention_required', 'frame_count': 2, 'saturated_frame_count': 1, 'quality_gate_saturation_rejected_count': 1, 'max_saturation_fraction': 0.00878906, 'max_saturation_fraction_policy': 0.005, 'worst_frame_id': 'bad', 'rejected_frame_ids': ['bad'], 'path': 'runs\\checkpoints\\s2_gate_354_quality_saturation_run\\frame_quality.json'}
