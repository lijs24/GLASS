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
- Status: `blocked`
- Passed: `False`
- Default route passed: `None`
- Default route contract/checks: `None`/`None`
- Rejection sample accounting: `None` failed=`None`
- Quality metrics compare: present=`True` ready=`True` status=`passed` failed-checks=`[]`
- Sample accounting closure: `None` present=`None` failed=`None`
- Resident result contract: ready=`False` status=`None` check=`None` phase2=`None` required=`None` failed=`None` failed-checks=`[]`
- Integration engine policy: ready=`False` acceptance=`None` pipeline=`None`
- StackEngine runtime default: ready=`False` acceptance=`None` pipeline=`None`
- Runtime default counts: acceptance-legacy=`None` acceptance-failed-masters=`None` pipeline-failed-outputs=`None` explicit-cuda=`None`
- Direct runtime evidence: ready=`True` acceptance-source=`explicit_resident_artifacts_json` acceptance-checks=`24` pipeline-calibration-source=`resident_artifacts_json_fallback` resident-lights=`200`
- Release decision direct publication guard: ready=`True` check=`True` source-ready=`True` count-ready=`True` lights=`200`
- Default promotion direct publication guard: ready=`True` check=`True` source-ready=`True` count-ready=`True` lights=`200`
- Resident fastpath release handoff: ready=`False` raw=`None` phase2=`None` agreement=`True` checks=`None`
- StackEngine default contract: ready=`False` phase2-check=`None` gaps=`None` blockers=`None`
- Resident winsorized sweep: passed=`None` phase2-check=`None` required-frame=`None` required-pass=`None` checks=`None`
- StackEngine publication audit: ready=`False` passed=`None` phase2-check=`None` failed=`None`
- Publication policy chain: raw=`None` phase2=`None` agreement=`None` check=`None`
- Publication resident winsorized chain: raw=`None` phase2=`None` agreement=`None` check=`None`

## Packages

| Package | Artifact | Compatible | Match | Role |
| --- | --- | --- | --- | --- |
| cuda11 | GLASS-Portable-win64-cuda11.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda12 | GLASS-Portable-win64-cuda12.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda13 | GLASS-Portable-win64-cuda13.zip | True | native_cubin | primary_cuda_package |
| cpu | GLASS-Portable-win64-cpu.zip | True | cpu_fallback | universal_cpu_fallback |

## Checks

