# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 353 (green)
- Checkpoint path: runs\checkpoints\s2_gate_353_status.md

## Registration Admission

- Registration admission: blocked passed=False blocked=True
- Reference frame: F000004
- Quality gate status: rejected
- Quality gate enforced: True
- Fallback/override: fallback=True allow_quality_rejected_reference=False
- Reason: reference frame failed the quality gate
- Admission rows: total=1 quality_reference_admission=1 quality_rejected=1

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Checks

- PASS: latest_checkpoint_green - {'gate': 353, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- FAIL: registration_reference_admission_not_blocked - {'status': 'blocked', 'blocked': True, 'reference_frame_id': 'F000004', 'quality_gate_status': 'rejected', 'quality_gate_enforced': True, 'reference_selection_fallback': True, 'allow_quality_rejected_reference': False, 'reason': 'reference frame failed the quality gate', 'quality_reference_admission_row_count': 1, 'path': 'runs\\checkpoints\\s2_gate_351_resume_admission_run\\registration_results.json'}
