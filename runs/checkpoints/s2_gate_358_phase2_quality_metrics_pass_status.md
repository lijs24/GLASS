# GLASS Phase 2 Status

- Status: green
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

- Quality metrics: passed metrics=7 frames=2
- star_count: median=105.0 mean=105.0 worst=F_SAT(90.0) bad_direction=low
- fwhm_px: median=3.95 mean=3.95 worst=F_SAT(5.8) bad_direction=high
- eccentricity: median=0.375 mean=0.375 worst=F_SAT(0.44) bad_direction=high
- background_rms: median=21.0 mean=21.0 worst=F_SAT(24.0) bad_direction=high
- snr: median=44.0 mean=44.0 worst=F_SAT(33.0) bad_direction=low
- quality_score: median=710.0 mean=710.0 worst=F_SAT(420.0) bad_direction=low
- weight: median=0.71 mean=0.71 worst=F_SAT(0.42) bad_direction=low

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
- PASS: quality_saturation_no_rejections - {'status': 'passed', 'frame_count': 2, 'saturated_frame_count': 1, 'quality_gate_saturation_rejected_count': 0, 'max_saturation_fraction': 0.00878906, 'max_saturation_fraction_policy': 0.005, 'worst_frame_id': 'F_SAT', 'rejected_frame_ids': [], 'path': 'runs\\checkpoints\\s2_gate_358_quality_metrics_frame_quality.json'}
- PASS: quality_metric_summary_available - {'status': 'passed', 'frame_count': 2, 'metric_count': 7, 'metrics': ['star_count', 'fwhm_px', 'eccentricity', 'background_rms', 'snr', 'quality_score', 'weight'], 'path': 'runs\\checkpoints\\s2_gate_358_quality_metrics_frame_quality.json'}
