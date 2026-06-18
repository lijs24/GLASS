# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 285 (green)
- Checkpoint path: GATE285_FIXTURE\checkpoints\s2_gate_285_status.md

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: Fixture GPU
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Windows Publish Preflight

- Preflight status: publish_preflight_ready
- Passed: True
- Recommendation: publish_release_bundle
- Release tag: v0.1.0-test
- Assets/packages: 4/4
- Primary package: cuda13
- Try order: ['cuda13', 'cuda12', 'cuda11', 'cpu']
- Default promotion: default_promotion_ready
- Default route checks: 4
- Default route speedup vs reference: 28.75
- Rejection sample accounting statuses: phase2=passed, plan-matrix=passed, matrix=passed, default-promotion=passed
- Rejection sample accounting checks: phase2=True, plan-matrix=True, matrix=True, default-promotion=True, matrix-match=True
- Sample accounting closure statuses: phase2=passed, plan-matrix=passed, matrix=passed, default-promotion=passed
- Sample accounting closure checks: phase2=True, plan-matrix=True, matrix=True, default-promotion=True, matrix-match=True
- Integration engine policy statuses: matrix-ready=True, matrix-acceptance=passed, matrix-pipeline=passed, default-promotion-ready=True, default-promotion-acceptance=passed, default-promotion-pipeline=passed
- Integration engine policy checks: matrix-acceptance=True, matrix-pipeline=True, default-promotion-acceptance=True, default-promotion-pipeline=True, agreement=True
- StackEngine default contract statuses: phase2=passed, plan-matrix=passed, matrix=passed, default-promotion=passed
- StackEngine default contract checks: phase2=True, plan-matrix=True, agreement=True, matrix=True, default-promotion=True, plan-matrix-match=True, default-promotion-match=True
- StackEngine default gaps: matrix=0, default-promotion=0
- Resident winsorized sweep statuses: matrix=passed, default-promotion=passed
- Resident winsorized sweep required frame: matrix=200/True, default-promotion=200/True
- Resident winsorized sweep checks: matrix-count=27, default-promotion-count=27, matrix-audit=True, matrix-frame=True, matrix-count-check=True, default-promotion-audit=True, default-promotion-frame=True, default-promotion-match=True

## Checks

- PASS: latest_checkpoint_green - {'gate': 285, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'Fixture GPU'}
- PASS: windows_publish_preflight_ready - {'status': 'publish_preflight_ready', 'passed': True, 'asset_count': 4, 'package_count': 4, 'primary_package': 'cuda13', 'default_route_check_count': 4, 'failed_checks': []}
- PASS: windows_publish_preflight_rejection_sample_accounting_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_sample_accounting_closure_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_integration_engine_policy_passed - {'matrix_ready': True, 'matrix_acceptance_status': 'passed', 'matrix_pipeline_status': 'passed', 'default_promotion_ready': True, 'default_promotion_acceptance_status': 'passed', 'default_promotion_pipeline_status': 'passed', 'matrix_acceptance_check': True, 'matrix_pipeline_check': True, 'default_promotion_acceptance_check': True, 'default_promotion_pipeline_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_default_contract_ready - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'matrix_default_gap_count': 0, 'default_promotion_default_gap_count': 0, 'phase2_check': True, 'plan_matrix_check': True, 'agreement_check': True, 'matrix_check': True, 'default_promotion_check': True, 'plan_matrix_match_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_resident_winsorized_sweep_passed - {'matrix_status': 'passed', 'matrix_required_frame_count': 200, 'matrix_required_frame_count_passed': True, 'matrix_check_count': 27, 'default_promotion_status': 'passed', 'default_promotion_required_frame_count': 200, 'default_promotion_required_frame_count_passed': True, 'default_promotion_check_count': 27, 'matrix_audit_check': True, 'matrix_required_frame_check': True, 'matrix_check_count_check': True, 'default_promotion_audit_check': True, 'default_promotion_required_frame_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
