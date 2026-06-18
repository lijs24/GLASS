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
- Best: `gate218_default_repeat02` `22.598500299995067` s
- Slowest: `23.807757599999604` s
- Slowest/best ratio: `1.053510511049479`

## Default Route Evidence

- Present: `False`
- Status: `None`
- Passed: `None`
- Route contract passed: `None`
- Route check count: `None`
- Route failed checks: `[]`
- Speedup vs reference: `None`
- Quality metrics compare: present=`True` ready=`False` status=`failed` phase2=`False` failed-checks=`['bad_median_ratio_within_limit']`
- Rejection sample accounting: `None`
- Sample accounting closure: `None`
- Resident result contract: ready=`False` status=`None` check=`None` phase2=`None` required=`None` failed=`None` failed-checks=`[]`
- Release resident winsorized semantics: `passed` required=`1` legacy-completions=`1`
- Acceptance integration engine policy: `None`
- Pipeline integration engine policy: `None`
- Integration engine policy ready: `False`
- Acceptance StackEngine runtime default: `None` check=`None` legacy=`None` failed-masters=`None` failed-outputs=`None`
- Pipeline StackEngine runtime default: `None` check=`None` legacy=`None` failed-masters=`None` failed-outputs=`None`
- StackEngine runtime default ready: `False`
- Direct runtime evidence: ready=`True` acceptance-source=`explicit_resident_artifacts_json` pipeline-calibration-source=`resident_artifacts_json_fallback`
- Release direct publication guard: ready=`True` check=`True` source-ready=`True` count-ready=`True`
- Release direct publication sources: raw-acceptance=`explicit_resident_artifacts_json` raw-calibration=`resident_artifacts_json_fallback` raw-lights=`200`
- Resident fastpath release handoff: ready=`False` raw=`None` phase2=`None` agreement=`True` checks=`None`

## StackEngine Default Contract

- Present: `False`
- Status: `None`
- Ready: `False`
- Phase2 check passed: `None`
- Scope: `None`
- Adoption recommendation: `None`
- Default gap count: `None`
- Default promotion: `None` ready=`None` blockers=`None`

## Resident Winsorized Sweep

- Present: `False`
- Status: `None`
- Passed: `None`
- Phase2 check passed: `None`
- Check count: `None`
- Required frame count: `None`
- Required frame count passed: `None`
- Required frame master RMS: `None`
- Required frame hardened CUDA seconds: `None`

## StackEngine Publication Audit

- Present: `False`
- Status: `None`
- Passed: `None`
- Ready: `False`
- Phase2 audit check passed: `None`
- Failed checks: `[]`
- Policy chain: raw=`None` phase2=`None` agreement=`None` phase2-check=`None`
- Resident winsorized chain: raw=`None` phase2=`None` agreement=`None` phase2-check=`None`

## Release Machine

