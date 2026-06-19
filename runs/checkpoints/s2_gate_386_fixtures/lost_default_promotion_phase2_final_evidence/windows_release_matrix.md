# GLASS Windows Release Matrix

- Status: `blocked`
- Recommendation: `fix_release_matrix_blockers`
- Passed: `False`
- Default resident runtime preset: `throughput-v1`

## Current Machine

- CUDA available: `True`
- Native extension loaded: `True`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`
- Guidance: Try cuda13 first for native performance; if it fails to load, try cuda12, cuda11, cpu. Newer GPUs may run older CUDA packages through PTX JIT.

## Default Promotion Manifest

- Present: `True`
- Status: `default_promotion_ready`
- Passed: `True`
- Default route passed: `True`
- Default route contract/checks: `True`/`4`
- Rejection sample accounting: `passed` failed=`0`
- Quality metrics compare: present=`True` ready=`True` status=`passed` failed-checks=`[]`
- Sample accounting closure: `passed` present=`1` failed=`0`
- Resident result contract: ready=`True` status=`passed` check=`True` phase2=`True` required=`1` failed=`0` failed-checks=`[]`
- Integration engine policy: ready=`True` acceptance=`passed` pipeline=`passed`
- StackEngine runtime default: ready=`True` acceptance=`passed` pipeline=`passed`
- Runtime default counts: acceptance-legacy=`0` acceptance-failed-masters=`0` pipeline-failed-outputs=`0` explicit-cuda=`1`
- Direct runtime evidence: ready=`True` acceptance-source=`explicit_resident_artifacts_json` acceptance-checks=`24` pipeline-calibration-source=`resident_artifacts_json_fallback` resident-lights=`200`
- Release decision direct publication guard: ready=`True` check=`True` source-ready=`True` count-ready=`True` lights=`200`
- Release decision quality publication guard: ready=`True` check=`True` quality-present=`True` compatible-missing=`False`
- Release decision release-quality publication guard: ready=`True` check=`True` guard-present=`True` compatible-missing=`False`
- Release quality publication final checks: ready=`True` match=`True` raw=`True` phase2=`True`
- Release quality publication final evidence: ready=`True` match=`True` raw=`True` phase2=`True`
- Default promotion direct publication guard: ready=`True` check=`True` source-ready=`True` count-ready=`True` lights=`200`
- Default promotion quality publication guard: ready=`True` check=`True` raw=`passed` phase2=`passed`
- Default promotion release-quality publication guard: ready=`True` check=`True` raw=`passed` phase2=`passed`
- Default promotion release quality final checks: ready=`True` match=`True` raw=`True` phase2=`True`
- Default promotion release quality final evidence: ready=`False` match=`False` raw=`True` phase2=`None`
- Resident fastpath release handoff: ready=`True` raw=`passed` phase2=`passed` agreement=`True` checks=`23`
- StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`
- Resident winsorized sweep: passed=`True` phase2-check=`True` required-frame=`200` required-pass=`True` checks=`27`
- StackEngine publication audit: ready=`True` passed=`True` phase2-check=`True` failed=`0`
- Publication policy chain: raw=`True` phase2=`True` agreement=`True` check=`True`
- Publication resident winsorized chain: raw=`True` phase2=`True` agreement=`True` check=`True`

## Packages

| Package | Artifact | Compatible | Match | Role |
| --- | --- | --- | --- | --- |
| cuda11 | GLASS-Portable-win64-cuda11.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda12 | GLASS-Portable-win64-cuda12.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda13 | GLASS-Portable-win64-cuda13.zip | True | native_cubin | primary_cuda_package |
| cpu | GLASS-Portable-win64-cpu.zip | True | cpu_fallback | universal_cpu_fallback |

## Checks

