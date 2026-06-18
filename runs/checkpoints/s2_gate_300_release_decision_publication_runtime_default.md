# GLASS Release Promotion Decision

- Status: `blocked`
- Recommendation: `fix_release_blockers`
- Release candidate ready: `False`
- Default change ready: `False`
- Speedup: `10.0`

## Checks

- PASS: `acceptance_audit_passed` - {'status': 'passed', 'path': 'runs\\checkpoints\\s2_gate_294_acceptance_runtime_default_ready.json'}
- PASS: `speedup_threshold` - {'actual': 10.0, 'required_min': 2.0}
- PASS: `pipeline_release_evidence_passed` - {'release_evidence_status': 'passed', 'pipeline_contract_passed': True, 'pipeline_contract_status': 'passed'}
- PASS: `pipeline_handoff_evidence_present` - {'source': 'explicit_pipeline_contract', 'audit_type': 'pipeline_invariant_contract', 'status': 'passed'}
- PASS: `pipeline_integration_dq_contract_passed` - {'source': 'explicit_pipeline_contract', 'check': True, 'integration_output_count': 1, 'integration_map_count': 6}
- PASS: `pipeline_result_contracts_passed` - {'stack_result_contract': True, 'resident_result_contract': True}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_verification_passed` - {'dq_pixels': True, 'coverage_pixels': True, 'rejection_pixels': True}
- FAIL: `pipeline_rejection_sample_accounting_passed` - {'check': None, 'status': 'not_available', 'failed_count': 0, 'failed_items': []}
- FAIL: `pipeline_sample_accounting_closure_passed` - {'check': None, 'status': 'not_available', 'present_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `stack_engine_release_evidence_passed` - {'release_evidence_status': 'not_requested', 'stack_engine_contract_passed': True, 'stack_engine_contract_status': 'passed'}
- PASS: `stack_engine_default_ready` - {'acceptance_release_status': 'not_requested', 'contract_default_ready': True}
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
- Rejection sample accounting: `not_available`
- Sample accounting closure: `not_available`


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