- PASS: `doctor_schema_version` - {'actual': 1, 'required': 1, 'path': 'runs\\checkpoints\\s2_gate_361_cuda_doctor.json'}
- PASS: `cuda_probe_completed` - {'probe_skipped': False}
- PASS: `cuda_available_for_release_machine` - {'actual': True, 'required': True, 'wrapper_importable': True, 'native_extension_loaded': True}
- PASS: `windows_package_recommendation_present` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'package_count': 3}
- PASS: `ordered_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `primary_package_matches_expected` - {'actual': 'cuda13', 'required': 'cuda13'}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'required': True, 'status': 'default_change_ready', 'recommendation': 'promote_default_candidate'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'checks_passed': True, 'source_ready': True, 'count_ready': True, 'raw_leaf_checks_ready': True, 'phase2_leaf_checks_ready': True, 'raw_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_acceptance_source': 'explicit_resident_artifacts_json', 'raw_calibration_source': 'resident_artifacts_json_fallback', 'phase2_calibration_source': 'resident_artifacts_json_fallback', 'raw_resident_lights': 200, 'raw_default_promotion_resident_lights': 200, 'phase2_resident_lights': 200, 'phase2_default_promotion_resident_lights': 200, 'required_min_resident_lights': 200}
- PASS: `default_promotion_manifest_present` - {'present': True, 'required': True}
- FAIL: `default_promotion_manifest_ready` - {'artifact_type': 'default_promotion_manifest', 'status': 'blocked', 'passed': False, 'default_change_ready': False}
- FAIL: `default_promotion_default_route_passed` - {'default_route_passed': None, 'route_contract_passed': None, 'route_check_count': None}
- PASS: `default_promotion_quality_metrics_compare_handoff_passed` - {'present': True, 'ready': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_check_count': 0, 'failed_checks': [], 'threshold_failure_count': 0, 'threshold_failures': []}
- FAIL: `default_promotion_rejection_sample_accounting_passed` - {'pipeline_contract_status': None, 'pipeline_contract_passed': None, 'check': None, 'status': None, 'failed_count': None, 'failed_items': None}
- FAIL: `default_promotion_sample_accounting_closure_passed` - {'pipeline_contract_status': None, 'pipeline_contract_passed': None, 'check': None, 'status': None, 'present_count': None, 'failed_count': None, 'failed_items': None}
- FAIL: `default_promotion_resident_result_contract_handoff_passed` - {'present': False, 'ready': False, 'status': None, 'top_level_check': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'required_count': None, 'failed_count': None, 'failed_check_count': None, 'failed_checks': [], 'failed_items': []}
- FAIL: `default_promotion_acceptance_integration_engine_policy_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'non_resident_count': None, 'failed_count': None, 'failed_items': []}
- FAIL: `default_promotion_pipeline_integration_engine_policy_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'default_engine_policy': None, 'non_resident_count': None, 'failed_count': None, 'failed_items': []}
- FAIL: `default_promotion_acceptance_stack_engine_runtime_default_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'master_count': None, 'legacy_master_count': None, 'failed_master_count': None, 'failed_output_count': None, 'explicit_cuda_fast_path_count': None, 'failed_masters': [], 'failed_outputs': []}
- FAIL: `default_promotion_pipeline_stack_engine_runtime_default_passed` - {'status': None, 'check_present': None, 'check_passed': None, 'phase2_check_passed': None, 'master_count': None, 'legacy_master_count': None, 'failed_master_count': None, 'failed_output_count': None, 'explicit_cuda_fast_path_count': None, 'failed_masters': [], 'failed_outputs': []}
- PASS: `default_promotion_direct_acceptance_fastpath_evidence` - {'present': True, 'ready': True, 'direct_fastpath': True, 'source': 'explicit_resident_artifacts_json', 'check_count': 24, 'failed_check_count': 0, 'failed_checks': [], 'required': True}
- PASS: `default_promotion_direct_pipeline_calibration_evidence` - {'present': True, 'ready': True, 'direct_pipeline_calibration': True, 'source': 'resident_artifacts_json_fallback', 'generated_for_contract': True, 'path_exists': False, 'resident_native_calibration_artifact': True, 'resident_calibrated_light_count': 200, 'required': True}
- PASS: `default_promotion_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200, 'required': True}
- FAIL: `default_promotion_resident_fastpath_release_handoff_ready` - {'present': False, 'ready': False, 'raw_ready': False, 'phase2_ready': False, 'agreement': True, 'decision_check_passed': None, 'phase2_check_passed': None, 'raw_status': None, 'phase2_status': None, 'raw_required': None, 'phase2_required': None, 'raw_mode': None, 'phase2_mode': None, 'raw_passed_check_count': None, 'phase2_passed_check_count': None, 'raw_failed_check_count': None, 'phase2_failed_check_count': None, 'raw_failed_checks': [], 'phase2_failed_checks': []}
- FAIL: `default_promotion_stack_engine_contract_ready` - {'present': False, 'ready': False, 'phase2_check_passed': None, 'status': None, 'passed': None, 'scope': None, 'adoption_recommendation': None, 'default_gap_count': None, 'blocker_count': None, 'blockers': []}
- FAIL: `default_promotion_resident_winsorized_sweep_audit_passed` - {'present': False, 'status': None, 'passed': None, 'phase2_check_passed': None, 'failed_checks': []}
- FAIL: `default_promotion_resident_winsorized_required_frame_passed` - {'actual_frame_count': None, 'required_frame_count': 200, 'required_frame_count_passed': None, 'required_frame_master_rms': None, 'required_frame_master_max_abs': None}
- FAIL: `default_promotion_resident_winsorized_sweep_check_count` - {'actual': None, 'required_min': 27, 'failed_check_count': None}
- FAIL: `default_promotion_stack_engine_publication_audit_passed` - {'present': False, 'ready': False, 'status': None, 'passed': None, 'phase2_check_passed': None, 'recommendation': None, 'check_count': None, 'failed_check_count': None, 'failed_checks': []}
- FAIL: `default_promotion_stack_engine_publication_policy_chain_passed` - {'phase2_check_passed': None, 'publish_preflight_policy_ready': None, 'phase2_policy_ready': None, 'policy_agreement': None}
- FAIL: `default_promotion_stack_engine_publication_resident_winsorized_chain_passed` - {'phase2_check_passed': None, 'publish_preflight_resident_winsorized_ready': None, 'phase2_resident_winsorized_ready': None, 'resident_winsorized_agreement': None}
- PASS: `default_runtime_preset` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `runtime_repeat_ratio_within_release_bound` - {'actual': 1.053510511049479, 'required_max': 1.25}
- PASS: `required_cuda_package_present:cuda13` - {'label': 'cuda13', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda13` - {'label': 'cuda13', 'compatible': True, 'match': 'native_cubin'}
- PASS: `required_cuda_package_present:cuda12` - {'label': 'cuda12', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda12` - {'label': 'cuda12', 'compatible': True, 'match': 'ptx_jit_forward'}
- PASS: `required_cuda_package_present:cuda11` - {'label': 'cuda11', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda11` - {'label': 'cuda11', 'compatible': True, 'match': 'ptx_jit_forward'}
