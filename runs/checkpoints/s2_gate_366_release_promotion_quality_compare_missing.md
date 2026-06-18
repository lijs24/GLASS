# GLASS Release Promotion Decision

- Status: `default_change_ready`
- Recommendation: `promote_default_candidate`
- Release candidate ready: `True`
- Default change ready: `True`
- Speedup: `46.8`

## Checks

- PASS: `acceptance_audit_passed` - {'status': 'passed', 'path': 'runs\\checkpoints\\s2_gate_366_fixtures\\missing_quality_compare\\acceptance.json'}
- PASS: `speedup_threshold` - {'actual': 46.8, 'required_min': 2.0}
- PASS: `pipeline_release_evidence_passed` - {'release_evidence_status': 'passed', 'pipeline_contract_passed': True, 'pipeline_contract_status': 'passed'}
- PASS: `pipeline_handoff_evidence_present` - {'source': 'explicit_pipeline_contract', 'audit_type': 'pipeline_invariant_contract', 'status': 'passed'}
- PASS: `pipeline_integration_dq_contract_passed` - {'source': 'explicit_pipeline_contract', 'check': True, 'integration_output_count': 1, 'integration_map_count': 3}
- PASS: `pipeline_result_contracts_passed` - {'stack_result_contract': True, 'resident_result_contract': True}
- PASS: `pipeline_resident_winsorized_semantics_handoff` - {'schema_version': 1, 'status': 'not_available', 'ready': True, 'scope': 'sparse_or_not_supplied', 'output_count': 0, 'required_count': 0, 'failed_count': 0, 'legacy_completion_count': 0, 'descriptor_sources': [], 'failed_items': [], 'rows': []}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_verification_passed` - {'dq_pixels': True, 'coverage_pixels': True, 'rejection_pixels': True}
- PASS: `pipeline_rejection_sample_accounting_passed` - {'ready': True, 'check': True, 'status': 'passed', 'check_present': True, 'required_count': None, 'verified_count': None, 'accounted_output_count': 1, 'failed_count': 0, 'failed_items': [], 'scope': 'not_required'}
- PASS: `pipeline_sample_accounting_closure_passed` - {'ready': True, 'check': True, 'status': 'passed', 'check_present': True, 'present_count': 1, 'required_count': 1, 'failed_count': 0, 'failed_items': [], 'scope': 'required'}
- PASS: `warp_quality_contract_handoff` - {'schema_version': 1, 'source': 'acceptance_audit', 'present': False, 'status': 'not_available', 'ready': True, 'path': None, 'exists': None, 'artifact_type': None, 'contract_status': None, 'contract_passed': None, 'check_count': None, 'output_count': None, 'failed_checks': [], 'acceptance_checks': {'warp_quality_contract_present': None, 'warp_quality_contract_type': None, 'warp_quality_contract_passed': None}, 'failed_acceptance_checks': []}
- PASS: `resident_registration_fastpath_handoff` - {'schema_version': 1, 'source': None, 'present': False, 'status': 'not_available', 'ready': True, 'required_by_benchmark_contract': False, 'path': None, 'exists': None, 'available': None, 'resident_registration_mode': None, 'descriptor_fit_batch_mode': None, 'pixel_refine_batch_mode': None, 'triangle_warp_batch_mode': None, 'triangle_warp_batch_frame_count': None, 'warp_copy_mode': None, 'passed_check_count': None, 'failed_check_count': 0, 'failed_checks': [], 'acceptance_check_count': 0, 'failed_acceptance_checks': [], 'acceptance_checks': {}}
- PASS: `stack_engine_release_evidence_passed` - {'release_evidence_status': 'passed', 'stack_engine_contract_passed': True, 'stack_engine_contract_status': 'passed'}
- PASS: `stack_engine_default_ready` - {'acceptance_release_status': 'passed', 'contract_default_ready': True}
- PASS: `stack_engine_scope_all` - {'actual': 'all', 'required': 'all'}
- PASS: `runtime_repeat_evidence_ready` - {'present': True, 'run_count': 3, 'considered_run_count': 3, 'ignored_warmup_run_count': 0, 'ignored_warmup_labels': [], 'required_min_runtime_runs': 3, 'recommendation': 'best_observed:repeat_2', 'best_label': 'repeat_2', 'best_elapsed_s': 18.0, 'slowest_elapsed_s': 19.0, 'elapsed_ratio_vs_best': 1.0555555555555556, 'max_elapsed_ratio_vs_best': 1.25}
- PASS: `stack_engine_publication_runtime_default_passed` - {'present': True, 'artifact_type': 'stack_engine_publication_audit', 'status': 'passed', 'passed': True, 'recommendation': 'publication_chain_ready', 'failed_checks': [], 'checks': {'publish_preflight_stack_engine_runtime_default_ready': True, 'phase2_publish_preflight_stack_engine_runtime_default_ready': True, 'phase2_publish_preflight_stack_engine_runtime_default_matches_publish_preflight': True}, 'checks_passed': True, 'raw_ready': True, 'raw_matrix_status': 'passed', 'raw_pipeline_status': 'passed', 'raw_legacy_master_count': 0, 'raw_failed_output_count': 0, 'phase2_ready': True, 'phase2_check_passed': True, 'phase2_matrix_status': 'passed', 'phase2_pipeline_status': 'passed', 'phase2_legacy_master_count': 0, 'phase2_failed_output_count': 0}
- PASS: `stack_engine_publication_direct_runtime_evidence_passed` - {'present': True, 'artifact_type': 'stack_engine_publication_audit', 'status': 'passed', 'passed': True, 'recommendation': 'publication_chain_ready', 'failed_checks': [], 'checks': {'publish_preflight_direct_runtime_evidence_ready': True, 'phase2_publish_preflight_direct_runtime_evidence_ready': True, 'phase2_publish_preflight_direct_runtime_evidence_matches_publish_preflight': True}, 'checks_passed': True, 'ready': True, 'raw_ready': True, 'raw_matrix_acceptance_source': 'explicit_resident_artifacts_json', 'raw_default_promotion_acceptance_source': 'explicit_resident_artifacts_json', 'raw_matrix_acceptance_check_count': 24, 'raw_default_promotion_acceptance_check_count': 24, 'raw_matrix_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'raw_default_promotion_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'raw_matrix_pipeline_resident_lights': 200, 'raw_default_promotion_pipeline_resident_lights': 200, 'raw_source_ready': True, 'raw_count_ready': True, 'raw_leaf_checks_ready': True, 'phase2_ready': True, 'phase2_check_passed': True, 'phase2_matrix_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_default_promotion_acceptance_source': 'explicit_resident_artifacts_json', 'phase2_matrix_acceptance_check_count': 24, 'phase2_default_promotion_acceptance_check_count': 24, 'phase2_matrix_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'phase2_default_promotion_pipeline_calibration_source': 'resident_artifacts_json_fallback', 'phase2_matrix_pipeline_resident_lights': 200, 'phase2_default_promotion_pipeline_resident_lights': 200, 'phase2_source_ready': True, 'phase2_count_ready': True, 'phase2_leaf_checks_ready': True}
- PASS: `stack_engine_publication_quality_metrics_compare_passed` - {'present': True, 'artifact_type': 'stack_engine_publication_audit', 'status': 'passed', 'passed': True, 'recommendation': 'publication_chain_ready', 'failed_checks': [], 'checks': {'publish_preflight_quality_metrics_compare_ready': None, 'phase2_publish_preflight_quality_metrics_compare_ready': None, 'phase2_publish_preflight_quality_metrics_compare_matches_publish_preflight': None}, 'checks_passed': True, 'ready': True, 'compatible_missing': True, 'quality_compare_present': False, 'raw_present': None, 'raw_ready': None, 'raw_matrix_present': None, 'raw_matrix_ready': None, 'raw_matrix_status': None, 'raw_matrix_failed_check_count': None, 'raw_default_promotion_present': None, 'raw_default_promotion_ready': None, 'raw_default_promotion_status': None, 'raw_default_promotion_failed_check_count': None, 'raw_matrix_handoff_passed': None, 'raw_default_promotion_handoff_passed': None, 'raw_matches_default_promotion': None, 'phase2_present': None, 'phase2_ready': None, 'phase2_check_passed': None, 'phase2_matrix_present': None, 'phase2_matrix_ready': None, 'phase2_matrix_status': None, 'phase2_matrix_failed_check_count': None, 'phase2_default_promotion_present': None, 'phase2_default_promotion_ready': None, 'phase2_default_promotion_status': None, 'phase2_default_promotion_failed_check_count': None, 'phase2_matrix_handoff_passed': None, 'phase2_default_promotion_handoff_passed': None, 'phase2_matches_default_promotion': None}

## Pipeline DQ Handoff

- Source: `explicit_pipeline_contract`
- Status: `passed`
- Passed: `True`
- Integration outputs: `1`
- Integration maps: `3`
- Pixel verification enabled: `True`
- Rejection sample accounting: `passed`
- Rejection sample release scope: `not_required`, ready `True`, required `None`, verified `None`
- Sample accounting closure: `passed`
- Sample closure release scope: `required`, ready `True`, required `1`, present `1`
- Resident winsorized semantics: `not_available`, ready `True`, required `0`, legacy completions `0`
- Resident winsorized descriptor sources: `[]`


## Resident Registration Fastpath Handoff

- Present: `False`
- Status: `not_available`
- Ready: `True`
- Required: `False`
- Source: `None`
- Path: `None`
- Mode: `None`
- Descriptor batch: `None`
- Pixel refine batch: `None`
- Triangle warp batch: `None`
- Triangle warp batch frames: `None`
- Warp copy mode: `None`
- Checks passed: `None`
- Checks failed: `0`
- Failed checks: `[]`
- Failed acceptance checks: `[]`


## Warp Quality Handoff

- Present: `False`
- Status: `not_available`
- Ready: `True`
- Contract passed: `None`
- Output count: `None`
- Failed checks: `[]`
- Failed acceptance checks: `[]`
- Path: `None`


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
- Direct runtime ready: `True`
- Direct runtime checks passed: `True`
- Direct runtime raw source: acceptance=`explicit_resident_artifacts_json` calibration=`resident_artifacts_json_fallback` lights=`200`
- Direct runtime Phase2 source: acceptance=`explicit_resident_artifacts_json` calibration=`resident_artifacts_json_fallback` lights=`200`
- Quality compare ready: `True`
- Quality compare present: `False`
- Quality compare checks passed: `True`
- Quality compare raw: present=`None` status=`None` failed_checks=`None`
- Quality compare Phase2: present=`None` status=`None` failed_checks=`None`


## Runtime Repeat Evidence

- Present: `True`
- Run count: `3`
- Recommendation: `best_observed:repeat_2`
- Ratio vs best: `1.0555555555555556`
