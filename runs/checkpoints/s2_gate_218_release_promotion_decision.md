# GLASS Release Promotion Decision

- Status: `default_change_ready`
- Recommendation: `promote_default_candidate`
- Release candidate ready: `True`
- Default change ready: `True`
- Speedup: `58.099101701945926`

## Checks

- PASS: `acceptance_audit_passed` - {'status': 'passed', 'path': 'runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json'}
- PASS: `speedup_threshold` - {'actual': 58.099101701945926, 'required_min': 2.0}
- PASS: `pipeline_release_evidence_passed` - {'release_evidence_status': 'passed', 'pipeline_contract_passed': True, 'pipeline_contract_status': 'passed'}
- PASS: `pipeline_handoff_evidence_present` - {'source': 'explicit_pipeline_contract', 'audit_type': 'pipeline_invariant_contract', 'status': 'passed'}
- PASS: `pipeline_integration_dq_contract_passed` - {'source': 'explicit_pipeline_contract', 'check': True, 'integration_output_count': 1, 'integration_map_count': 6}
- PASS: `pipeline_result_contracts_passed` - {'stack_result_contract': True, 'resident_result_contract': True}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_verification_passed` - {'dq_pixels': True, 'coverage_pixels': True, 'rejection_pixels': True}
- PASS: `stack_engine_release_evidence_passed` - {'release_evidence_status': 'passed', 'stack_engine_contract_passed': True, 'stack_engine_contract_status': 'passed'}
- PASS: `stack_engine_default_ready` - {'acceptance_release_status': 'passed', 'contract_default_ready': True}
- PASS: `stack_engine_scope_all` - {'actual': 'all', 'required': 'all'}
- PASS: `runtime_repeat_evidence_ready` - {'present': True, 'run_count': 3, 'considered_run_count': 3, 'ignored_warmup_run_count': 0, 'ignored_warmup_labels': [], 'required_min_runtime_runs': 3, 'recommendation': 'best_observed:gate218_default_repeat02', 'best_label': 'gate218_default_repeat02', 'best_elapsed_s': 22.598500299995067, 'slowest_elapsed_s': 23.807757599999604, 'elapsed_ratio_vs_best': 1.053510511049479, 'max_elapsed_ratio_vs_best': 1.25}

## Pipeline DQ Handoff

- Source: `explicit_pipeline_contract`
- Status: `passed`
- Passed: `True`
- Integration outputs: `1`
- Integration maps: `6`
- Pixel verification enabled: `True`


## Runtime Repeat Evidence

- Present: `True`
- Run count: `3`
- Recommendation: `best_observed:gate218_default_repeat02`
- Ratio vs best: `1.053510511049479`
