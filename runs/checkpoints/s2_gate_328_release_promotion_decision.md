# GLASS Release Promotion Decision

- Status: `default_change_ready`
- Recommendation: `promote_default_candidate`
- Release candidate ready: `True`
- Default change ready: `True`
- Speedup: `10.0`

## Checks

- PASS: `acceptance_audit_passed` - {'status': 'passed', 'path': 'runs\\checkpoints\\s2_gate_327_acceptance_audit.json'}
- PASS: `speedup_threshold` - {'actual': 10.0, 'required_min': 2.0}
- PASS: `pipeline_release_evidence_passed` - {'release_evidence_status': 'passed', 'pipeline_contract_passed': None, 'pipeline_contract_status': None}
- PASS: `pipeline_handoff_evidence_present` - {'source': 'acceptance_pipeline_contract', 'audit_type': 'pipeline_invariant_contract', 'status': 'passed'}
- PASS: `pipeline_integration_dq_contract_passed` - {'source': 'acceptance_pipeline_contract', 'check': True, 'integration_output_count': 1, 'integration_map_count': 6}
- PASS: `pipeline_result_contracts_passed` - {'stack_result_contract': True, 'resident_result_contract': True}
- PASS: `pipeline_resident_winsorized_semantics_handoff` - {'schema_version': 1, 'status': 'not_available', 'ready': True, 'scope': 'sparse_or_not_supplied', 'output_count': 0, 'required_count': 0, 'failed_count': 0, 'legacy_completion_count': 0, 'descriptor_sources': [], 'failed_items': [], 'rows': []}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 8}
- PASS: `pipeline_pixel_verification_passed` - {'dq_pixels': True, 'coverage_pixels': True, 'rejection_pixels': True}
- PASS: `pipeline_rejection_sample_accounting_passed` - {'ready': True, 'check': True, 'status': 'passed', 'check_present': True, 'required_count': 0, 'verified_count': 1, 'accounted_output_count': 1, 'failed_count': 0, 'failed_items': [], 'scope': 'not_required'}
- PASS: `pipeline_sample_accounting_closure_passed` - {'ready': True, 'check': True, 'status': 'passed', 'check_present': True, 'present_count': 1, 'required_count': 1, 'failed_count': 0, 'failed_items': [], 'scope': 'required'}
- PASS: `warp_quality_contract_handoff` - {'schema_version': 1, 'source': 'acceptance_audit', 'present': True, 'status': 'passed', 'ready': True, 'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json', 'exists': True, 'artifact_type': 'warp_quality_contract', 'contract_status': 'passed', 'contract_passed': True, 'check_count': 9, 'output_count': 1, 'failed_checks': [], 'acceptance_checks': {'warp_quality_contract_present': True, 'warp_quality_contract_type': True, 'warp_quality_contract_passed': True}, 'failed_acceptance_checks': []}
- PASS: `resident_registration_fastpath_handoff` - {'schema_version': 1, 'source': 'explicit_resident_artifacts_json', 'present': True, 'status': 'passed', 'ready': True, 'required_by_benchmark_contract': True, 'path': 'runs\\checkpoints\\s2_gate_327_fastpath_fixture\\resident_artifacts.json', 'exists': True, 'available': True, 'resident_registration_mode': 'similarity_cuda_triangle', 'descriptor_fit_batch_mode': 'native_batch_shared_reference_device', 'pixel_refine_batch_mode': 'native_batch_one_seed_per_frame', 'triangle_warp_batch_mode': 'native_matrix_lanczos3_frames', 'triangle_warp_batch_frame_count': 3, 'warp_copy_mode': 'default_stream_async_device_to_device', 'passed_check_count': 23, 'failed_check_count': 0, 'failed_checks': [], 'acceptance_check_count': 23, 'failed_acceptance_checks': [], 'acceptance_checks': {'contract_resident_registration_fastpath_present': True, 'contract_resident_registration_fastpath_value:resident_registration.mode': True, 'contract_resident_registration_fastpath_value:resident_registration.triangle_descriptor_fit_batch_mode': True, 'contract_resident_registration_fastpath_value:resident_registration.triangle_pixel_refine_batch_mode': True, 'contract_resident_registration_fastpath_value:resident_registration.triangle_pixel_refine_batch_metric_mode': True, 'contract_resident_registration_fastpath_value:resident_registration.triangle_warp_batch_mode': True, 'contract_resident_registration_fastpath_value:artifact.resident_warp_copy_mode': True, 'contract_resident_registration_fastpath_value:resident_io_pipeline.warp_copy_mode': True, 'contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_batch': True, 'contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_reference_device_reuse': True, 'contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_moving_device_reuse': True, 'contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_output_device_reuse': True, 'contract_resident_registration_fastpath_true:resident_registration.triangle_pixel_refine_batch': True, 'contract_resident_registration_fastpath_true:resident_registration.triangle_warp_batch': True, 'contract_resident_registration_fastpath_positive:resident_registration.triangle_descriptor_fit_reference_device_bytes': True, 'contract_resident_registration_fastpath_positive:resident_registration.triangle_descriptor_fit_moving_device_bytes': True, 'contract_resident_registration_fastpath_positive:resident_registration.triangle_descriptor_fit_output_device_bytes': True, 'contract_resident_registration_fastpath_positive:resident_registration.triangle_pixel_refine_workspace_bytes': True, 'contract_resident_registration_fastpath_positive:artifact.resident_warp_scratch_bytes': True, 'contract_resident_registration_fastpath_positive:resident_io_pipeline.warp_scratch_bytes': True, 'contract_resident_registration_fastpath_min:resident_registration.triangle_warp_batch_frame_count': True, 'contract_resident_registration_fastpath_component:triangle_descriptor_fit_batch': True, 'contract_resident_registration_fastpath_component:triangle_pixel_refine_batch': True}}
- PASS: `stack_engine_release_evidence_passed` - {'release_evidence_status': 'passed', 'stack_engine_contract_passed': None, 'stack_engine_contract_status': None}
- PASS: `stack_engine_default_ready` - {'acceptance_release_status': 'passed', 'contract_default_ready': None}
- PASS: `stack_engine_scope_all` - {'actual': 'all', 'required': 'all'}
- PASS: `runtime_repeat_evidence_ready` - {'present': True, 'run_count': 3, 'considered_run_count': 3, 'ignored_warmup_run_count': 0, 'ignored_warmup_labels': [], 'required_min_runtime_runs': 3, 'recommendation': 'best_observed:repeat03', 'best_label': 'repeat03', 'best_elapsed_s': 99.8, 'slowest_elapsed_s': 101.2, 'elapsed_ratio_vs_best': 1.0140280561122246, 'max_elapsed_ratio_vs_best': 1.25}

