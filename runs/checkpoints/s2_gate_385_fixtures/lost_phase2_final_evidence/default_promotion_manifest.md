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
- Quality metrics compare: present=`True` ready=`True` status=`passed` phase2=`True` failed-checks=`[]`
- Rejection sample accounting: `passed`
- Sample accounting closure: `passed`
- Resident result contract: ready=`True` status=`passed` check=`True` phase2=`True` required=`1` failed=`0` failed-checks=`[]`
- Release resident winsorized semantics: `passed` required=`1` legacy-completions=`1`
- Acceptance integration engine policy: `passed`
- Pipeline integration engine policy: `passed`
- Integration engine policy ready: `True`
- Acceptance StackEngine runtime default: `passed` check=`True` legacy=`0` failed-masters=`0` failed-outputs=`0`
- Pipeline StackEngine runtime default: `passed` check=`True` legacy=`0` failed-masters=`0` failed-outputs=`0`
- StackEngine runtime default ready: `True`
- Direct runtime evidence: ready=`False` acceptance-source=`None` pipeline-calibration-source=`None`
- Release direct publication guard: ready=`True` check=`True` source-ready=`True` count-ready=`True`
- Release direct publication sources: raw-acceptance=`explicit_resident_artifacts_json` raw-calibration=`resident_artifacts_json_fallback` raw-lights=`200`
- Release quality compare publication guard: ready=`True` check=`True` quality-present=`True` compatible-missing=`False`
- Release quality compare sources: raw=`passed` phase2=`passed` raw-failed=`0` phase2-failed=`0`
- Release quality publication guard: ready=`False` check=`False` guard-present=`True` compatible-missing=`False`
- Release quality publication sources: raw-status=`passed` phase2-status=`passed` raw-phase2=`passed` phase2-phase2=`passed`
- Release quality publication final checks: ready=`True` match=`True` compatible-missing=`False` raw-present=`True` phase2-present=`True`
- Release quality publication final evidence: ready=`False` match=`False` compatible-missing=`False` raw-present=`True` phase2-present=`False`
- Release quality publication final values: raw-matrix=`True` raw-manifest=`True` phase2-matrix=`True` phase2-manifest=`True`
- Resident fastpath release handoff: ready=`True` raw=`passed` phase2=`passed` agreement=`True` checks=`23`

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
- Status: `passed`
- Passed: `True`
- Ready: `True`
- Phase2 audit check passed: `True`
- Failed checks: `[]`
- Policy chain: raw=`True` phase2=`True` agreement=`True` phase2-check=`True`
- Resident winsorized chain: raw=`True` phase2=`True` agreement=`True` phase2-check=`True`

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
- PASS: `phase2_status_green` - {'status': 'green', 'passed': True}
- PASS: `latest_checkpoint_green` - {'gate': 252, 'status': 'green', 'green': True}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'status': 'default_change_ready'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `phase2_embeds_same_release_decision` - {'input': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_385_fixtures\\lost_phase2_final_evidence\\release_promotion_decision.json', 'phase2_release_decision_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_385_fixtures\\lost_phase2_final_evidence\\release_promotion_decision.json'}
- PASS: `phase2_release_decision_default_change_ready` - {'actual': True}
- PASS: `phase2_release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'status': 'passed', 'passed': True, 'checks_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'raw_ready': True, 'phase2_ready': True, 'phase2_check_passed': True, 'raw_matrix_acceptance_source': 'explicit_resident_artifacts_json', 'raw_default_promotion_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_matrix_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_default_promotion_acceptance_source': 'explicit_resident_artifacts_json', 'raw_matrix_acceptance_check_count': 24, 'raw_default_promotion_acceptance_check_count': 24, 'phase2_matrix_acceptance_check_count': 24, 'phase2_default_promotion_acceptance_check_count': 24, 'raw_matrix_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'raw_default_promotion_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'phase2_matrix_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'phase2_default_promotion_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'raw_matrix_pipeline_resident_lights': 200, 'raw_default_promotion_pipeline_resident_lights': 200, 'phase2_matrix_pipeline_resident_lights': 200, 'phase2_default_promotion_pipeline_resident_lights': 200, 'required_min_resident_lights': 200}
- PASS: `release_decision_quality_compare_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'status': 'passed', 'passed': True, 'checks_passed': True, 'compatible_missing': False, 'quality_compare_present': True, 'decision_check_ready': True, 'checks_ready': True, 'layers_ready': True, 'raw_present': True, 'raw_ready': True, 'raw_matrix_status': 'passed', 'raw_matrix_failed_check_count': 0, 'raw_default_promotion_status': 'passed', 'raw_default_promotion_failed_check_count': 0, 'phase2_present': True, 'phase2_ready': True, 'phase2_check_passed': True, 'phase2_matrix_status': 'passed', 'phase2_matrix_failed_check_count': 0, 'phase2_default_promotion_status': 'passed', 'phase2_default_promotion_failed_check_count': 0, 'failed_checks': []}
- FAIL: `release_decision_release_quality_publication_guard_passed` - {'present': True, 'ready': False, 'decision_check_passed': False, 'status': 'blocked', 'passed': False, 'checks_passed': False, 'compatible_missing': False, 'release_quality_guard_present': True, 'final_fields_present': True, 'final_checks_compatible_missing': False, 'final_checks_ready': True, 'final_checks_match': True, 'raw_final_checks_present': True, 'raw_final_checks_ready': True, 'phase2_final_checks_present': True, 'phase2_final_checks_ready': True, 'final_evidence_fields_present': True, 'final_evidence_compatible_missing': False, 'final_evidence_ready': False, 'final_evidence_match': False, 'raw_final_evidence_present': True, 'raw_final_evidence_ready': True, 'phase2_final_evidence_present': False, 'phase2_final_evidence_ready': None, 'decision_check_ready': False, 'checks_ready': False, 'layers_ready': False, 'raw_present': True, 'raw_ready': True, 'raw_matrix_raw_status': 'passed', 'raw_matrix_phase2_status': 'passed', 'raw_matrix_check_passed': True, 'raw_matrix_layers_ready': True, 'raw_default_promotion_raw_status': 'passed', 'raw_default_promotion_phase2_status': 'passed', 'raw_default_promotion_check_passed': True, 'raw_default_promotion_layers_ready': True, 'raw_matrix_check': True, 'raw_matrix_default_check': True, 'raw_default_promotion_check': True, 'raw_matrix_default_match_check': True, 'raw_matrix_manifest_match_check': True, 'raw_release_matrix_check': True, 'raw_release_matrix_default_check': True, 'raw_release_default_promotion_check': True, 'raw_release_matrix_default_match_check': True, 'raw_release_matrix_manifest_match_check': True, 'phase2_present': True, 'phase2_ready': True, 'phase2_check_passed': True, 'phase2_matrix_raw_status': 'passed', 'phase2_matrix_phase2_status': 'passed', 'phase2_matrix_check_passed': True, 'phase2_matrix_layers_ready': True, 'phase2_default_promotion_raw_status': 'passed', 'phase2_default_promotion_phase2_status': 'passed', 'phase2_default_promotion_check_passed': True, 'phase2_default_promotion_layers_ready': True, 'phase2_matrix_check': True, 'phase2_matrix_default_check': True, 'phase2_default_promotion_check': True, 'phase2_matrix_default_match_check': True, 'phase2_matrix_manifest_match_check': True, 'phase2_release_matrix_check': True, 'phase2_release_matrix_default_check': True, 'phase2_release_default_promotion_check': True, 'phase2_release_matrix_default_match_check': True, 'phase2_release_matrix_manifest_match_check': True, 'raw_matrix_final_checks_ready': True, 'raw_matrix_final_checks_match': True, 'raw_matrix_raw_final_checks_ready': True, 'raw_matrix_phase2_final_checks_ready': True, 'raw_matrix_default_final_checks_ready': True, 'raw_matrix_default_final_checks_match': True, 'raw_matrix_default_raw_final_checks_ready': True, 'raw_matrix_default_phase2_final_checks_ready': True, 'raw_default_promotion_final_checks_ready': True, 'raw_default_promotion_final_checks_match': True, 'raw_default_promotion_raw_final_checks_ready': True, 'raw_default_promotion_phase2_final_checks_ready': True, 'phase2_matrix_final_checks_ready': None, 'phase2_matrix_final_checks_match': None, 'phase2_matrix_raw_final_checks_ready': None, 'phase2_matrix_phase2_final_checks_ready': None, 'phase2_matrix_default_final_checks_ready': None, 'phase2_matrix_default_final_checks_match': None, 'phase2_matrix_default_raw_final_checks_ready': None, 'phase2_matrix_default_phase2_final_checks_ready': None, 'phase2_default_promotion_final_checks_ready': None, 'phase2_default_promotion_final_checks_match': None, 'phase2_default_promotion_raw_final_checks_ready': None, 'phase2_default_promotion_phase2_final_checks_ready': None, 'failed_checks': ['stack_engine_publication_release_quality_guard_passed']}
- PASS: `resident_registration_fastpath_release_handoff_ready` - {'present': True, 'ready': True, 'raw_ready': True, 'phase2_ready': True, 'agreement': True, 'decision_check_passed': True, 'phase2_check_passed': True, 'raw_status': 'passed', 'phase2_status': 'passed', 'raw_required': True, 'phase2_required': True, 'raw_source': 'explicit_resident_artifacts_json', 'phase2_source': 'explicit_resident_artifacts_json', 'raw_path': 'resident_artifacts.json', 'phase2_path': 'resident_artifacts.json', 'raw_mode': 'similarity_cuda_triangle', 'phase2_mode': 'similarity_cuda_triangle', 'raw_descriptor_fit_batch_mode': 'native_batch_shared_reference_device', 'phase2_descriptor_fit_batch_mode': 'native_batch_shared_reference_device', 'raw_pixel_refine_batch_mode': 'native_batch_one_seed_per_frame', 'phase2_pixel_refine_batch_mode': 'native_batch_one_seed_per_frame', 'raw_triangle_warp_batch_mode': 'native_matrix_lanczos3_frames', 'phase2_triangle_warp_batch_mode': 'native_matrix_lanczos3_frames', 'raw_triangle_warp_batch_frame_count': 3, 'phase2_triangle_warp_batch_frame_count': 3, 'raw_warp_copy_mode': 'default_stream_async_device_to_device', 'phase2_warp_copy_mode': 'default_stream_async_device_to_device', 'raw_passed_check_count': 23, 'phase2_passed_check_count': 23, 'raw_failed_check_count': 0, 'phase2_failed_check_count': 0, 'raw_failed_checks': [], 'phase2_failed_checks': [], 'raw_failed_acceptance_checks': [], 'phase2_failed_acceptance_checks': []}
- PASS: `default_route_acceptance_present` - {'path': 'C:/glass_runs/run/default_route_acceptance.json', 'status': 'passed'}
- PASS: `default_route_acceptance_passed` - {'status': 'passed', 'passed': True, 'acceptance_passed': True}
- PASS: `default_route_acceptance_route_contract_passed` - {'route_contract_passed': True, 'route_failed_checks': []}
- PASS: `default_route_acceptance_route_check_count` - {'actual': 4, 'required_min': 4}
- PASS: `runtime_repeat_present` - {'present': True, 'recommendation': 'best_observed:repeat02'}
- PASS: `runtime_repeat_count` - {'actual': 3, 'required_min': 3}
- PASS: `runtime_repeat_ratio_within_bound` - {'actual': 1.053, 'required_max': 1.25}
- PASS: `quality_metrics_compare_handoff_passed` - {'present': True, 'ready': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'check_count': 3, 'failed_check_count': 0, 'failed_checks': [], 'baseline_metric_count': 7, 'candidate_metric_count': 7, 'metric_row_count': 7, 'threshold_failure_count': 0, 'threshold_failures': [], 'path': 'runs/checkpoints/quality_metrics_compare.json'}
- PASS: `pipeline_contract_passed` - {'status': 'passed', 'passed': True}
- PASS: `pipeline_dq_contract_passed` - {'actual': True}
- PASS: `pipeline_stack_and_resident_result_contracts_passed` - {'stack': True, 'resident': True}
- PASS: `pipeline_resident_result_contract_handoff_passed` - {'present': True, 'ready': True, 'status': 'passed', 'top_level_check': True, 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'required_count': 1, 'failed_count': 0, 'failed_check_count': 0, 'failed_checks': [], 'failed_items': []}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_maps_match_dq` - {'dq': True, 'coverage': True, 'rejection': True}
- PASS: `pipeline_rejection_sample_accounting_passed` - {'check': True, 'status': 'passed', 'failed_count': 0, 'failed_items': []}
- PASS: `pipeline_sample_accounting_closure_passed` - {'check': True, 'status': 'passed', 'present_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: `acceptance_integration_engine_policy_handoff_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `pipeline_integration_engine_policy_default_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'default_engine_policy': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `acceptance_stack_engine_runtime_default_handoff_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 1, 'failed_masters': [], 'failed_outputs': []}
- PASS: `pipeline_stack_engine_runtime_default_handoff_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 1, 'failed_masters': [], 'failed_outputs': []}
- PASS: `phase2_stack_engine_default_contract_ready` - {'present': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'expected_integration_engine': 'stack_engine_cpu', 'adoption_recommendation': 'stack_engine_default_ready', 'adoption_gap_count': 0, 'default_promotion_ready': True, 'default_promotion_status': 'ready', 'default_promotion_blocker_count': 0, 'default_promotion_blockers': []}
- PASS: `resident_calibration_artifact_present` - {'actual': True}
- PASS: `resident_light_count` - {'actual': 200, 'required_min': 200}
- PASS: `resident_winsorized_sweep_audit_passed` - {'present': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_checks': []}
- PASS: `resident_winsorized_sweep_required_frame_passed` - {'actual_frame_count': 200, 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3e-05, 'required_frame_master_max_abs': 6.1e-05}
- PASS: `resident_winsorized_sweep_check_count` - {'actual': 27, 'required_min': 27, 'failed_check_count': 0}
- PASS: `stack_engine_publication_audit_passed` - {'present': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_checks': []}
- PASS: `stack_engine_publication_policy_chain_passed` - {'publish_preflight_policy_ready': True, 'phase2_policy_ready': True, 'policy_agreement': True, 'phase2_check_passed': True, 'publish_preflight_layer': {'ready': True, 'status': 'publish_preflight_ready'}, 'phase2_layer': {'ready': True, 'status': 'publish_preflight_ready'}}
- PASS: `stack_engine_publication_resident_winsorized_chain_passed` - {'publish_preflight_resident_winsorized_ready': True, 'phase2_resident_winsorized_ready': True, 'resident_winsorized_agreement': True, 'phase2_check_passed': True, 'publish_preflight_layer': {'ready': True, 'status': 'publish_preflight_ready'}, 'phase2_layer': {'ready': True, 'status': 'publish_preflight_ready'}}
- PASS: `default_memory_mode_candidate` - {'actual': 'resident', 'required': 'resident'}
- PASS: `fallback_memory_mode_preserved` - {'actual': 'tile', 'required': 'tile'}
- PASS: `default_runtime_preset_candidate` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `integration_engine_candidate` - {'actual': 'cuda_resident_stack', 'required': 'cuda_resident_stack'}
- PASS: `doctor_artifact_available` - {'present': True, 'required': True}
- PASS: `doctor_cuda_available` - {'cuda_available': True, 'native_extension_loaded': True, 'wrapper_importable': True}
- PASS: `doctor_native_extension_loaded` - {'actual': True}
- PASS: `windows_package_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `windows_package_primary_present` - {'primary': 'cuda13'}
