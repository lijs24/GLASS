# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 298 (Green)
- Checkpoint path: runs\checkpoints\s2_gate_298_status.md

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Windows Publish Preflight

- Preflight status: publish_preflight_ready
- Passed: True
- Recommendation: publish_release_bundle
- Release tag: v0.1.0-test
- Assets/packages: 2/2
- Primary package: cuda13
- Try order: ['cuda13', 'cpu']
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
- StackEngine runtime default statuses: matrix-ready=True, matrix-acceptance=passed, matrix-pipeline=passed, default-promotion-ready=True, default-promotion-acceptance=passed, default-promotion-pipeline=passed
- StackEngine runtime default checks: matrix-acceptance=True, matrix-pipeline=True, default-promotion-acceptance=True, default-promotion-pipeline=True, agreement=True
- StackEngine runtime default drift counters: matrix-legacy=0, matrix-failed-outputs=0, default-legacy=0, default-failed-outputs=0
- Resident winsorized sweep statuses: matrix=passed, default-promotion=passed
- Resident winsorized sweep required frame: matrix=200/True, default-promotion=200/True
- Resident winsorized sweep checks: matrix-count=27, default-promotion-count=27, matrix-audit=True, matrix-frame=True, matrix-count-check=True, default-promotion-audit=True, default-promotion-frame=True, default-promotion-match=True
- StackEngine publication audit statuses: matrix=passed/True, default-promotion=passed/True
- StackEngine publication audit chains: matrix-policy=True, matrix-resident-winsorized=True, default-policy=True, default-resident-winsorized=True
- StackEngine publication audit checks: matrix-audit=True, matrix-policy=True, matrix-resident-winsorized=True, default-audit=True, default-policy=True, default-resident-winsorized=True, agreement=True

## StackEngine Default Contract

- Status: passed
- Passed: True
- Scope: all
- Expected integration engine: cuda_resident_stack
- Adoption recommendation: stack_engine_default_ready
- Adoption surfaces: 4 ready=4
- StackEngine/resident surfaces: 0/4
- Phase 2 default gaps: 0
- Default promotion: ready ready=True blockers=0

## Checks

- PASS: latest_checkpoint_green - {'gate': 298, 'status': 'Green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: windows_publish_preflight_ready - {'status': 'publish_preflight_ready', 'passed': True, 'asset_count': 2, 'package_count': 2, 'primary_package': 'cuda13', 'default_route_check_count': 4, 'failed_checks': []}
- PASS: windows_publish_preflight_rejection_sample_accounting_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_sample_accounting_closure_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_integration_engine_policy_passed - {'matrix_ready': True, 'matrix_acceptance_status': 'passed', 'matrix_pipeline_status': 'passed', 'default_promotion_ready': True, 'default_promotion_acceptance_status': 'passed', 'default_promotion_pipeline_status': 'passed', 'matrix_acceptance_check': True, 'matrix_pipeline_check': True, 'default_promotion_acceptance_check': True, 'default_promotion_pipeline_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_default_contract_ready - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'matrix_default_gap_count': 0, 'default_promotion_default_gap_count': 0, 'phase2_check': True, 'plan_matrix_check': True, 'agreement_check': True, 'matrix_check': True, 'default_promotion_check': True, 'plan_matrix_match_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_runtime_default_passed - {'matrix_ready': True, 'matrix_acceptance_status': 'passed', 'matrix_pipeline_status': 'passed', 'matrix_acceptance_legacy_master_count': 0, 'matrix_pipeline_failed_output_count': 0, 'default_promotion_ready': True, 'default_promotion_acceptance_status': 'passed', 'default_promotion_pipeline_status': 'passed', 'default_promotion_acceptance_legacy_master_count': 0, 'default_promotion_pipeline_failed_output_count': 0, 'matrix_acceptance_check': True, 'matrix_pipeline_check': True, 'default_promotion_acceptance_check': True, 'default_promotion_pipeline_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_resident_winsorized_sweep_passed - {'matrix_status': 'passed', 'matrix_required_frame_count': 200, 'matrix_required_frame_count_passed': True, 'matrix_check_count': 27, 'default_promotion_status': 'passed', 'default_promotion_required_frame_count': 200, 'default_promotion_required_frame_count_passed': True, 'default_promotion_check_count': 27, 'matrix_audit_check': True, 'matrix_required_frame_check': True, 'matrix_check_count_check': True, 'default_promotion_audit_check': True, 'default_promotion_required_frame_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_publication_audit_passed - {'matrix_status': 'passed', 'matrix_ready': True, 'matrix_policy_agreement': True, 'matrix_resident_winsorized_agreement': True, 'default_promotion_status': 'passed', 'default_promotion_ready': True, 'default_promotion_policy_agreement': True, 'default_promotion_resident_winsorized_agreement': True, 'matrix_audit_check': True, 'matrix_policy_check': True, 'matrix_resident_winsorized_check': True, 'default_promotion_audit_check': True, 'default_promotion_policy_check': True, 'default_promotion_resident_winsorized_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: stack_engine_default_contract_ready - {'status': 'passed', 'passed': True, 'scope': 'all', 'expected_integration_engine': 'cuda_resident_stack', 'adoption_recommendation': 'stack_engine_default_ready', 'adoption_gap_count': 0, 'default_promotion_ready': True, 'default_promotion_status': 'ready', 'default_promotion_blocker_count': 0, 'failed_checks': [], 'blockers': []}
