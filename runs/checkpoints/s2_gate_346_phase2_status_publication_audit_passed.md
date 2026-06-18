# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 346 (green)
- Checkpoint path: runs\checkpoints\s2_gate_346_status.md

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## StackEngine Publication Audit

- Status: passed
- Passed: True
- Recommendation: publication_chain_ready
- Layers/checks: 19/34
- Failed checks: []
- Publish-preflight policy layer: {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Phase2 policy layer: {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Policy checks: raw=True, phase2=True, agreement=True
- Direct runtime layers: raw={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, phase2={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Direct runtime checks: raw=True, phase2=True, agreement=True
- Resident winsorized layers: raw={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, phase2={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Resident winsorized checks: raw=True, phase2=True, agreement=True
- Resident result-contract layers: raw={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, phase2={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Resident result-contract checks: raw=True, phase2=True, agreement=True

## Checks

- PASS: latest_checkpoint_green - {'gate': 346, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: stack_engine_publication_audit_passed - {'status': 'passed', 'passed': True, 'recommendation': 'publication_chain_ready', 'check_count': 34, 'failed_check_count': 0, 'failed_checks': []}
- PASS: stack_engine_publication_audit_policy_chain_passed - {'raw_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: stack_engine_publication_audit_resident_winsorized_chain_passed - {'raw_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: stack_engine_publication_audit_resident_result_contract_chain_passed - {'raw_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: stack_engine_publication_audit_direct_runtime_chain_passed - {'raw_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': []}
