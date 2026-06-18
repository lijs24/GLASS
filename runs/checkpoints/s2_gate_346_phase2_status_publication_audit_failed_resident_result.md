# GLASS Phase 2 Status

- Status: attention_required
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

- Status: blocked
- Passed: False
- Recommendation: fix_stack_engine_publication_chain
- Layers/checks: 19/34
- Failed checks: ['publish_preflight_resident_result_contract_ready', 'phase2_publish_preflight_resident_result_contract_ready']
- Publish-preflight policy layer: {'status': 'blocked', 'ready': True, 'gap_count': None}
- Phase2 policy layer: {'status': 'blocked', 'ready': True, 'gap_count': None}
- Policy checks: raw=True, phase2=True, agreement=True
- Direct runtime layers: raw={'status': 'blocked', 'ready': True, 'gap_count': None}, phase2={'status': 'blocked', 'ready': True, 'gap_count': None}
- Direct runtime checks: raw=True, phase2=True, agreement=True
- Resident winsorized layers: raw={'status': 'blocked', 'ready': True, 'gap_count': None}, phase2={'status': 'blocked', 'ready': True, 'gap_count': None}
- Resident winsorized checks: raw=True, phase2=True, agreement=True
- Resident result-contract layers: raw={'status': 'blocked', 'ready': False, 'gap_count': None}, phase2={'status': 'blocked', 'ready': False, 'gap_count': None}
- Resident result-contract checks: raw=False, phase2=False, agreement=True

## Checks

- PASS: latest_checkpoint_green - {'gate': 346, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- FAIL: stack_engine_publication_audit_passed - {'status': 'blocked', 'passed': False, 'recommendation': 'fix_stack_engine_publication_chain', 'check_count': 34, 'failed_check_count': 2, 'failed_checks': ['publish_preflight_resident_result_contract_ready', 'phase2_publish_preflight_resident_result_contract_ready']}
- PASS: stack_engine_publication_audit_policy_chain_passed - {'raw_layer': {'status': 'blocked', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'blocked', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': ['publish_preflight_resident_result_contract_ready', 'phase2_publish_preflight_resident_result_contract_ready']}
- PASS: stack_engine_publication_audit_resident_winsorized_chain_passed - {'raw_layer': {'status': 'blocked', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'blocked', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': ['publish_preflight_resident_result_contract_ready', 'phase2_publish_preflight_resident_result_contract_ready']}
- FAIL: stack_engine_publication_audit_resident_result_contract_chain_passed - {'raw_layer': {'status': 'blocked', 'ready': False, 'gap_count': None}, 'phase2_layer': {'status': 'blocked', 'ready': False, 'gap_count': None}, 'raw_ready_check': False, 'phase2_ready_check': False, 'agreement_check': True, 'failed_checks': ['publish_preflight_resident_result_contract_ready', 'phase2_publish_preflight_resident_result_contract_ready']}
- PASS: stack_engine_publication_audit_direct_runtime_chain_passed - {'raw_layer': {'status': 'blocked', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'blocked', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': ['publish_preflight_resident_result_contract_ready', 'phase2_publish_preflight_resident_result_contract_ready']}
