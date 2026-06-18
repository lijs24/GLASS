# GLASS Default Promotion Manifest

- Status: `default_promotion_ready`
- Recommendation: `promote_resident_cuda_default`
- Passed: `True`
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

- Present: `True`
- Status: `passed`
- Passed: `True`
- Route contract passed: `True`
- Route check count: `4`
- Route failed checks: `[]`
- Speedup vs reference: `28.75107894736842`
- Rejection sample accounting: `passed`
- Sample accounting closure: `passed`
- Release resident winsorized semantics: `passed` required=`1` legacy-completions=`1`
- Acceptance integration engine policy: `passed`
- Pipeline integration engine policy: `passed`
- Integration engine policy ready: `True`
- Acceptance StackEngine runtime default: `passed` check=`True` legacy=`0` failed-masters=`0` failed-outputs=`0`
- Pipeline StackEngine runtime default: `passed` check=`True` legacy=`0` failed-masters=`0` failed-outputs=`0`
- StackEngine runtime default ready: `True`
- Direct runtime evidence: ready=`True` acceptance-source=`explicit_resident_artifacts_json` pipeline-calibration-source=`resident_artifacts_json_fallback`

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
- Required frame master RMS: `2.3066304440398834e-05`
- Required frame hardened CUDA seconds: `0.0012743999977828935`

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
- PASS: `latest_checkpoint_green` - {'gate': 304, 'status': 'Green', 'green': True}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'status': 'default_change_ready'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `phase2_embeds_same_release_decision` - {'input': 'runs\\checkpoints\\s2_gate_305_release_decision_direct_acceptance_fastpath.json', 'phase2_release_decision_path': 'runs\\checkpoints\\s2_gate_305_release_decision_direct_acceptance_fastpath.json'}
- PASS: `phase2_release_decision_default_change_ready` - {'actual': True}
- PASS: `phase2_release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `default_route_acceptance_present` - {'path': 'runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json', 'status': 'passed'}
- PASS: `default_route_acceptance_passed` - {'status': 'passed', 'passed': True, 'acceptance_passed': True}
- PASS: `default_route_acceptance_route_contract_passed` - {'route_contract_passed': True, 'route_failed_checks': []}
- PASS: `default_route_acceptance_route_check_count` - {'actual': 4, 'required_min': 4}
- PASS: `runtime_repeat_present` - {'present': True, 'recommendation': 'best_observed:gate218_default_repeat02'}
- PASS: `runtime_repeat_count` - {'actual': 3, 'required_min': 2}
- PASS: `runtime_repeat_ratio_within_bound` - {'actual': 1.053510511049479, 'required_max': 1.25}
- PASS: `pipeline_contract_passed` - {'status': 'passed', 'passed': True}
- PASS: `pipeline_dq_contract_passed` - {'actual': True}
- PASS: `pipeline_stack_and_resident_result_contracts_passed` - {'stack': True, 'resident': True}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_maps_match_dq` - {'dq': True, 'coverage': True, 'rejection': True}
- PASS: `pipeline_rejection_sample_accounting_passed` - {'check': True, 'status': 'passed', 'failed_count': 0, 'failed_items': []}
- PASS: `pipeline_sample_accounting_closure_passed` - {'check': True, 'status': 'passed', 'present_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `acceptance_integration_engine_policy_handoff_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `pipeline_integration_engine_policy_default_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'default_engine_policy': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `acceptance_stack_engine_runtime_default_handoff_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': []}
- PASS: `pipeline_stack_engine_runtime_default_handoff_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': []}
- PASS: `phase2_stack_engine_default_contract_ready` - {'present': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'expected_integration_engine': 'cuda_resident_stack', 'adoption_recommendation': 'stack_engine_default_ready', 'adoption_gap_count': 0, 'default_promotion_ready': True, 'default_promotion_status': 'ready', 'default_promotion_blocker_count': 0, 'default_promotion_blockers': []}
- PASS: `resident_calibration_artifact_present` - {'actual': True}
- PASS: `resident_light_count` - {'actual': 200, 'required_min': 200}
- PASS: `resident_winsorized_sweep_audit_passed` - {'present': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_checks': []}
- PASS: `resident_winsorized_sweep_required_frame_passed` - {'actual_frame_count': 200, 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3066304440398834e-05, 'required_frame_master_max_abs': 6.103515625e-05}
- PASS: `resident_winsorized_sweep_check_count` - {'actual': 27, 'required_min': 27, 'failed_check_count': 0}
- PASS: `stack_engine_publication_audit_passed` - {'present': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_checks': []}
- PASS: `stack_engine_publication_policy_chain_passed` - {'publish_preflight_policy_ready': True, 'phase2_policy_ready': True, 'policy_agreement': True, 'phase2_check_passed': True, 'publish_preflight_layer': {'gap_count': None, 'ready': True, 'status': 'publish_preflight_ready'}, 'phase2_layer': {'gap_count': None, 'ready': True, 'status': 'publish_preflight_ready'}}
- PASS: `stack_engine_publication_resident_winsorized_chain_passed` - {'publish_preflight_resident_winsorized_ready': True, 'phase2_resident_winsorized_ready': True, 'resident_winsorized_agreement': True, 'phase2_check_passed': True, 'publish_preflight_layer': {'gap_count': None, 'ready': True, 'status': 'publish_preflight_ready'}, 'phase2_layer': {'gap_count': None, 'ready': True, 'status': 'publish_preflight_ready'}}
- PASS: `default_memory_mode_candidate` - {'actual': 'resident', 'required': 'resident'}
- PASS: `fallback_memory_mode_preserved` - {'actual': 'tile', 'required': 'tile'}
- PASS: `default_runtime_preset_candidate` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `integration_engine_candidate` - {'actual': 'cuda_resident_stack', 'required': 'cuda_resident_stack'}
- PASS: `doctor_artifact_available` - {'present': True, 'required': True}
- PASS: `doctor_cuda_available` - {'cuda_available': True, 'native_extension_loaded': True, 'wrapper_importable': True}
- PASS: `doctor_native_extension_loaded` - {'actual': True}
- PASS: `windows_package_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `windows_package_primary_present` - {'primary': 'cuda13'}