## Pipeline DQ Handoff

- Source: `acceptance_pipeline_contract`
- Status: `passed`
- Passed: `True`
- Integration outputs: `1`
- Integration maps: `6`
- Pixel verification enabled: `True`
- Rejection sample accounting: `passed`
- Rejection sample release scope: `not_required`, ready `True`, required `0`, verified `1`
- Sample accounting closure: `passed`
- Sample closure release scope: `required`, ready `True`, required `1`, present `1`
- Resident winsorized semantics: `not_available`, ready `True`, required `0`, legacy completions `0`
- Resident winsorized descriptor sources: `[]`


## Resident Registration Fastpath Handoff

- Present: `True`
- Status: `passed`
- Ready: `True`
- Required: `True`
- Source: `explicit_resident_artifacts_json`
- Path: `runs\checkpoints\s2_gate_327_fastpath_fixture\resident_artifacts.json`
- Mode: `similarity_cuda_triangle`
- Descriptor batch: `native_batch_shared_reference_device`
- Pixel refine batch: `native_batch_one_seed_per_frame`
- Triangle warp batch: `native_matrix_lanczos3_frames`
- Triangle warp batch frames: `3`
- Warp copy mode: `default_stream_async_device_to_device`
- Checks passed: `23`
- Checks failed: `0`
- Failed checks: `[]`
- Failed acceptance checks: `[]`


## Warp Quality Handoff

- Present: `True`
- Status: `passed`
- Ready: `True`
- Contract passed: `True`
- Output count: `1`
- Failed checks: `[]`
- Failed acceptance checks: `[]`
- Path: `runs\checkpoints\s2_gate_321_guardrails\warp_quality_contract.json`


## StackEngine Publication Runtime Default

- Present: `False`
- Status: `None`
- Passed: `None`
- Checks passed: `None`
- Raw ready: `None`
- Phase2 ready: `None`
- Phase2 check: `None`
- Raw drift: legacy=`None` failed_outputs=`None`
- Phase2 drift: legacy=`None` failed_outputs=`None`
- Direct runtime ready: `None`
- Direct runtime checks passed: `None`
- Direct runtime raw source: acceptance=`None` calibration=`None` lights=`None`
- Direct runtime Phase2 source: acceptance=`None` calibration=`None` lights=`None`


## Runtime Repeat Evidence

- Present: `True`
- Run count: `3`
- Recommendation: `best_observed:repeat03`
- Ratio vs best: `1.0140280561122246`
