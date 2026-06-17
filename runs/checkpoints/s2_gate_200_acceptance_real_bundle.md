# GLASS Acceptance Audit

- Status: passed
- Benchmark contract: phase2_m38_h_200_resident_cuda
- Contract bundle: passed
- Pipeline contract: passed
- StackEngine contract: passed
- DQ provenance records: 2
- Frame accounting artifact: C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\frame_accounting.json
- Speedup vs WBPP: 58.099101701945926
- Frame counts: {'light': 200, 'bias': 20, 'dark': 20, 'flat': 20}
- Shape match: True
- RMS diff: 0.0014945534429799121
- abs diff p99: 0.00043544556712731865
- Coverage fraction: 0.9577924192878646

## Checks

## Pipeline Contract Evidence

- Status: passed
- Required by benchmark contract: True
- Pipeline contract path: C:\glass_runs\phase2_s2_gate_200_real_bundle_acceptance\guardrails\pipeline_contract.json
- Pipeline contract audit type: pipeline_invariant_contract
- Pipeline contract passed: True
- Pipeline contract checks: 10
- Acceptance pipeline checks passed: 8
- Acceptance pipeline checks failed: 0
- Failed pipeline checks: []

- PASS: pipeline_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\pipeline_contract.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: contract_pipeline_contract_present - {'required': True, 'present': True, 'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\pipeline_contract.json'}
- PASS: contract_pipeline_contract_audit_type - {'actual': 'pipeline_invariant_contract', 'required': 'pipeline_invariant_contract'}
- PASS: contract_pipeline_contract_passed - {'actual': True, 'status': 'passed', 'failed_checks': []}
- PASS: contract_pipeline_contract_min_check_count - {'actual': 10, 'required_min': 1}
- PASS: contract_pipeline_contract_check:integration_resident_result_contract - {'required': 'integration_resident_result_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_no_failed_checks - {'failed_checks': []}

## StackEngine Default Promotion Evidence

- Status: passed
- Required by benchmark contract: True
- StackEngine contract path: C:\glass_runs\phase2_s2_gate_200_real_bundle_acceptance\guardrails\stack_engine_contract.json
- StackEngine contract audit type: stack_engine_default_contract
- StackEngine contract passed: True
- StackEngine contract scope: all
- Default promotion ready: True
- Default promotion status: ready
- Default promotion gaps: 0
- Default promotion blockers: 0
- Adoption recommendation: stack_engine_default_ready
- Acceptance StackEngine checks passed: 11
- Acceptance StackEngine checks failed: 0
- Failed StackEngine checks: []

- PASS: stack_engine_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: contract_stack_engine_default_promotion_present - {'required': True, 'present': True, 'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\stack_engine_contract.json'}
- PASS: contract_stack_engine_default_promotion_audit_type - {'actual': 'stack_engine_default_contract', 'required': 'stack_engine_default_contract'}
- PASS: contract_stack_engine_default_promotion_contract_passed - {'actual': True, 'status': 'passed', 'failed_checks': []}
- PASS: contract_stack_engine_default_promotion_ready - {'actual': True, 'status': 'ready', 'blockers': []}
- PASS: contract_stack_engine_default_promotion_scope - {'actual': 'all', 'required': 'all'}
- PASS: contract_stack_engine_default_promotion_recommendation - {'actual': 'stack_engine_default_ready', 'required': 'stack_engine_default_ready'}
- PASS: contract_stack_engine_default_promotion_gap_count - {'actual': 0, 'required_max': 0}
- PASS: contract_stack_engine_default_promotion_blocker_count - {'actual': 0, 'required_max': 0}
- PASS: contract_stack_engine_default_promotion_no_failed_checks - {'failed_checks': []}

- PASS: minimum_light_frames - {'actual': 200, 'required': 200}
- PASS: minimum_bias_frames - {'actual': 20, 'required': 20}
- PASS: minimum_dark_frames - {'actual': 20, 'required': 20}
- PASS: minimum_flat_frames - {'actual': 20, 'required': 20}
- PASS: minimum_active_frames - {'actual': 193, 'required': 1}
- PASS: minimum_speedup - {'actual': 58.099101701945926, 'required': 2.0}
- PASS: shape_match - {'actual': True, 'required': True}
- PASS: minimum_coverage_fraction - {'actual': 0.9577924192878646, 'required': 0.95}
- PASS: maximum_rms_diff - {'actual': 0.0014945534429799121, 'required_max': 0.01}
- PASS: maximum_abs_diff_p99 - {'actual': 0.00043544556712731865, 'required_max': 0.01}
- PASS: contract_bundle_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\acceptance_contract_bundle.json', 'exists': True}
- PASS: contract_bundle_type - {'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\acceptance_contract_bundle.json', 'artifact_type': 'glass_acceptance_contract_bundle', 'required': 'glass_acceptance_contract_bundle'}
- PASS: pipeline_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\pipeline_contract.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: stack_engine_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: contract_minimum_light_frames - {'actual': 200, 'required': 200}
- PASS: contract_minimum_bias_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_dark_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_flat_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_active_light_frames - {'actual': 193, 'required': 190}
- PASS: contract_max_runtime_vs_release_baseline - {'actual_s': 18.80478299999959, 'release_baseline_s': 30.361440100008622, 'max_regression_factor': 1.3, 'required_max_s': 39.46987213001121}
- PASS: contract_minimum_speedup_vs_reference - {'actual': 58.099101701945926, 'required': 20.0}
- PASS: contract_required_command_token:--backend cuda - {'token': '--backend cuda', 'run_command_present': True}
- PASS: contract_required_command_token:--until-stage integration - {'token': '--until-stage integration', 'run_command_present': True}
- PASS: contract_required_command_token:--memory-mode resident - {'token': '--memory-mode resident', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-registration similarity_cuda_triangle - {'token': '--resident-registration similarity_cuda_triangle', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-warp-interpolation lanczos3 - {'token': '--resident-warp-interpolation lanczos3', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-warp-clamping-threshold 0.3 - {'token': '--resident-warp-clamping-threshold 0.3', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-star-threshold 350 - {'token': '--resident-star-threshold 350', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-star-max-candidates 48 - {'token': '--resident-star-max-candidates 48', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-star-grid-rows 16 - {'token': '--resident-star-grid-rows 16', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-triangle-pixel-refine-coarse-stride 4 - {'token': '--resident-triangle-pixel-refine-coarse-stride 4', 'run_command_present': True}
- PASS: contract_required_command_token:--resident-triangle-pixel-refine-final-stride 8 - {'token': '--resident-triangle-pixel-refine-final-stride 8', 'run_command_present': True}
- PASS: contract_required_command_token:--reference-frame-id F000196 - {'token': '--reference-frame-id F000196', 'run_command_present': True}
- PASS: contract_required_command_token:--local-normalization off - {'token': '--local-normalization off', 'run_command_present': True}
- PASS: contract_required_command_token:--integration-weighting none - {'token': '--integration-weighting none', 'run_command_present': True}
- PASS: contract_required_command_token:--integration-rejection winsorized_sigma - {'token': '--integration-rejection winsorized_sigma', 'run_command_present': True}
- PASS: contract_required_command_token:--flat-floor 0.05 - {'token': '--flat-floor 0.05', 'run_command_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0100 - {'token': '--exclude-frame-id LIGHT_H_0100', 'run_command_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0153 - {'token': '--exclude-frame-id LIGHT_H_0153', 'run_command_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0154 - {'token': '--exclude-frame-id LIGHT_H_0154', 'run_command_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0155 - {'token': '--exclude-frame-id LIGHT_H_0155', 'run_command_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0156 - {'token': '--exclude-frame-id LIGHT_H_0156', 'run_command_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0157 - {'token': '--exclude-frame-id LIGHT_H_0157', 'run_command_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0158 - {'token': '--exclude-frame-id LIGHT_H_0158', 'run_command_present': True}
- PASS: contract_required_command_token_group:resident_h2d_or_runtime_preset - {'any_of': ['--resident-h2d-mode pinned_ring', '--resident-runtime-preset throughput-v1'], 'matched': [], 'artifact_matches': [{'artifact': 'resident_artifacts.json', 'artifact_index': 0, 'resident_io_pipeline': {'h2d_mode': 'pinned_ring'}, 'token': '--resident-h2d-mode pinned_ring'}, {'artifact': 'resident_artifacts.json', 'artifact_index': 0, 'resident_io_pipeline': {'h2d_mode': 'pinned_ring', 'prefetch_frames': 12, 'prefetch_workers': 7, 'calibration_batch_requested_frames': 8, 'calibration_batch_requested_streams': 4, 'calibration_wave_requested_frames': 2, 'calibration_release_mode_requested': 'callback_queue', 'calibration_release_mode_effective': 'callback_queue'}, 'token': '--resident-runtime-preset throughput-v1', 'preset': 'throughput-v1'}], 'resident_io_pipeline_records': 1, 'run_command_present': True}
- PASS: contract_required_command_token_group:resident_star_grid_cols - {'any_of': ['--resident-star-grid-cols 24', '--resident-star-grid-cols 28'], 'matched': ['--resident-star-grid-cols 28'], 'artifact_matches': [], 'resident_io_pipeline_records': 1, 'run_command_present': True}
- PASS: contract_compare_scale - {'actual': 8.764434957115609e-06, 'required': 8.764434957115609e-06, 'abs_tol': 1e-12, 'rel_tol': 1e-09}
- PASS: contract_compare_offset - {'actual': 0.0006274500691899127, 'required': 0.0006274500691899127, 'abs_tol': 1e-12, 'rel_tol': 1e-09}
- PASS: contract_compare_min_coverage - {'actual': 190.0, 'required': 190.0}
- PASS: contract_max_rms_diff - {'actual': 0.0014945534429799121, 'required_max': 0.01}
- PASS: contract_max_abs_diff_p99 - {'actual': 0.00043544556712731865, 'required_max': 0.01}
- PASS: contract_min_coverage_fraction - {'actual': 0.9577924192878646, 'required': 0.95}
- PASS: contract_dq_provenance_records - {'actual': 2, 'required_min': 1}
- PASS: contract_dq_source_schema:resident_dq_coverage_provenance - {'required': 'resident_dq_coverage_provenance', 'available': ['resident_dq_coverage_provenance']}
- PASS: contract_dq_engine:cuda_resident_stack - {'required': 'cuda_resident_stack', 'available': ['cuda_resident_stack']}
- PASS: contract_dq_min_active_frame_count - {'actual_max': 193.0, 'required_min': 190.0}
- PASS: contract_dq_map_path_present - {'records_with_dq_map_path': 2}
- PASS: contract_dq_map_exists - {'records_with_existing_dq_map': 2}
- PASS: contract_dq_coverage_map_path_present - {'records_with_coverage_map_path': 2}
- PASS: contract_dq_summary_field:zero_coverage_pixels - {'required': 'zero_coverage_pixels'}
- PASS: contract_dq_summary_field:partial_coverage_pixels - {'required': 'partial_coverage_pixels'}
- PASS: contract_dq_output_flag:valid - {'required': 'valid', 'available_values': [20892861.0, 20892861.0]}
- PASS: contract_dq_output_flag:warp_edge - {'required': 'warp_edge', 'available_values': [5394370.0, 5394370.0]}
- PASS: contract_dq_output_flag:low_rejected - {'required': 'low_rejected', 'available_values': [13114786.0, 13114786.0]}
- PASS: contract_dq_output_flag:high_rejected - {'required': 'high_rejected', 'available_values': [32370393.0, 32370393.0]}
- PASS: contract_dq_positive_output_flag:valid - {'required': 'valid', 'available_values': [20892861.0, 20892861.0]}
- PASS: contract_dq_positive_output_flag:warp_edge - {'required': 'warp_edge', 'available_values': [5394370.0, 5394370.0]}
- PASS: contract_dq_map_pixel_verification - {'verified_records': 2, 'error_records': 0, 'errors': []}
- PASS: contract_dq_map_summary_match:valid - {'matches': [{'actual': 20892861, 'summary': 20892861, 'delta': 0, 'passed': True}, {'actual': 20892861, 'summary': 20892861, 'delta': 0, 'passed': True}]}
- PASS: contract_dq_map_summary_match:warp_edge - {'matches': [{'actual': 5394370, 'summary': 5394370, 'delta': 0, 'passed': True}, {'actual': 5394370, 'summary': 5394370, 'delta': 0, 'passed': True}]}
- PASS: contract_dq_map_summary_match:low_rejected - {'matches': [{'actual': 13114786, 'summary': 13114786, 'delta': 0, 'passed': True}, {'actual': 13114786, 'summary': 13114786, 'delta': 0, 'passed': True}]}
- PASS: contract_dq_map_summary_match:high_rejected - {'matches': [{'actual': 32370393, 'summary': 32370393, 'delta': 0, 'passed': True}, {'actual': 32370393, 'summary': 32370393, 'delta': 0, 'passed': True}]}
- PASS: contract_coverage_map_pixel_verification - {'verified_records': 2, 'error_records': 0, 'errors': []}
- PASS: contract_coverage_map_finite_pixels_match - {'matches': [{'actual': 61651200, 'provenance': 61651200, 'delta': 0, 'passed': True}, {'actual': 61651200, 'provenance': 61651200, 'delta': 0, 'passed': True}]}
- PASS: contract_coverage_zero_pixels_match_no_data - {'matches': [{'actual': 0, 'summary': 0, 'delta': 0, 'passed': True}, {'actual': 0, 'summary': 0, 'delta': 0, 'passed': True}]}
- PASS: contract_low_rejection_map_available_or_skipped - {'verified_records': 2, 'missing_or_skipped_records': 0, 'allow_skipped_by_policy': True}
- PASS: contract_low_rejection_map_positive_pixels_match:low_rejected - {'matches': [{'actual': 13114786, 'summary': 13114786, 'delta': 0, 'passed': True}, {'actual': 13114786, 'summary': 13114786, 'delta': 0, 'passed': True}]}
- PASS: contract_high_rejection_map_available_or_skipped - {'verified_records': 2, 'missing_or_skipped_records': 0, 'allow_skipped_by_policy': True}
- PASS: contract_high_rejection_map_positive_pixels_match:high_rejected - {'matches': [{'actual': 32370393, 'summary': 32370393, 'delta': 0, 'passed': True}, {'actual': 32370393, 'summary': 32370393, 'delta': 0, 'passed': True}]}
- PASS: contract_rejection_map_sum_matches_provenance - {'matches': [{'actual': 62488423, 'provenance': 62488423, 'delta': 0, 'passed': True}, {'actual': 62488423, 'provenance': 62488423, 'delta': 0, 'passed': True}], 'tolerance_samples': 0}
- PASS: contract_dq_source_term:geometric_warp_coverage - {'required': 'geometric_warp_coverage'}
- PASS: contract_frame_accounting_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\frame_accounting.json', 'exists': True}
- PASS: contract_frame_accounting_input_light_frames - {'actual': 200, 'required': 200}
- PASS: contract_frame_accounting_integrated_frames - {'actual': 193, 'required': 193}
- PASS: contract_frame_accounting_zero_weight_frames - {'actual': 7, 'required': 7}
- PASS: contract_frame_accounting_registration_accepted_frames - {'actual': 193, 'required': 193}
- PASS: contract_frame_accounting_min_integrated_frames - {'actual': 193, 'required_min': 190}
- PASS: contract_frame_accounting_integration_source_stage - {'actual': 'resident_calibrated_stack', 'required': 'resident_calibrated_stack'}
- PASS: contract_frame_accounting_final_status:integrated - {'actual': 193, 'calculated_from_rows': 193, 'required': 193}
- PASS: contract_frame_accounting_final_status:zero_weight - {'actual': 7, 'calculated_from_rows': 7, 'required': 7}
- PASS: contract_frame_accounting_matches_integration_weights - {'matches': [{'field': 'input_light_frames', 'accounting': 200, 'weights': 200}, {'field': 'integrated_frames', 'accounting': 193, 'weights': 193}, {'field': 'zero_weight_frames', 'accounting': 7, 'weights': 7}], 'invalid_weights': 0}
- PASS: contract_frame_accounting_matches_speedup_summary - {'matches': [{'field': 'integrated_frames', 'accounting': 193, 'speedup_summary': 193}, {'field': 'zero_weight_frames', 'accounting': 7, 'speedup_summary': 7}]}
- PASS: contract_frame_accounting_matches_dq_active_frames - {'accounting_integrated_frames': 193, 'dq_active_frame_counts': [193.0, 193.0]}
- PASS: contract_frame_accounting_matches_registration - {'accounting_registration_accepted_frames': 193, 'registration_accepted_frames': 193, 'registration_status_counts': {'ok': 192, 'excluded': 7, 'reference': 1}}
- PASS: contract_pipeline_contract_present - {'required': True, 'present': True, 'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\pipeline_contract.json'}
- PASS: contract_pipeline_contract_audit_type - {'actual': 'pipeline_invariant_contract', 'required': 'pipeline_invariant_contract'}
- PASS: contract_pipeline_contract_passed - {'actual': True, 'status': 'passed', 'failed_checks': []}
- PASS: contract_pipeline_contract_min_check_count - {'actual': 10, 'required_min': 1}
- PASS: contract_pipeline_contract_check:integration_resident_result_contract - {'required': 'integration_resident_result_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_no_failed_checks - {'failed_checks': []}
- PASS: contract_stack_engine_default_promotion_present - {'required': True, 'present': True, 'path': 'C:\\glass_runs\\phase2_s2_gate_200_real_bundle_acceptance\\guardrails\\stack_engine_contract.json'}
- PASS: contract_stack_engine_default_promotion_audit_type - {'actual': 'stack_engine_default_contract', 'required': 'stack_engine_default_contract'}
- PASS: contract_stack_engine_default_promotion_contract_passed - {'actual': True, 'status': 'passed', 'failed_checks': []}
- PASS: contract_stack_engine_default_promotion_ready - {'actual': True, 'status': 'ready', 'blockers': []}
- PASS: contract_stack_engine_default_promotion_scope - {'actual': 'all', 'required': 'all'}
- PASS: contract_stack_engine_default_promotion_recommendation - {'actual': 'stack_engine_default_ready', 'required': 'stack_engine_default_ready'}
- PASS: contract_stack_engine_default_promotion_gap_count - {'actual': 0, 'required_max': 0}
- PASS: contract_stack_engine_default_promotion_blocker_count - {'actual': 0, 'required_max': 0}
- PASS: contract_stack_engine_default_promotion_no_failed_checks - {'failed_checks': []}

## DQ Provenance

- integration_results.json[0] schema=resident_dq_coverage_provenance engine=cuda_resident_stack stage=integration item=H dq_map_exists=True legacy_normalized=False pixel_verification=verified coverage_verification=verified
- resident_artifacts.json[0] schema=resident_dq_coverage_provenance engine=cuda_resident_stack stage=integration item=H dq_map_exists=True legacy_normalized=False pixel_verification=verified coverage_verification=verified

## Frame Accounting

- Exists: True
- Input lights: 200
- Integrated frames: 193
- Zero-weight frames: 7
- Final status counts: {'integrated': 193, 'zero_weight': 7}
- Exception summary: {'count': 7, 'final_status_counts': {'zero_weight': 7}, 'primary_stage_counts': {'integration': 7}}
- Integration weight counts: {'total': 200, 'positive': 193, 'zero': 7, 'invalid': 0}
- Registration counts: {'total': 200, 'accepted': 193, 'zero_weight_statuses': 7, 'status_counts': {'ok': 192, 'excluded': 7, 'reference': 1}}
- Exception frame: F000160 status=zero_weight stage=integration reason=integration weight is zero
- Exception frame: F000213 status=zero_weight stage=integration reason=integration weight is zero
- Exception frame: F000214 status=zero_weight stage=integration reason=integration weight is zero
- Exception frame: F000215 status=zero_weight stage=integration reason=integration weight is zero
- Exception frame: F000216 status=zero_weight stage=integration reason=integration weight is zero
- Exception frame: F000217 status=zero_weight stage=integration reason=integration weight is zero
- Exception frame: F000218 status=zero_weight stage=integration reason=integration weight is zero

## Performance Regression Diagnostics

- Status: regressed
- Worst stage: output_write actual=2.2748387999999977s baseline=0.9690760000376031s factor=2.347430748374459
- regressed: output_write actual=2.2748387999999977s baseline=0.9690760000376031s delta=1.3057627999623946s factor=2.347430748374459
- informational_cumulative: light_fits_open actual=0.3095644000204629s baseline=0.25601840019226074s delta=0.053545999828202184s factor=1.2091490290853746
- ok: resident_integration actual=0.3265083999995113s baseline=0.2955454000039026s delta=0.030962999995608698s factor=1.1047656299005155
- informational_cumulative: light_read_decode_worker actual=41.274104000009174s baseline=45.18920989986509s delta=-3.9151058998559165s factor=0.9133619306792172
- informational_cumulative: light_fits_materialize_decode actual=36.670810600009645s baseline=40.36132279911544s delta=-3.6905121991057968s factor=0.9085631504826032
- ok: light_h2d_calibrate_store actual=2.3060552000006282s baseline=2.7688988983863965s delta=-0.4628436983857682s factor=0.832841965210252
- ok: light_read_upload_calibrate actual=7.153982399999222s baseline=15.546634200029075s delta=-8.392651800029853s factor=0.46016277915549353
- ok: resident_registration_component_accounted actual=3.9273199000216255s baseline=15.875620800070465s delta=-11.948300900048839s factor=0.2473805559782704

## Optimization Guidance

- Primary target: io_upload_calibration_pipeline
- Exception context: {'count': 7, 'dominant_stage': 'integration', 'primary_stage_counts': {'integration': 7}, 'final_status_counts': {'zero_weight': 7}, 'sample_frame_ids': ['F000160', 'F000213', 'F000214', 'F000215', 'F000216', 'F000217', 'F000218'], 'note': 'Exception frames explain active-frame count drift; timing priorities remain based on wall-clock stages.'}
- #1 I/O + upload + calibration overlap stage=light_read_upload_calibrate current=7.153982399999222s baseline=15.546634200029075s factor=0.46016277915549353 action=Use deeper double/multi buffering, pinned host rings, async H2D, and larger batches so GPU calibration overlaps CPU FITS decode and disk reads.
- #2 Output-map write policy stage=output_write current=2.2748387999999977s baseline=0.9690760000376031s factor=2.347430748374459 action=Use science/minimal map policies for speed runs and keep full audit maps for validation runs.
- #3 Resident registration/warp batching stage=resident_registration_warp current=2.0032748999929026s baseline=10.903585300431587s factor=0.18372625561186823 action=Keep star tables, descriptors, candidate scoring, pixel refinement, and warp scheduling resident on the GPU; reduce per-frame Python orchestration and host/device synchronization.
- #4 Resident master-frame cache stage=master_build_or_load current=0.46706669999912265s baseline=9.85976749996189s factor=0.047370964883393846 action=Reuse the shared resident master cache when calibration inputs and policies are unchanged.

## Clean-room

- Acceptance audit consumes GLASS artifacts and user-generated PixInsight/WBPP black-box timing/output metadata only.
