# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 288 (green)
- Checkpoint path: GATE287_FIXTURE\blocked\s2_gate_288_status.md

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: Fixture GPU
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## StackEngine Publication Audit

- Status: blocked
- Passed: False
- Recommendation: fix_stack_engine_publication_chain
- Layers/checks: 8/10
- Failed checks: ['publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_matches_publish_preflight']
- Publish-preflight policy layer: {'status': 'blocked', 'ready': False, 'gap_count': None}
- Phase2 policy layer: {'status': 'blocked', 'ready': False, 'gap_count': None}
- Policy checks: raw=False, phase2=False, agreement=False
- Resident winsorized layers: raw={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, phase2={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Resident winsorized checks: raw=True, phase2=True, agreement=True

## Checks

- PASS: latest_checkpoint_green - {'gate': 288, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'Fixture GPU'}
- FAIL: stack_engine_publication_audit_passed - {'status': 'blocked', 'passed': False, 'recommendation': 'fix_stack_engine_publication_chain', 'check_count': 10, 'failed_check_count': 3, 'failed_checks': ['publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_matches_publish_preflight']}
- FAIL: stack_engine_publication_audit_policy_chain_passed - {'raw_layer': {'status': 'blocked', 'ready': False, 'gap_count': None}, 'phase2_layer': {'status': 'blocked', 'ready': False, 'gap_count': None}, 'raw_ready_check': False, 'phase2_ready_check': False, 'agreement_check': False, 'failed_checks': ['publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_matches_publish_preflight']}
- PASS: stack_engine_publication_audit_resident_winsorized_chain_passed - {'raw_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': ['publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_ready', 'phase2_publish_preflight_integration_engine_policy_matches_publish_preflight']}
