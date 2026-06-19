# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 382 (green)
- Checkpoint path: C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_382_fixtures\compatible_missing_final_evidence\checkpoints\s2_gate_382_status.md

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
- StackEngine runtime default statuses: matrix-ready=True, matrix-acceptance=passed, matrix-pipeline=passed, default-promotion-ready=True, default-promotion-acceptance=passed, default-promotion-pipeline=passed
- StackEngine runtime default checks: matrix-acceptance=True, matrix-pipeline=True, default-promotion-acceptance=True, default-promotion-pipeline=True, agreement=True
- StackEngine runtime default drift counters: matrix-legacy=0, matrix-failed-outputs=0, default-legacy=0, default-failed-outputs=0
- Direct runtime evidence: matrix-ready=True matrix-source=explicit_resident_artifacts_json matrix-calibration=resident_artifacts_json_fallback matrix-lights=200 default-ready=True default-source=explicit_resident_artifacts_json default-calibration=resident_artifacts_json_fallback default-lights=200
- Direct runtime checks: matrix-acceptance=True, matrix-calibration=True, default-acceptance=True, default-calibration=True, agreement=True
- Release direct publication guard evidence: plan-matrix=True/200, plan-default=True/200, matrix=True/200 source=True count=True check=True, matrix-default=True/200, default=True/200
- Release direct publication guard checks: plan-matrix=True, plan-default=True, plan-matrix-match=True, plan-default-match=True, matrix=True, matrix-default=True, default=True, matrix-default-match=True, matrix-manifest-match=True
- Release quality publication guard evidence: matrix=True/True/passed/passed, matrix-default=True/passed/passed, default=True/True/passed/passed
- Release quality publication guard checks: matrix=True, matrix-default=True, default=True, matrix-default-match=True, matrix-manifest-match=True
- Release quality publication guard final checks: matrix=True, matrix-default=True, default=True, matrix-default-match=True, matrix-manifest-match=True
- Release quality publication guard final evidence: matrix=True/True/None/None, matrix-default=True/True/None/None, default=True/True/None/None
- Resident winsorized sweep statuses: matrix=passed, default-promotion=passed
- Resident winsorized sweep required frame: matrix=200/True, default-promotion=200/True
- Resident winsorized sweep checks: matrix-count=27, default-promotion-count=27, matrix-audit=True, matrix-frame=True, matrix-count-check=True, default-promotion-audit=True, default-promotion-frame=True, default-promotion-match=True
- Resident fastpath handoff: plan-matrix=True/passed/31, matrix=True/passed/31, default-promotion=True/passed/31
- Resident fastpath handoff checks: plan-matrix=True, matrix=True, default-promotion=True, plan-matrix-match=True, matrix-default-match=True
- StackEngine publication audit statuses: matrix=passed/True, default-promotion=passed/True
- StackEngine publication audit chains: matrix-policy=True, matrix-resident-winsorized=True, default-policy=True, default-resident-winsorized=True
- StackEngine publication audit checks: matrix-audit=True, matrix-policy=True, matrix-resident-winsorized=True, default-audit=True, default-policy=True, default-resident-winsorized=True, agreement=True
- Quality metrics compare handoff: matrix=passed/True/0, default-promotion=passed/True/0
- Quality metrics compare checks: matrix=True, default-promotion=True, agreement=True

## Checks

