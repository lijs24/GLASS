# GLASS Default Promotion Manifest

- Status: `blocked`
- Recommendation: `fix_default_blockers`
- Passed: `False`
- Default memory mode candidate: `resident`
- Fallback memory mode: `tile`
- Runtime preset: `throughput-v1`
- Integration engine: `cuda_resident_stack`

## Runtime Evidence

- Runs: `3`
- Best: `repeat02` `22.6` s
- Slowest: `23.8` s
- Slowest/best ratio: `1.053`

## Default Route Evidence

- Present: `True`
- Status: `passed`
- Passed: `True`
- Route contract passed: `True`
- Route check count: `4`
- Route failed checks: `[]`
- Speedup vs reference: `28.75`
- Rejection sample accounting: `passed`
- Sample accounting closure: `passed`
- Acceptance integration engine policy: `passed`
- Pipeline integration engine policy: `passed`
- Integration engine policy ready: `True`

## StackEngine Default Contract

- Present: `True`
- Status: `passed`
- Ready: `True`
- Phase2 check passed: `True`
- Scope: `all`
- Adoption recommendation: `stack_engine_default_ready`
- Default gap count: `0`
- Default promotion: `ready` ready=`True` blockers=`0`

## Resident Winsorized Sweep

- Present: `True`
- Status: `passed`
- Passed: `True`
- Phase2 check passed: `True`
- Check count: `27`
- Required frame count: `200`
- Required frame count passed: `True`
- Required frame master RMS: `2.3e-05`
- Required frame hardened CUDA seconds: `0.0012`

## StackEngine Publication Audit

- Present: `True`
- Status: `blocked`
- Passed: `False`
- Ready: `False`
- Phase2 audit check passed: `False`
- Failed checks: `['stack_engine_publication_audit_passed', 'stack_engine_publication_audit_policy_chain_passed']`
- Policy chain: raw=`False` phase2=`False` agreement=`False` phase2-check=`False`
- Resident winsorized chain: raw=`True` phase2=`True` agreement=`True` phase2-check=`True`

## Release Machine

- Doctor present: `False`
- CUDA available: `None`
- Native extension loaded: `None`
- GPU: `None`
- Primary package: `None`
- Try order: ``

## Checks

- PASS: `release_decision_artifact_type` - {'actual': 'release_promotion_decision', 'required': 'release_promotion_decision'}
- PASS: `phase2_status_artifact_type` - {'actual': 'glass_phase2_status', 'required': 'glass_phase2_status'}
- FAIL: `phase2_status_green` - {'status': 'attention_required', 'passed': False}
- PASS: `latest_checkpoint_green` - {'gate': 252, 'status': 'green', 'green': True}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'status': 'default_change_ready'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `phase2_embeds_same_release_decision` - {'input': 'GATE288_FIXTURE\\failed_policy\\release_decision.json', 'phase2_release_decision_path': 'GATE288_FIXTURE\\failed_policy\\release_decision.json'}
- PASS: `phase2_release_decision_default_change_ready` - {'actual': True}
- PASS: `phase2_release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `default_route_acceptance_present` - {'path': 'C:/glass_runs/run/default_route_acceptance.json', 'status': 'passed'}
- PASS: `default_route_acceptance_passed` - {'status': 'passed', 'passed': True, 'acceptance_passed': True}
- PASS: `default_route_acceptance_route_contract_passed` - {'route_contract_passed': True, 'route_failed_checks': []}
- PASS: `default_route_acceptance_route_check_count` - {'actual': 4, 'required_min': 4}
- PASS: `runtime_repeat_present` - {'present': True, 'recommendation': 'best_observed:repeat02'}
- PASS: `runtime_repeat_count` - {'actual': 3, 'required_min': 3}
- PASS: `runtime_repeat_ratio_within_bound` - {'actual': 1.053, 'required_max': 1.25}
- PASS: `pipeline_contract_passed` - {'status': 'passed', 'passed': True}
- PASS: `pipeline_dq_contract_passed` - {'actual': True}
- PASS: `pipeline_stack_and_resident_result_contracts_passed` - {'stack': True, 'resident': True}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_maps_match_dq` - {'dq': True, 'coverage': True, 'rejection': True}
- PASS: `pipeline_rejection_sample_accounting_passed` - {'check': True, 'status': 'passed', 'failed_count': 0, 'failed_items': []}
- PASS: `pipeline_sample_accounting_closure_passed` - {'check': True, 'status': 'passed', 'present_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: `acceptance_integration_engine_policy_handoff_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `pipeline_integration_engine_policy_default_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'default_engine_policy': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `phase2_stack_engine_default_contract_ready` - {'present': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'expected_integration_engine': 'stack_engine_cpu', 'adoption_recommendation': 'stack_engine_default_ready', 'adoption_gap_count': 0, 'default_promotion_ready': True, 'default_promotion_status': 'ready', 'default_promotion_blocker_count': 0, 'default_promotion_blockers': []}
- PASS: `resident_calibration_artifact_present` - {'actual': True}
- PASS: `resident_light_count` - {'actual': 200, 'required_min': 200}
- PASS: `resident_winsorized_sweep_audit_passed` - {'present': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_checks': []}
- PASS: `resident_winsorized_sweep_required_frame_passed` - {'actual_frame_count': 200, 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3e-05, 'required_frame_master_max_abs': 6.1e-05}
- PASS: `resident_winsorized_sweep_check_count` - {'actual': 27, 'required_min': 27, 'failed_check_count': 0}
- FAIL: `stack_engine_publication_audit_passed` - {'present': True, 'status': 'blocked', 'passed': False, 'phase2_check_passed': False, 'failed_checks': ['stack_engine_publication_audit_passed', 'stack_engine_publication_audit_policy_chain_passed']}
- FAIL: `stack_engine_publication_policy_chain_passed` - {'publish_preflight_policy_ready': False, 'phase2_policy_ready': False, 'policy_agreement': False, 'phase2_check_passed': False, 'publish_preflight_layer': {'ready': False, 'status': 'blocked'}, 'phase2_layer': {'ready': False, 'status': 'blocked'}}
- PASS: `stack_engine_publication_resident_winsorized_chain_passed` - {'publish_preflight_resident_winsorized_ready': True, 'phase2_resident_winsorized_ready': True, 'resident_winsorized_agreement': True, 'phase2_check_passed': True, 'publish_preflight_layer': {'ready': True, 'status': 'publish_preflight_ready'}, 'phase2_layer': {'ready': True, 'status': 'publish_preflight_ready'}}
- PASS: `default_memory_mode_candidate` - {'actual': 'resident', 'required': 'resident'}
- PASS: `fallback_memory_mode_preserved` - {'actual': 'tile', 'required': 'tile'}
- PASS: `default_runtime_preset_candidate` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `integration_engine_candidate` - {'actual': 'cuda_resident_stack', 'required': 'cuda_resident_stack'}
- PASS: `doctor_artifact_available` - {'present': False, 'required': False}
