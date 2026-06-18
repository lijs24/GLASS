# GLASS Acceptance Audit

- Status: passed
- Benchmark contract: phase2_m38_h_200_resident_cuda
- Contract bundle: None
- Pipeline contract: passed
- StackEngine contract: passed
- DQ provenance records: 2
- Frame accounting artifact: C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view\frame_accounting.json
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
- Pipeline contract path: runs\checkpoints\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json
- Pipeline contract audit type: pipeline_invariant_contract
- Pipeline contract passed: True
- Pipeline contract checks: 19
- Acceptance pipeline checks passed: 12
- Acceptance pipeline checks failed: 0
- Failed pipeline checks: []

### Rejection Sample Accounting

- Status: passed
- Check passed: True
- Pixel verification enabled: True
- Accounting rows: 1
- Required rows: 1
- Verified rows: 1
- Failed rows: 0

### Integration Engine Policy

- Status: passed
- Check passed: True
- Non-resident outputs: 0
- Resident outputs: 1
- Failed rows: 0

### StackEngine Runtime Default Path

- Status: passed
- Check passed: True
- Master rows: 3
- Master StackEngine rows: 0
- Master resident rows: 3
- Legacy master rows: 0
- Integration outputs: 1
- Integration StackEngine defaults: 0
- Integration resident outputs: 1
- Explicit CUDA fast paths: 0
- Failed master rows: 0
- Failed integration rows: 0

### Integration Sample Accounting Closure

- Status: passed
- Check passed: True
- Output rows: 1
- Present rows: 0
- Required rows: 0
- Failed rows: 0