- PASS: latest_checkpoint_green - {'gate': 382, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'Fixture GPU'}
- PASS: windows_publish_preflight_ready - {'status': 'publish_preflight_ready', 'passed': True, 'asset_count': 4, 'package_count': 4, 'primary_package': 'cuda13', 'default_route_check_count': 4, 'failed_checks': []}
- PASS: windows_publish_preflight_rejection_sample_accounting_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_sample_accounting_closure_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_integration_engine_policy_passed - {'matrix_ready': True, 'matrix_acceptance_status': 'passed', 'matrix_pipeline_status': 'passed', 'default_promotion_ready': True, 'default_promotion_acceptance_status': 'passed', 'default_promotion_pipeline_status': 'passed', 'matrix_acceptance_check': True, 'matrix_pipeline_check': True, 'default_promotion_acceptance_check': True, 'default_promotion_pipeline_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_default_contract_ready - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'matrix_default_gap_count': 0, 'default_promotion_default_gap_count': 0, 'phase2_check': True, 'plan_matrix_check': True, 'agreement_check': True, 'matrix_check': True, 'default_promotion_check': True, 'plan_matrix_match_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_runtime_default_passed - {'matrix_ready': True, 'matrix_acceptance_status': 'passed', 'matrix_pipeline_status': 'passed', 'matrix_acceptance_legacy_master_count': 0, 'matrix_pipeline_failed_output_count': 0, 'default_promotion_ready': True, 'default_promotion_acceptance_status': 'passed', 'default_promotion_pipeline_status': 'passed', 'default_promotion_acceptance_legacy_master_count': 0, 'default_promotion_pipeline_failed_output_count': 0, 'matrix_acceptance_check': True, 'matrix_pipeline_check': True, 'default_promotion_acceptance_check': True, 'default_promotion_pipeline_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_direct_runtime_evidence_passed - {'matrix_ready': True, 'matrix_acceptance_source': 'explicit_resident_artifacts_json', 'matrix_acceptance_check_count': 24, 'matrix_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'matrix_pipeline_resident_lights': 200, 'default_promotion_ready': True, 'default_promotion_acceptance_source': 'explicit_resident_artifacts_json', 'default_promotion_acceptance_check_count': 24, 'default_promotion_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'default_promotion_pipeline_resident_lights': 200, 'matrix_acceptance_check': True, 'matrix_pipeline_check': True, 'default_promotion_acceptance_check': True, 'default_promotion_pipeline_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_release_direct_publication_guard_passed - {'github_plan_matrix_ready': True, 'github_plan_matrix_lights': 200, 'github_plan_default_promotion_ready': True, 'github_plan_default_promotion_lights': 200, 'matrix_ready': True, 'matrix_source_ready': True, 'matrix_count_ready': True, 'matrix_check_passed': True, 'matrix_lights': 200, 'matrix_default_promotion_ready': True, 'matrix_default_promotion_lights': 200, 'default_promotion_ready': True, 'default_promotion_lights': 200, 'github_plan_matrix_check': True, 'github_plan_default_promotion_check': True, 'github_plan_matrix_match_check': True, 'github_plan_default_promotion_match_check': True, 'matrix_release_check': True, 'matrix_default_promotion_check': True, 'default_promotion_check': True, 'matrix_default_match_check': True, 'matrix_manifest_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_release_quality_publication_guard_passed - {'present': True, 'matrix_present': True, 'matrix_ready': True, 'matrix_check_passed': True, 'matrix_layers_ready': True, 'matrix_raw_status': 'passed', 'matrix_phase2_status': 'passed', 'matrix_default_ready': True, 'matrix_default_raw_status': 'passed', 'matrix_default_phase2_status': 'passed', 'default_promotion_present': True, 'default_promotion_ready': True, 'default_promotion_check_passed': True, 'default_promotion_layers_ready': True, 'default_promotion_raw_status': 'passed', 'default_promotion_phase2_status': 'passed', 'matrix_check': True, 'matrix_default_check': True, 'default_promotion_check': True, 'matrix_default_match_check': True, 'matrix_manifest_match_check': True, 'final_checks_present': True, 'final_evidence_present': True, 'final_evidence_passed': True, 'release_matrix_check': True, 'release_matrix_default_check': True, 'release_default_promotion_check': True, 'release_matrix_default_match_check': True, 'release_matrix_manifest_match_check': True, 'matrix_final_checks_ready': True, 'matrix_final_checks_match': True, 'matrix_raw_final_checks_ready': None, 'matrix_phase2_final_checks_ready': None, 'matrix_default_final_checks_ready': True, 'matrix_default_final_checks_match': True, 'matrix_default_raw_final_checks_ready': None, 'matrix_default_phase2_final_checks_ready': None, 'default_promotion_final_checks_ready': True, 'default_promotion_final_checks_match': True, 'default_promotion_raw_final_checks_ready': None, 'default_promotion_phase2_final_checks_ready': None, 'failed_checks': []}
- PASS: windows_publish_preflight_resident_winsorized_sweep_passed - {'matrix_status': 'passed', 'matrix_required_frame_count': 200, 'matrix_required_frame_count_passed': True, 'matrix_check_count': 27, 'default_promotion_status': 'passed', 'default_promotion_required_frame_count': 200, 'default_promotion_required_frame_count_passed': True, 'default_promotion_check_count': 27, 'matrix_audit_check': True, 'matrix_required_frame_check': True, 'matrix_check_count_check': True, 'default_promotion_audit_check': True, 'default_promotion_required_frame_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_resident_fastpath_handoff_passed - {'github_plan_matrix_ready': True, 'github_plan_matrix_raw_status': 'passed', 'github_plan_matrix_phase2_status': 'passed', 'github_plan_matrix_raw_check_count': 31, 'matrix_ready': True, 'matrix_raw_status': 'passed', 'matrix_phase2_status': 'passed', 'matrix_raw_check_count': 31, 'default_promotion_ready': True, 'default_promotion_raw_status': 'passed', 'default_promotion_phase2_status': 'passed', 'default_promotion_raw_check_count': 31, 'github_plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'github_plan_matrix_match_check': True, 'matrix_default_promotion_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_publication_audit_passed - {'matrix_status': 'passed', 'matrix_ready': True, 'matrix_policy_agreement': True, 'matrix_resident_winsorized_agreement': True, 'default_promotion_status': 'passed', 'default_promotion_ready': True, 'default_promotion_policy_agreement': True, 'default_promotion_resident_winsorized_agreement': True, 'matrix_audit_check': True, 'matrix_policy_check': True, 'matrix_resident_winsorized_check': True, 'default_promotion_audit_check': True, 'default_promotion_policy_check': True, 'default_promotion_resident_winsorized_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_quality_metrics_compare_passed - {'present': True, 'matrix_present': True, 'matrix_ready': True, 'matrix_status': 'passed', 'matrix_failed_check_count': 0, 'default_promotion_present': True, 'default_promotion_ready': True, 'default_promotion_status': 'passed', 'default_promotion_failed_check_count': 0, 'matrix_check': True, 'default_promotion_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_resident_result_contract_handoff_passed - {'github_plan_matrix_ready': True, 'github_plan_matrix_status': 'passed', 'github_plan_matrix_phase2_check': True, 'github_plan_matrix_required_count': 1, 'github_plan_matrix_failed_count': 0, 'matrix_ready': True, 'matrix_status': 'passed', 'matrix_phase2_check': True, 'matrix_required_count': 1, 'matrix_failed_count': 0, 'default_promotion_ready': True, 'default_promotion_status': 'passed', 'default_promotion_phase2_check': True, 'default_promotion_required_count': 1, 'default_promotion_failed_count': 0, 'github_plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'github_plan_matrix_match_check': True, 'matrix_default_promotion_match_check': True, 'failed_checks': []}