- Doctor present: `True`
- CUDA available: `True`
- Native extension loaded: `True`
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`

## Checks

- PASS: `release_decision_artifact_type` - {'actual': 'release_promotion_decision', 'required': 'release_promotion_decision'}
- PASS: `phase2_status_artifact_type` - {'actual': 'glass_phase2_status', 'required': 'glass_phase2_status'}
- FAIL: `phase2_status_green` - {'status': 'attention_required', 'passed': False}
- PASS: `latest_checkpoint_green` - {'gate': 359, 'status': 'green', 'green': True}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'status': 'default_change_ready'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- FAIL: `phase2_embeds_same_release_decision` - {'input': 'runs\\checkpoints\\s2_gate_309_release_decision_direct_runtime_publication_guard.json', 'phase2_release_decision_path': None}
- FAIL: `phase2_release_decision_default_change_ready` - {'actual': None}
- FAIL: `phase2_release_decision_recommends_promotion` - {'actual': None, 'required': 'promote_default_candidate'}
- PASS: `release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'status': 'passed', 'passed': True, 'checks_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'raw_ready': True, 'phase2_ready': True, 'phase2_check_passed': True, 'raw_matrix_acceptance_source': 'explicit_resident_artifacts_json', 'raw_default_promotion_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_matrix_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_default_promotion_acceptance_source': 'explicit_resident_artifacts_json', 'raw_matrix_acceptance_check_count': 24, 'raw_default_promotion_acceptance_check_count': 24, 'phase2_matrix_acceptance_check_count': 24, 'phase2_default_promotion_acceptance_check_count': 24, 'raw_matrix_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'raw_default_promotion_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'phase2_matrix_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'phase2_default_promotion_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'raw_matrix_pipeline_resident_lights': 200, 'raw_default_promotion_pipeline_resident_lights': 200, 'phase2_matrix_pipeline_resident_lights': 200, 'phase2_default_promotion_pipeline_resident_lights': 200, 'required_min_resident_lights': 200}
- FAIL: `resident_registration_fastpath_release_handoff_ready` - {'present': False, 'ready': False, 'raw_ready': False, 'phase2_ready': False, 'agreement': True, 'decision_check_passed': None, 'phase2_check_passed': None, 'raw_status': None, 'phase2_status': None, 'raw_required': None, 'phase2_required': None, 'raw_source': None, 'phase2_source': None, 'raw_path': None, 'phase2_path': None, 'raw_mode': None, 'phase2_mode': None, 'raw_descriptor_fit_batch_mode': None, 'phase2_descriptor_fit_batch_mode': None, 'raw_pixel_refine_batch_mode': None, 'phase2_pixel_refine_batch_mode': None, 'raw_triangle_warp_batch_mode': None, 'phase2_triangle_warp_batch_mode': None, 'raw_triangle_warp_batch_frame_count': None, 'phase2_triangle_warp_batch_frame_count': None, 'raw_warp_copy_mode': None, 'phase2_warp_copy_mode': None, 'raw_passed_check_count': None, 'phase2_passed_check_count': None, 'raw_failed_check_count': None, 'phase2_failed_check_count': None, 'raw_failed_checks': [], 'phase2_failed_checks': [], 'raw_failed_acceptance_checks': [], 'phase2_failed_acceptance_checks': []}
- FAIL: `default_route_acceptance_present` - {'path': None, 'status': None}
- FAIL: `default_route_acceptance_passed` - {'status': None, 'passed': None, 'acceptance_passed': None}
- FAIL: `default_route_acceptance_route_contract_passed` - {'route_contract_passed': None, 'route_failed_checks': []}
- FAIL: `default_route_acceptance_route_check_count` - {'actual': None, 'required_min': 4}
- PASS: `runtime_repeat_present` - {'present': True, 'recommendation': 'best_observed:gate218_default_repeat02'}
- PASS: `runtime_repeat_count` - {'actual': 3, 'required_min': 2}
- PASS: `runtime_repeat_ratio_within_bound` - {'actual': 1.053510511049479, 'required_max': 1.25}
- FAIL: `quality_metrics_compare_handoff_passed` - {'present': True, 'ready': False, 'status': 'failed', 'passed': False, 'phase2_check_passed': False, 'check_count': 4, 'failed_check_count': 1, 'failed_checks': ['bad_median_ratio_within_limit'], 'baseline_metric_count': 7, 'candidate_metric_count': 7, 'metric_row_count': 7, 'threshold_failure_count': 6, 'threshold_failures': [{'bad_median_ratio': 1.4, 'baseline_median': 2.5, 'candidate_median': 3.5, 'metric': 'fwhm_px'}, {'bad_median_ratio': 1.4, 'baseline_median': 0.4, 'candidate_median': 0.56, 'metric': 'eccentricity'}, {'bad_median_ratio': 1.4, 'baseline_median': 25.0, 'candidate_median': 35.0, 'metric': 'background_rms'}, {'bad_median_ratio': 1.4, 'baseline_median': 45.0, 'candidate_median': 32.142857, 'metric': 'snr'}, {'bad_median_ratio': 1.4, 'baseline_median': 800.0, 'candidate_median': 571.428571, 'metric': 'quality_score'}, {'bad_median_ratio': 1.399999, 'baseline_median': 0.8, 'candidate_median': 0.571429, 'metric': 'weight'}], 'path': 'runs\\checkpoints\\s2_gate_359_quality_metrics_compare.json'}
- FAIL: `pipeline_contract_passed` - {'status': None, 'passed': None}
- FAIL: `pipeline_dq_contract_passed` - {'actual': None}
- FAIL: `pipeline_stack_and_resident_result_contracts_passed` - {'stack': None, 'resident': None}
- FAIL: `pipeline_resident_result_contract_handoff_passed` - {'present': False, 'ready': False, 'status': None, 'top_level_check': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'required_count': None, 'failed_count': None, 'failed_check_count': None, 'failed_checks': [], 'failed_items': []}
- FAIL: `pipeline_pixel_verification_enabled` - {'enabled': None, 'tile_size': None}
- FAIL: `pipeline_pixel_maps_match_dq` - {'dq': None, 'coverage': None, 'rejection': None}
- FAIL: `pipeline_rejection_sample_accounting_passed` - {'check': None, 'status': None, 'failed_count': None, 'failed_items': None}
- FAIL: `pipeline_sample_accounting_closure_passed` - {'check': None, 'status': None, 'present_count': None, 'failed_count': None, 'failed_items': None}
- FAIL: `acceptance_integration_engine_policy_handoff_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'non_resident_count': None, 'failed_count': None, 'failed_items': []}
- FAIL: `pipeline_integration_engine_policy_default_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'default_engine_policy': None, 'non_resident_count': None, 'failed_count': None, 'failed_items': []}
- FAIL: `acceptance_stack_engine_runtime_default_handoff_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'master_count': None, 'legacy_master_count': None, 'failed_master_count': None, 'failed_output_count': None, 'explicit_cuda_fast_path_count': None, 'failed_masters': [], 'failed_outputs': []}
- FAIL: `pipeline_stack_engine_runtime_default_handoff_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'master_count': None, 'legacy_master_count': None, 'failed_master_count': None, 'failed_output_count': None, 'explicit_cuda_fast_path_count': None, 'failed_masters': [], 'failed_outputs': []}
- FAIL: `phase2_stack_engine_default_contract_ready` - {'present': False, 'phase2_check_passed': None, 'status': None, 'passed': None, 'scope': None, 'expected_integration_engine': None, 'adoption_recommendation': None, 'adoption_gap_count': None, 'default_promotion_ready': None, 'default_promotion_status': None, 'default_promotion_blocker_count': None, 'default_promotion_blockers': []}
- FAIL: `resident_calibration_artifact_present` - {'actual': None}
- FAIL: `resident_light_count` - {'actual': None, 'required_min': 200}
- FAIL: `resident_winsorized_sweep_audit_passed` - {'present': False, 'status': None, 'passed': None, 'phase2_check_passed': None, 'failed_checks': []}
- FAIL: `resident_winsorized_sweep_required_frame_passed` - {'actual_frame_count': None, 'required_frame_count': 200, 'required_frame_count_passed': None, 'required_frame_master_rms': None, 'required_frame_master_max_abs': None}
- FAIL: `resident_winsorized_sweep_check_count` - {'actual': None, 'required_min': 27, 'failed_check_count': None}
- FAIL: `stack_engine_publication_audit_passed` - {'present': False, 'status': None, 'passed': None, 'phase2_check_passed': None, 'failed_checks': []}
- FAIL: `stack_engine_publication_policy_chain_passed` - {'publish_preflight_policy_ready': None, 'phase2_policy_ready': None, 'policy_agreement': None, 'phase2_check_passed': None, 'publish_preflight_layer': {}, 'phase2_layer': {}}
- FAIL: `stack_engine_publication_resident_winsorized_chain_passed` - {'publish_preflight_resident_winsorized_ready': None, 'phase2_resident_winsorized_ready': None, 'resident_winsorized_agreement': None, 'phase2_check_passed': None, 'publish_preflight_layer': {}, 'phase2_layer': {}}
- PASS: `default_memory_mode_candidate` - {'actual': 'resident', 'required': 'resident'}
- PASS: `fallback_memory_mode_preserved` - {'actual': 'tile', 'required': 'tile'}
- PASS: `default_runtime_preset_candidate` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `integration_engine_candidate` - {'actual': 'cuda_resident_stack', 'required': 'cuda_resident_stack'}
- PASS: `doctor_artifact_available` - {'present': True, 'required': False}
- PASS: `doctor_cuda_available` - {'cuda_available': True, 'native_extension_loaded': True, 'wrapper_importable': True}
- PASS: `doctor_native_extension_loaded` - {'actual': True}
- PASS: `windows_package_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `windows_package_primary_present` - {'primary': 'cuda13'}
