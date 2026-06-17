# GLASS Acceptance Audit

- Status: passed
- Benchmark contract: s2_gate_222_default_route_contract
- Contract bundle: None
- Pipeline contract: None
- StackEngine contract: None
- DQ provenance records: 0
- Frame accounting artifact: runs\tmp_s2_gate_222_default_route_acceptance\glass_run\frame_accounting.json
- Speedup vs WBPP: 28.75107894736842
- Frame counts: {'light': 200, 'bias': 20, 'dark': 20, 'flat': 20}
- Shape match: True
- RMS diff: 0.001
- abs diff p99: 0.002
- Coverage fraction: 0.97

## Checks

## Pipeline Contract Evidence

- Status: not_requested
- Required by benchmark contract: False
- Pipeline contract path: None
- Pipeline contract audit type: None
- Pipeline contract passed: None
- Pipeline contract checks: 0
- Acceptance pipeline checks passed: 0
- Acceptance pipeline checks failed: 0
- Failed pipeline checks: []


## StackEngine Default Promotion Evidence

- Status: not_requested
- Required by benchmark contract: False
- StackEngine contract path: None
- StackEngine contract audit type: None
- StackEngine contract passed: None
- StackEngine contract scope: None
- Default promotion ready: None
- Default promotion status: None
- Default promotion gaps: None
- Default promotion blockers: None
- Adoption recommendation: None
- Acceptance StackEngine checks passed: 0
- Acceptance StackEngine checks failed: 0
- Failed StackEngine checks: []


