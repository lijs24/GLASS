# GLASS Release Promotion Decision

- Status: `default_change_ready`
- Recommendation: `promote_default_candidate`
- Release candidate ready: `True`
- Default change ready: `True`
- Speedup: `58.099101701945926`

## Checks

- PASS: `acceptance_audit_passed` - {'status': 'passed', 'path': 'runs\\checkpoints\\s2_gate_305_acceptance_direct_fastpath_runtime_default.json'}
- PASS: `speedup_threshold` - {'actual': 58.099101701945926, 'required_min': 2.0}
- PASS: `pipeline_release_evidence_passed` - {'release_evidence_status': 'passed', 'pipeline_contract_passed': True, 'pipeline_contract_status': 'passed'}
- PASS: `pipeline_handoff_evidence_present` - {'source': 'explicit_pipeline_contract', 'audit_type': 'pipeline_invariant_contract', 'status': 'passed'}
- PASS: `pipeline_integration_dq_contract_passed` - {'source': 'explicit_pipeline_contract', 'check': True, 'integration_output_count': 1, 'integration_map_count': 6}
- PASS: `pipeline_result_contracts_passed` - {'stack_result_contract': True, 'resident_result_contract': True}
- PASS: `pipeline_resident_winsorized_semantics_handoff` - {'schema_version': 1, 'status': 'passed', 'ready': True, 'scope': 'passed', 'output_count': 1, 'required_count': 1, 'failed_count': 0, 'legacy_completion_count': 1, 'descriptor_sources': ['resident_artifacts.integration_rejection'], 'failed_items': [], 'rows': [{'item': 'H', 'required': True, 'present': True, 'passed': True, 'status': 'passed', 'rejection': 'winsorized_sigma', 'descriptor_source': 'resident_artifacts.integration_rejection', 'integration_results_descriptor_present': False, 'resident_artifacts_descriptor_present': True, 'legacy_completion_applied': True, 'legacy_completion_source': 'fast_approx_algorithm', 'resident_winsorized_mode': 'fast_approx', 'algorithm': 'two_stage_winsorized_mean_std_rejection_approximation', 'scale_estimator': 'mean_std_two_stage_winsorized', 'cpu_baseline_parity': False, 'parity_status': 'known_non_parity_pending_cuda_update', 'approximation': True}]}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_verification_passed` - {'dq_pixels': True, 'coverage_pixels': True, 'rejection_pixels': True}
- PASS: `pipeline_rejection_sample_accounting_passed` - {'ready': True, 'check': True, 'status': 'passed', 'check_present': True, 'required_count': 1, 'verified_count': 1, 'accounted_output_count': 1, 'failed_count': 0, 'failed_items': [], 'scope': 'required'}
- PASS: `pipeline_sample_accounting_closure_passed` - {'ready': True, 'check': True, 'status': 'passed', 'check_present': True, 'present_count': 0, 'required_count': 0, 'failed_count': 0, 'failed_items': [], 'scope': 'not_required'}
- PASS: `stack_engine_release_evidence_passed` - {'release_evidence_status': 'passed', 'stack_engine_contract_passed': True, 'stack_engine_contract_status': 'passed'}
- PASS: `stack_engine_default_ready` - {'acceptance_release_status': 'passed', 'contract_default_ready': True}
- PASS: `stack_engine_scope_all` - {'actual': 'all', 'required': 'all'}
- PASS: `runtime_repeat_evidence_ready` - {'present': True, 'run_count': 3, 'considered_run_count': 3, 'ignored_warmup_run_count': 0, 'ignored_warmup_labels': [], 'required_min_runtime_runs': 2, 'recommendation': 'best_observed:gate218_default_repeat02', 'best_label': 'gate218_default_repeat02', 'best_elapsed_s': 22.598500299995067, 'slowest_elapsed_s': 23.807757599999604, 'elapsed_ratio_vs_best': 1.053510511049479, 'max_elapsed_ratio_vs_best': 1.25}
- PASS: `stack_engine_publication_runtime_default_passed` - {'present': True, 'artifact_type': 'stack_engine_publication_audit', 'status': 'passed', 'passed': True, 'recommendation': 'publication_chain_ready', 'failed_checks': [], 'checks': {'publish_preflight_stack_engine_runtime_default_ready': True, 'phase2_publish_preflight_stack_engine_runtime_default_ready': True, 'phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight': True}, 'checks_passed': True, 'raw_ready': True, 'raw_matrix_status': 'passed', 'raw_pipeline_status': 'passed', 'raw_legacy_master_count': 0, 'raw_failed_output_count': 0, 'phase2_ready': True, 'phase2_check_passed': True, 'phase2_matrix_status': 'passed', 'phase2_pipeline_status': 'passed', 'phase2_legacy_master_count': 0, 'phase2_failed_output_count': 0}

## Pipeline DQ Handoff

- Source: `explicit_pipeline_contract`
- Status: `passed`
- Passed: `True`
- Integration outputs: `1`
- Integration maps: `6`
- Pixel verification enabled: `True`
- Rejection sample accounting: `passed`
- Rejection sample release scope: `required`, ready `True`, required `1`, verified `1`
- Sample accounting closure: `passed`
- Sample closure release scope: `not_required`, ready `True`, required `0`, present `0`
- Resident winsorized semantics: `passed`, ready `True`, required `1`, legacy completions `1`
- Resident winsorized descriptor sources: `['resident_artifacts.integration_rejection']`


## StackEngine Publication Runtime Default

- Present: `True`
- Status: `passed`
- Passed: `True`
- Checks passed: `True`
- Raw ready: `True`
- Phase2 ready: `True`
- Phase2 check: `True`
- Raw drift: legacy=`0` failed_outputs=`0`
- Phase2 drift: legacy=`0` failed_outputs=`0`


## Runtime Repeat Evidence

- Present: `True`
- Run count: `3`
- Recommendation: `best_observed:gate218_default_repeat02`
- Ratio vs best: `1.053510511049479`