- PASS: `doctor_schema_version` - {'actual': 1, 'required': 1, 'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_386_fixtures\\lost_default_promotion_phase2_final_evidence\\doctor.json'}
- PASS: `cuda_probe_completed` - {'probe_skipped': False}
- PASS: `cuda_available_for_release_machine` - {'actual': True, 'required': True, 'wrapper_importable': True, 'native_extension_loaded': True}
- PASS: `windows_package_recommendation_present` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'package_count': 3}
- PASS: `ordered_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `primary_package_matches_expected` - {'actual': 'cuda13', 'required': 'cuda13'}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'required': True, 'status': 'default_change_ready', 'recommendation': 'promote_default_candidate'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'checks_passed': True, 'source_ready': True, 'count_ready': True, 'raw_leaf_checks_ready': True, 'phase2_leaf_checks_ready': True, 'raw_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_acceptance_source': 'explicit_resident_artifacts_json', 'raw_calibration_source': 'resident_artifacts_json_fallback', 'phase2_calibration_source': 'resident_artifacts_json_fallback', 'raw_resident_lights': 200, 'raw_default_promotion_resident_lights': 200, 'phase2_resident_lights': 200, 'phase2_default_promotion_resident_lights': 200, 'required_min_resident_lights': 200}
- PASS: `release_decision_quality_compare_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'status': 'passed', 'passed': True, 'checks_passed': True, 'compatible_missing': False, 'quality_compare_present': True, 'decision_check_ready': True, 'checks_ready': True, 'layers_ready': True, 'raw_present': True, 'raw_ready': True, 'raw_matrix_status': 'passed', 'raw_matrix_failed_check_count': 0, 'phase2_present': True, 'phase2_ready': True, 'phase2_check_passed': True, 'phase2_matrix_status': 'passed', 'phase2_matrix_failed_check_count': 0, 'failed_checks': []}
- PASS: `release_decision_release_quality_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'status': 'passed', 'passed': True, 'checks_passed': True, 'compatible_missing': False, 'release_quality_guard_present': True, 'final_fields_present': True, 'final_checks_compatible_missing': False, 'final_checks_ready': True, 'final_checks_match': True, 'raw_final_checks_present': True, 'raw_final_checks_ready': True, 'phase2_final_checks_present': True, 'phase2_final_checks_ready': True, 'final_evidence_fields_present': True, 'final_evidence_compatible_missing': False, 'final_evidence_ready': True, 'final_evidence_match': True, 'raw_final_evidence_present': True, 'raw_final_evidence_ready': True, 'phase2_final_evidence_present': True, 'phase2_final_evidence_ready': True, 'decision_check_ready': True, 'checks_ready': True, 'layers_ready': True, 'raw_present': True, 'raw_ready': True, 'raw_matrix_raw_status': 'passed', 'raw_matrix_phase2_status': 'passed', 'raw_matrix_check_passed': True, 'raw_matrix_layers_ready': True, 'raw_default_promotion_raw_status': 'passed', 'raw_default_promotion_phase2_status': 'passed', 'raw_default_promotion_check_passed': True, 'raw_default_promotion_layers_ready': True, 'raw_matrix_check': True, 'raw_matrix_default_check': True, 'raw_default_promotion_check': True, 'raw_matrix_default_match_check': True, 'raw_matrix_manifest_match_check': True, 'raw_release_matrix_check': True, 'raw_release_matrix_default_check': True, 'raw_release_default_promotion_check': True, 'raw_release_matrix_default_match_check': True, 'raw_release_matrix_manifest_match_check': True, 'phase2_present': True, 'phase2_ready': True, 'phase2_check_passed': True, 'phase2_matrix_raw_status': 'passed', 'phase2_matrix_phase2_status': 'passed', 'phase2_matrix_check_passed': True, 'phase2_matrix_layers_ready': True, 'phase2_default_promotion_raw_status': 'passed', 'phase2_default_promotion_phase2_status': 'passed', 'phase2_default_promotion_check_passed': True, 'phase2_default_promotion_layers_ready': True, 'phase2_matrix_check': True, 'phase2_matrix_default_check': True, 'phase2_default_promotion_check': True, 'phase2_matrix_default_match_check': True, 'phase2_matrix_manifest_match_check': True, 'phase2_release_matrix_check': True, 'phase2_release_matrix_default_check': True, 'phase2_release_default_promotion_check': True, 'phase2_release_matrix_default_match_check': True, 'phase2_release_matrix_manifest_match_check': True, 'raw_matrix_final_checks_ready': True, 'raw_matrix_final_checks_match': True, 'raw_matrix_raw_final_checks_ready': True, 'raw_matrix_phase2_final_checks_ready': True, 'raw_matrix_default_final_checks_ready': True, 'raw_matrix_default_final_checks_match': True, 'raw_matrix_default_raw_final_checks_ready': True, 'raw_matrix_default_phase2_final_checks_ready': True, 'raw_default_promotion_final_checks_ready': True, 'raw_default_promotion_final_checks_match': True, 'raw_default_promotion_raw_final_checks_ready': True, 'raw_default_promotion_phase2_final_checks_ready': True, 'phase2_matrix_final_checks_ready': True, 'phase2_matrix_final_checks_match': True, 'phase2_matrix_raw_final_checks_ready': True, 'phase2_matrix_phase2_final_checks_ready': True, 'phase2_matrix_default_final_checks_ready': True, 'phase2_matrix_default_final_checks_match': True, 'phase2_matrix_default_raw_final_checks_ready': True, 'phase2_matrix_default_phase2_final_checks_ready': True, 'phase2_default_promotion_final_checks_ready': True, 'phase2_default_promotion_final_checks_match': True, 'phase2_default_promotion_raw_final_checks_ready': True, 'phase2_default_promotion_phase2_final_checks_ready': True, 'failed_checks': []}
- PASS: `default_promotion_manifest_present` - {'present': True, 'required': True}
- PASS: `default_promotion_manifest_ready` - {'artifact_type': 'default_promotion_manifest', 'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True}
- PASS: `default_promotion_default_route_passed` - {'default_route_passed': True, 'route_contract_passed': True, 'route_check_count': 4}
- PASS: `default_promotion_quality_metrics_compare_handoff_passed` - {'present': True, 'ready': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_check_count': 0, 'failed_checks': [], 'threshold_failure_count': 0, 'threshold_failures': []}
- PASS: `default_promotion_rejection_sample_accounting_passed` - {'pipeline_contract_status': 'passed', 'pipeline_contract_passed': True, 'check': True, 'status': 'passed', 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_sample_accounting_closure_passed` - {'pipeline_contract_status': 'passed', 'pipeline_contract_passed': True, 'check': True, 'status': 'passed', 'present_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_resident_result_contract_handoff_passed` - {'present': True, 'ready': True, 'status': 'passed', 'top_level_check': True, 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'required_count': 1, 'failed_count': 0, 'failed_check_count': 0, 'failed_checks': [], 'failed_items': []}
- PASS: `default_promotion_acceptance_integration_engine_policy_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_pipeline_integration_engine_policy_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'default_engine_policy': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_acceptance_stack_engine_runtime_default_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 1, 'failed_masters': [], 'failed_outputs': []}
- PASS: `default_promotion_pipeline_stack_engine_runtime_default_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 1, 'failed_masters': [], 'failed_outputs': []}
- PASS: `default_promotion_direct_acceptance_fastpath_evidence` - {'present': True, 'ready': True, 'direct_fastpath': True, 'source': 'explicit_resident_artifacts_json', 'check_count': 24, 'failed_check_count': 0, 'failed_checks': [], 'required': True}
- PASS: `default_promotion_direct_pipeline_calibration_evidence` - {'present': True, 'ready': True, 'direct_pipeline_calibration': True, 'source': 'resident_artifacts_json_fallback', 'generated_for_contract': True, 'path_exists': False, 'resident_native_calibration_artifact': True, 'resident_calibrated_light_count': 200, 'required': True}
- PASS: `default_promotion_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200, 'required': True}
- PASS: `default_promotion_release_decision_quality_compare_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'quality_present': True, 'compatible_missing': False, 'layers_ready': True, 'raw_status': 'passed', 'raw_failed_count': 0, 'phase2_status': 'passed', 'phase2_failed_count': 0}
- FAIL: `default_promotion_release_decision_release_quality_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'decision_check_ready': True, 'checks_ready': True, 'layers_ready': True, 'compatible_missing': False, 'release_quality_present': True, 'raw_matrix_raw_status': 'passed', 'raw_matrix_phase2_status': 'passed', 'raw_matrix_check_passed': True, 'raw_default_promotion_check_passed': True, 'raw_matrix_default_match_check': True, 'raw_matrix_manifest_match_check': True, 'phase2_matrix_raw_status': 'passed', 'phase2_matrix_phase2_status': 'passed', 'phase2_matrix_check_passed': True, 'phase2_default_promotion_check_passed': True, 'phase2_matrix_default_match_check': True, 'phase2_matrix_manifest_match_check': True, 'direct_final_fields_present': True, 'final_fields_present': True, 'final_checks_compatible_missing': False, 'final_checks_ready': True, 'final_checks_match': True, 'raw_final_checks_present': True, 'raw_final_checks_ready': True, 'phase2_final_checks_present': True, 'phase2_final_checks_ready': True, 'direct_final_evidence_fields_present': True, 'final_evidence_fields_present': True, 'final_evidence_compatible_missing': False, 'final_evidence_ready': False, 'final_evidence_match': False, 'raw_final_evidence_present': True, 'raw_final_evidence_ready': True, 'phase2_final_evidence_present': False, 'phase2_final_evidence_ready': None, 'raw_matrix_final_checks_ready': True, 'raw_matrix_final_checks_match': True, 'raw_matrix_raw_final_checks_ready': True, 'raw_matrix_phase2_final_checks_ready': None, 'phase2_matrix_final_checks_ready': None, 'phase2_matrix_final_checks_match': None, 'phase2_matrix_raw_final_checks_ready': True, 'phase2_matrix_phase2_final_checks_ready': None, 'raw_release_matrix_check': True, 'raw_release_matrix_manifest_match_check': True, 'phase2_release_matrix_check': True, 'phase2_release_matrix_manifest_match_check': True, 'failed_checks': []}
- PASS: `default_promotion_resident_fastpath_release_handoff_ready` - {'present': True, 'ready': True, 'raw_ready': True, 'phase2_ready': True, 'agreement': True, 'decision_check_passed': True, 'phase2_check_passed': True, 'raw_status': 'passed', 'phase2_status': 'passed', 'raw_required': True, 'phase2_required': True, 'raw_mode': 'similarity_cuda_triangle', 'phase2_mode': 'similarity_cuda_triangle', 'raw_passed_check_count': 23, 'phase2_passed_check_count': 23, 'raw_failed_check_count': 0, 'phase2_failed_check_count': 0, 'raw_failed_checks': [], 'phase2_failed_checks': []}
- PASS: `default_promotion_stack_engine_contract_ready` - {'present': True, 'ready': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'adoption_recommendation': 'stack_engine_default_ready', 'default_gap_count': 0, 'blocker_count': 0, 'blockers': []}
- PASS: `default_promotion_resident_winsorized_sweep_audit_passed` - {'present': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_checks': []}
- PASS: `default_promotion_resident_winsorized_required_frame_passed` - {'actual_frame_count': 200, 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3e-05, 'required_frame_master_max_abs': 6.1e-05}
- PASS: `default_promotion_resident_winsorized_sweep_check_count` - {'actual': 27, 'required_min': 27, 'failed_check_count': 0}
- PASS: `default_promotion_stack_engine_publication_audit_passed` - {'present': True, 'ready': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'recommendation': 'publish_stack_engine_default', 'check_count': 18, 'failed_check_count': 0, 'failed_checks': []}
- PASS: `default_promotion_stack_engine_publication_policy_chain_passed` - {'phase2_check_passed': True, 'publish_preflight_policy_ready': True, 'phase2_policy_ready': True, 'policy_agreement': True}
- PASS: `default_promotion_stack_engine_publication_resident_winsorized_chain_passed` - {'phase2_check_passed': True, 'publish_preflight_resident_winsorized_ready': True, 'phase2_resident_winsorized_ready': True, 'resident_winsorized_agreement': True}
- PASS: `default_runtime_preset` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `runtime_repeat_ratio_within_release_bound` - {'actual': 1.0140343433372492, 'required_max': 1.25}
- PASS: `required_cuda_package_present:cuda13` - {'label': 'cuda13', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda13` - {'label': 'cuda13', 'compatible': True, 'match': 'native_cubin'}
- PASS: `required_cuda_package_present:cuda12` - {'label': 'cuda12', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda12` - {'label': 'cuda12', 'compatible': True, 'match': 'ptx_jit_forward'}
- PASS: `required_cuda_package_present:cuda11` - {'label': 'cuda11', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda11` - {'label': 'cuda11', 'compatible': True, 'match': 'ptx_jit_forward'}