- PASS: minimum_light_frames - {'actual': 200, 'required': 200}
- PASS: minimum_bias_frames - {'actual': 20, 'required': 20}
- PASS: minimum_dark_frames - {'actual': 20, 'required': 20}
- PASS: minimum_flat_frames - {'actual': 20, 'required': 20}
- PASS: minimum_active_frames - {'actual': 193, 'required': 190}
- PASS: minimum_speedup - {'actual': 28.75107894736842, 'required': 2.0}
- PASS: shape_match - {'actual': True, 'required': True}
- PASS: minimum_coverage_fraction - {'actual': 0.97, 'required': 0.95}
- PASS: maximum_rms_diff - {'actual': 0.001, 'required_max': 0.01}
- PASS: maximum_abs_diff_p99 - {'actual': 0.002, 'required_max': 0.01}
- PASS: contract_minimum_light_frames - {'actual': 200, 'required': 200}
- PASS: contract_minimum_bias_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_dark_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_flat_frames - {'actual': 20, 'required': 20}
- PASS: contract_minimum_active_light_frames - {'actual': 193, 'required': 190}
- PASS: contract_max_runtime_vs_release_baseline - {'actual_s': 38.0, 'release_baseline_s': 30.0, 'max_regression_factor': 1.3, 'required_max_s': 39.0}
- PASS: contract_minimum_speedup_vs_reference - {'actual': 28.75107894736842, 'required': 20.0}
- PASS: contract_required_command_token:--memory-mode resident - {'token': '--memory-mode resident', 'command_match': False, 'artifact_match': {'token': '--memory-mode resident', 'source': 'run_timing', 'field': 'memory_mode', 'actual': 'resident', 'requested': 'resident', 'reason': 'resident_cuda_default'}, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--backend cuda - {'token': '--backend cuda', 'command_match': False, 'artifact_match': {'token': '--backend cuda', 'source': 'run_timing', 'field': 'backend', 'actual': 'cuda', 'requested': 'auto', 'reason': 'resident_cuda_default'}, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--resident-registration similarity_cuda_triangle - {'token': '--resident-registration similarity_cuda_triangle', 'command_match': False, 'artifact_match': {'token': '--resident-registration similarity_cuda_triangle', 'source': 'resident_artifacts', 'field': 'resident_registration.mode', 'actual': 'similarity_cuda_triangle', 'artifact': 'runs\\tmp_s2_gate_222_default_route_acceptance\\glass_run\\resident_artifacts.json'}, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token:--flat-floor 0.05 - {'token': '--flat-floor 0.05', 'command_match': True, 'artifact_match': None, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_required_command_token_group:resident_h2d_or_runtime_preset - {'any_of': ['--resident-h2d-mode pinned_ring', '--resident-runtime-preset throughput-v1'], 'matched': [], 'artifact_matches': [{'token': '--resident-runtime-preset throughput-v1', 'source': 'run_timing', 'field': 'resident_runtime_preset', 'actual': 'throughput-v1', 'reason': 'resident_cuda_default'}], 'resident_io_pipeline_records': 0, 'run_command_present': True, 'run_timing_present': True}
- PASS: contract_compare_scale - {'actual': 8.764434957115609e-06, 'required': 8.764434957115609e-06, 'abs_tol': 1e-12, 'rel_tol': 1e-09}
- PASS: contract_compare_offset - {'actual': 0.0006274500691899127, 'required': 0.0006274500691899127, 'abs_tol': 1e-12, 'rel_tol': 1e-09}
- PASS: contract_compare_min_coverage - {'actual': 190.0, 'required': 190.0}
- PASS: contract_max_rms_diff - {'actual': 0.001, 'required_max': 0.01}
- PASS: contract_max_abs_diff_p99 - {'actual': 0.002, 'required_max': 0.01}
- PASS: contract_min_coverage_fraction - {'actual': 0.97, 'required': 0.95}

## Frame Accounting

- Exists: False
- Input lights: None
- Integrated frames: None
- Zero-weight frames: None
- Final status counts: None
- Exception summary: {}
- Integration weight counts: {'total': 200, 'positive': 193, 'zero': 7, 'invalid': 0}
- Registration counts: {'total': 0, 'accepted': 0, 'zero_weight_statuses': 0, 'status_counts': {}}

## Resident Registration Fast Path

- Exists: True
- Available: True
- Mode: similarity_cuda_triangle
- Descriptor fit batch: None
- Descriptor fit batch mode: None
- Descriptor device reuse: reference=None moving=None output=None
- Pixel refine batch: None
- Pixel refine metric mode: None
- Triangle warp batch: None
- Triangle warp batch mode: None
- Warp copy mode: None
- I/O pipeline warp copy mode: None
- Warp scratch bytes: None
- Component seconds: {}

## Performance Regression Diagnostics

- Status: regressed
- Worst stage: output_write actual=3.5s baseline=1.0s factor=3.5
- regressed: output_write actual=3.5s baseline=1.0s delta=2.5s factor=3.5
- ok: master_build_or_load actual=11.0s baseline=10.0s delta=1.0s factor=1.1
- ok: resident_registration_warp actual=12.0s baseline=11.0s delta=1.0s factor=1.0909090909090908
- ok: light_read_upload_calibrate actual=16.0s baseline=15.0s delta=1.0s factor=1.0666666666666667

## Optimization Guidance

- Primary target: io_upload_calibration_pipeline
- Exception context: {'count': 0, 'dominant_stage': None, 'primary_stage_counts': {}, 'final_status_counts': {}, 'sample_frame_ids': [], 'note': 'No rejected or zero-weight frame exceptions were recorded.'}
- #1 I/O + upload + calibration overlap stage=light_read_upload_calibrate current=16.0s baseline=15.0s factor=1.0666666666666667 action=Use deeper double/multi buffering, pinned host rings, async H2D, and larger batches so GPU calibration overlaps CPU FITS decode and disk reads.
- #2 Resident registration/warp batching stage=resident_registration_warp current=12.0s baseline=11.0s factor=1.0909090909090908 action=Keep star tables, descriptors, candidate scoring, pixel refinement, and warp scheduling resident on the GPU; reduce per-frame Python orchestration and host/device synchronization.
- #3 Resident master-frame cache stage=master_build_or_load current=11.0s baseline=10.0s factor=1.1 action=Reuse the shared resident master cache when calibration inputs and policies are unchanged.
- #4 Output-map write policy stage=output_write current=3.5s baseline=1.0s factor=3.5 action=Use science/minimal map policies for speed runs and keep full audit maps for validation runs.

## Clean-room

- Acceptance audit consumes GLASS artifacts and user-generated PixInsight/WBPP black-box timing/output metadata only.