- PASS: pipeline_contract_present - {'path': 'runs\\checkpoints\\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: pipeline_contract_integration_default_engine_policy - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_contract_stack_engine_runtime_default - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'integration_output_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': []}
- PASS: contract_pipeline_contract_present - {'required': True, 'present': True, 'path': 'runs\\checkpoints\\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json'}
- PASS: contract_pipeline_contract_audit_type - {'actual': 'pipeline_invariant_contract', 'required': 'pipeline_invariant_contract'}
- PASS: contract_pipeline_contract_passed - {'actual': True, 'status': 'passed', 'failed_checks': []}
- PASS: contract_pipeline_contract_min_check_count - {'actual': 19, 'required_min': 3}
- PASS: contract_pipeline_contract_check:calibration_master_surface_contract - {'required': 'calibration_master_surface_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_default_engine_policy', 'stack_engine_runtime_default_path', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_sample_accounting_closure', 'calibration_master_surfaces_present', 'calibration_master_surface_contract', 'resident_calibration_surface_contract', 'resident_calibrated_lights_present', 'resident_calibrated_light_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'integration_rejection_sample_counts_match_maps', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_check:resident_calibrated_light_contract - {'required': 'resident_calibrated_light_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_default_engine_policy', 'stack_engine_runtime_default_path', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_sample_accounting_closure', 'calibration_master_surfaces_present', 'calibration_master_surface_contract', 'resident_calibration_surface_contract', 'resident_calibrated_lights_present', 'resident_calibrated_light_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'integration_rejection_sample_counts_match_maps', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_check:integration_resident_result_contract - {'required': 'integration_resident_result_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_default_engine_policy', 'stack_engine_runtime_default_path', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_sample_accounting_closure', 'calibration_master_surfaces_present', 'calibration_master_surface_contract', 'resident_calibration_surface_contract', 'resident_calibrated_lights_present', 'resident_calibrated_light_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'integration_rejection_sample_counts_match_maps', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_no_failed_checks - {'failed_checks': []}

## StackEngine Default Promotion Evidence

- Status: passed
- Required by benchmark contract: True
- StackEngine contract path: runs\checkpoints\s2_gate_211_stack_engine_contract.json
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

- PASS: stack_engine_contract_present - {'path': 'runs\\checkpoints\\s2_gate_211_stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: contract_stack_engine_default_promotion_present - {'required': True, 'present': True, 'path': 'runs\\checkpoints\\s2_gate_211_stack_engine_contract.json'}
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
- PASS: pipeline_contract_present - {'path': 'runs\\checkpoints\\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: pipeline_contract_integration_default_engine_policy - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_contract_stack_engine_runtime_default - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'integration_output_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': []}
- PASS: stack_engine_contract_present - {'path': 'runs\\checkpoints\\s2_gate_211_stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: contract_minimum_light_frames - {'actual': 200, 'required': 200}
- PASS: contract_minimum_bias_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_dark_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_flat_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_active_light_frames - {'actual': 193, 'required': 190}
- PASS: contract_max_runtime_vs_release_baseline - {'actual_s': 18.80478299999959, 'release_baseline_s': 30.361440100008622, 'max_regression_factor': 1.3, 'required_max_s': 39.46987213001121}
- PASS: contract_minimum_speedup_vs_reference - {'actual': 58.099101701945926, 'required': 20.0}
- PASS: contract_required_command_token:--backend cuda - {'token': '--backend cuda', 'command_match': True, 'artifact_match': {'token': '--backend cuda', 'source': 'run_timing', 'field': 'backend', 'actual': 'cuda', 'requested': None, 'reason': None}, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--until-stage integration - {'token': '--until-stage integration', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--memory-mode resident - {'token': '--memory-mode resident', 'command_match': True, 'artifact_match': {'token': '--memory-mode resident', 'source': 'run_timing', 'field': 'memory_mode', 'actual': 'resident', 'requested': None, 'reason': None}, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-registration similarity_cuda_triangle - {'token': '--resident-registration similarity_cuda_triangle', 'command_match': True, 'artifact_match': {'token': '--resident-registration similarity_cuda_triangle', 'source': 'resident_artifacts', 'field': 'resident_registration.mode', 'actual': 'similarity_cuda_triangle', 'artifact': 'C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\resident_artifacts.json'}, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-warp-interpolation lanczos3 - {'token': '--resident-warp-interpolation lanczos3', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-warp-clamping-threshold 0.3 - {'token': '--resident-warp-clamping-threshold 0.3', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-star-threshold 350 - {'token': '--resident-star-threshold 350', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-star-max-candidates 48 - {'token': '--resident-star-max-candidates 48', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-star-grid-rows 16 - {'token': '--resident-star-grid-rows 16', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-triangle-pixel-refine-coarse-stride 4 - {'token': '--resident-triangle-pixel-refine-coarse-stride 4', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-triangle-pixel-refine-final-stride 8 - {'token': '--resident-triangle-pixel-refine-final-stride 8', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--reference-frame-id F000196 - {'token': '--reference-frame-id F000196', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--local-normalization off - {'token': '--local-normalization off', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--integration-weighting none - {'token': '--integration-weighting none', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--integration-rejection winsorized_sigma - {'token': '--integration-rejection winsorized_sigma', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--flat-floor 0.05 - {'token': '--flat-floor 0.05', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0100 - {'token': '--exclude-frame-id LIGHT_H_0100', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0153 - {'token': '--exclude-frame-id LIGHT_H_0153', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0154 - {'token': '--exclude-frame-id LIGHT_H_0154', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0155 - {'token': '--exclude-frame-id LIGHT_H_0155', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0156 - {'token': '--exclude-frame-id LIGHT_H_0156', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0157 - {'token': '--exclude-frame-id LIGHT_H_0157', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--exclude-frame-id LIGHT_H_0158 - {'token': '--exclude-frame-id LIGHT_H_0158', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token_group:resident_h2d_or_runtime_preset - {'any_of': ['--resident-h2d-mode pinned_ring', '--resident-runtime-preset throughput-v1'], 'matched': [], 'artifact_matches': [{'artifact': 'resident_artifacts.json', 'artifact_index': 0, 'resident_io_pipeline': {'h2d_mode': 'pinned_ring'}, 'token': '--resident-h2d-mode pinned_ring', 'source': 'resident_io_pipeline'}, {'artifact': 'resident_artifacts.json', 'artifact_index': 0, 'resident_io_pipeline': {'h2d_mode': 'pinned_ring', 'prefetch_frames': 12, 'prefetch_workers': 7, 'calibration_batch_requested_frames': 8, 'calibration_batch_requested_streams': 4, 'calibration_wave_requested_frames': 2, 'calibration_release_mode_requested': 'callback_queue', 'calibration_release_mode_effective': 'callback_queue'}, 'token': '--resident-runtime-preset throughput-v1', 'preset': 'throughput-v1', 'source': 'resident_io_pipeline'}], 'resident_io_pipeline_records': 1, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token_group:resident_star_grid_cols - {'any_of': ['--resident-star-grid-cols 24', '--resident-star-grid-cols 28'], 'matched': ['--resident-star-grid-cols 28'], 'artifact_matches': [], 'resident_io_pipeline_records': 1, 'run_command_present': True, 'run_timing_present': True}
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
- PASS: contract_frame_accounting_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view\\frame_accounting.json', 'exists': True}
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
- PASS: contract_resident_registration_fastpath_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\resident_artifacts.json', 'exists': True, 'available': True, 'artifact_count': 1}
- PASS: contract_resident_registration_fastpath_value:resident_registration.mode - {'field': 'resident_registration.mode', 'actual': 'similarity_cuda_triangle', 'required': 'similarity_cuda_triangle'}
- PASS: contract_resident_registration_fastpath_value:resident_registration.triangle_descriptor_fit_batch_mode - {'field': 'resident_registration.triangle_descriptor_fit_batch_mode', 'actual': 'native_batch_shared_reference_device', 'required': 'native_batch_shared_reference_device'}
- PASS: contract_resident_registration_fastpath_value:resident_registration.triangle_descriptor_fit_batch_timing_model - {'field': 'resident_registration.triangle_descriptor_fit_batch_timing_model', 'actual': 'per_frame_reused_buffers_sync_timed', 'required': 'per_frame_reused_buffers_sync_timed'}
- PASS: contract_resident_registration_fastpath_value:resident_registration.triangle_pixel_refine_batch_mode - {'field': 'resident_registration.triangle_pixel_refine_batch_mode', 'actual': 'native_batch_one_seed_per_frame', 'required': 'native_batch_one_seed_per_frame'}
- PASS: contract_resident_registration_fastpath_value:resident_registration.triangle_pixel_refine_batch_metric_mode - {'field': 'resident_registration.triangle_pixel_refine_batch_metric_mode', 'actual': 'flattened_frame_candidate_grid', 'required': 'flattened_frame_candidate_grid'}
- PASS: contract_resident_registration_fastpath_value:resident_registration.triangle_warp_batch_mode - {'field': 'resident_registration.triangle_warp_batch_mode', 'actual': 'native_matrix_lanczos3_frames', 'required': 'native_matrix_lanczos3_frames'}
- PASS: contract_resident_registration_fastpath_value:artifact.resident_warp_copy_mode - {'field': 'artifact.resident_warp_copy_mode', 'actual': 'default_stream_async_device_to_device', 'required': 'default_stream_async_device_to_device'}
- PASS: contract_resident_registration_fastpath_value:resident_io_pipeline.warp_copy_mode - {'field': 'resident_io_pipeline.warp_copy_mode', 'actual': 'default_stream_async_device_to_device', 'required': 'default_stream_async_device_to_device'}
- PASS: contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_batch - {'field': 'resident_registration.triangle_descriptor_fit_batch', 'actual': True, 'required': True}
- PASS: contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_reference_device_reuse - {'field': 'resident_registration.triangle_descriptor_fit_reference_device_reuse', 'actual': True, 'required': True}
- PASS: contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_moving_device_reuse - {'field': 'resident_registration.triangle_descriptor_fit_moving_device_reuse', 'actual': True, 'required': True}
- PASS: contract_resident_registration_fastpath_true:resident_registration.triangle_descriptor_fit_output_device_reuse - {'field': 'resident_registration.triangle_descriptor_fit_output_device_reuse', 'actual': True, 'required': True}
- PASS: contract_resident_registration_fastpath_true:resident_registration.triangle_pixel_refine_batch - {'field': 'resident_registration.triangle_pixel_refine_batch', 'actual': True, 'required': True}
- PASS: contract_resident_registration_fastpath_true:resident_registration.triangle_warp_batch - {'field': 'resident_registration.triangle_warp_batch', 'actual': True, 'required': True}
- PASS: contract_resident_registration_fastpath_positive:resident_registration.triangle_descriptor_fit_reference_device_bytes - {'field': 'resident_registration.triangle_descriptor_fit_reference_device_bytes', 'actual': 5944.0, 'required': '> 0'}
- PASS: contract_resident_registration_fastpath_positive:resident_registration.triangle_descriptor_fit_moving_device_bytes - {'field': 'resident_registration.triangle_descriptor_fit_moving_device_bytes', 'actual': 6624.0, 'required': '> 0'}
- PASS: contract_resident_registration_fastpath_positive:resident_registration.triangle_descriptor_fit_output_device_bytes - {'field': 'resident_registration.triangle_descriptor_fit_output_device_bytes', 'actual': 4163384.0, 'required': '> 0'}
- PASS: contract_resident_registration_fastpath_positive:resident_registration.triangle_pixel_refine_workspace_bytes - {'field': 'resident_registration.triangle_pixel_refine_workspace_bytes', 'actual': 1617408.0, 'required': '> 0'}
- PASS: contract_resident_registration_fastpath_positive:artifact.resident_warp_scratch_bytes - {'field': 'artifact.resident_warp_scratch_bytes', 'actual': 493209636.0, 'required': '> 0'}
- PASS: contract_resident_registration_fastpath_positive:resident_io_pipeline.warp_scratch_bytes - {'field': 'resident_io_pipeline.warp_scratch_bytes', 'actual': 493209636.0, 'required': '> 0'}
- PASS: contract_resident_registration_fastpath_min:resident_registration.triangle_warp_batch_frame_count - {'field': 'resident_registration.triangle_warp_batch_frame_count', 'actual': 188.0, 'required_min': 180.0}
- PASS: contract_resident_registration_fastpath_component:triangle_descriptor_fit_batch - {'component': 'triangle_descriptor_fit_batch', 'actual_s': 0.06670789999952831}
- PASS: contract_resident_registration_fastpath_component:triangle_pixel_refine_batch - {'component': 'triangle_pixel_refine_batch', 'actual_s': 1.0763637999989442}
- PASS: contract_pipeline_contract_present - {'required': True, 'present': True, 'path': 'runs\\checkpoints\\s2_gate_304_pipeline_contract_resident_calibration_direct_visibility.json'}
- PASS: contract_pipeline_contract_audit_type - {'actual': 'pipeline_invariant_contract', 'required': 'pipeline_invariant_contract'}
- PASS: contract_pipeline_contract_passed - {'actual': True, 'status': 'passed', 'failed_checks': []}
- PASS: contract_pipeline_contract_min_check_count - {'actual': 19, 'required_min': 3}
- PASS: contract_pipeline_contract_check:calibration_master_surface_contract - {'required': 'calibration_master_surface_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_default_engine_policy', 'stack_engine_runtime_default_path', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_sample_accounting_closure', 'calibration_master_surfaces_present', 'calibration_master_surface_contract', 'resident_calibration_surface_contract', 'resident_calibrated_lights_present', 'resident_calibrated_light_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'integration_rejection_sample_counts_match_maps', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_check:resident_calibrated_light_contract - {'required': 'resident_calibrated_light_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_default_engine_policy', 'stack_engine_runtime_default_path', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_sample_accounting_closure', 'calibration_master_surfaces_present', 'calibration_master_surface_contract', 'resident_calibration_surface_contract', 'resident_calibrated_lights_present', 'resident_calibrated_light_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'integration_rejection_sample_counts_match_maps', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_check:integration_resident_result_contract - {'required': 'integration_resident_result_contract', 'available': ['integration_artifact_exists', 'integration_outputs_present', 'integration_default_engine_policy', 'stack_engine_runtime_default_path', 'integration_output_maps_available', 'integration_dq_contract', 'integration_stack_result_contract', 'integration_resident_result_contract', 'integration_sample_accounting_closure', 'calibration_master_surfaces_present', 'calibration_master_surface_contract', 'resident_calibration_surface_contract', 'resident_calibrated_lights_present', 'resident_calibrated_light_contract', 'integration_dq_map_pixels_match_summary', 'integration_coverage_map_pixels_match_dq', 'integration_rejection_map_pixels_match_dq', 'integration_rejection_sample_counts_match_maps', 'local_normalization_contract']}
- PASS: contract_pipeline_contract_no_failed_checks - {'failed_checks': []}
- PASS: contract_stack_engine_default_promotion_present - {'required': True, 'present': True, 'path': 'runs\\checkpoints\\s2_gate_211_stack_engine_contract.json'}
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

## Resident Registration Fast Path

- Exists: True
- Available: True
- Mode: similarity_cuda_triangle
- Descriptor fit batch: True
- Descriptor fit batch mode: native_batch_shared_reference_device
- Descriptor device reuse: reference=True moving=True output=True
- Pixel refine batch: True
- Pixel refine metric mode: flattened_frame_candidate_grid
- Triangle warp batch: True
- Triangle warp batch mode: native_matrix_lanczos3_frames
- Warp copy mode: default_stream_async_device_to_device
- I/O pipeline warp copy mode: default_stream_async_device_to_device
- Warp scratch bytes: 493209636
- Component seconds: {'component_accounted_total': 3.9273199000216255, 'python_orchestration_or_uninstrumented': 0.0, 'triangle_descriptor_fit': 0.06670789999952831, 'triangle_descriptor_fit_batch': 0.06670789999952831, 'triangle_descriptor_fit_native_kernel_sync': 0.0373757, 'triangle_descriptor_fit_native_moving_upload': 0.0071799, 'triangle_descriptor_fit_native_output_download': 0.0141034, 'triangle_frame_total': 2.0032748999929026, 'triangle_moving_catalog': 0.1956029000102717, 'triangle_moving_catalog_batch': 0.19535399999949732, 'triangle_moving_catalog_native_count_download': 0.0069847, 'triangle_moving_catalog_native_enqueue': 0.0068736, 'triangle_moving_catalog_native_output_download': 0.0054274, 'triangle_moving_catalog_native_sync': 0.1689171, 'triangle_moving_catalog_native_total': 0.1882028, 'triangle_moving_descriptors': 0.15364480000607728, 'triangle_moving_descriptors_batch': 0.1527226000052906, 'triangle_pixel_refine': 1.0763637999989442, 'triangle_pixel_refine_batch': 1.0763637999989442, 'triangle_pixel_refine_native_coarse': 0.804891, 'triangle_pixel_refine_native_fine': 0.2660334, 'triangle_reference_catalog': 0.0015794000009918818, 'triangle_reference_descriptors': 0.001846899998781737, 'triangle_threshold_select': 7.660000665055122e-05, 'triangle_warp': 0.4726477000003797, 'triangle_warp_native_batch': 0.4556608, 'triangle_warp_native_sync': 0.4528609}

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
