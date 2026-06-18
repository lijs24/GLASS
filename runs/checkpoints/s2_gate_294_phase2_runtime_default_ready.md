# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 294 (green)
- Checkpoint path: runs\checkpoints\s2_gate_294_fixtures\phase2\checkpoints\s2_gate_294_status.md

## Acceptance

- Status: passed
- Speedup vs reference: 58.0
- Active frames: 193
- RMS diff: 0.001
- Coverage fraction: 0.957
- Contract bundle schema: passed
- Resident calibration contract: True
- Resident result contract: True
- Native guardrails bundle: present
- Native resident result source: run_default
- Native resident result run default: True
- Native resident result contract: C:/glass_runs/run/resident_result_contract.json
- Native calibration artifact: True
- Native calibration masters: 3
- Native calibrated lights: 200
- Registration fast path: present
- Registration fast path contract: passed checks=2 failed=0
- Registration fast path mode: similarity_cuda_triangle
- Descriptor fit batch: True
- Descriptor fit batch mode: native_batch_shared_reference_device
- Descriptor device reuse: {'reference': True, 'moving': True, 'output': True}
- Pixel refine batch: True
- Pixel refine metric mode: flattened_frame_candidate_grid
- Triangle warp batch: True
- Triangle warp batch mode: native_matrix_lanczos3_frames
- Triangle warp batch frames: 188
- Resident warp copy mode: default_stream_async_device_to_device
- Resident warp scratch bytes: 493209636
- Pipeline integration engine policy: passed check=True nonresident=0 failed=0
- Pipeline StackEngine runtime default: passed check=True masters=1 legacy=0 failed_masters=0 failed_outputs=0 explicit_cuda=0

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: Fixture GPU
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Pipeline Contract

- Status: passed
- Passed: True
- Check count: 11
- Failed checks: 0
- Integration outputs: 1
- Integration maps: 3
- Integration DQ contract: True
- Integration StackEngine result contract: True
- Integration resident result contract: True
- Integration engine policy: passed check=True nonresident=0 failed=0
- StackEngine runtime default: passed check=True legacy=0 failed_masters=0 failed_outputs=0 explicit_cuda=0
- Pixel verification enabled: True
- DQ pixels match summary: True
- Coverage pixels match DQ: True
- Rejection pixels match DQ: True
- Rejection sample counts match maps: True
- Rejection sample accounting: passed failed=0
- Sample accounting closure: passed present=1 failed=0

## Checks

- PASS: latest_checkpoint_green - {'gate': 294, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 58.0}
- PASS: acceptance_pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0}
- PASS: acceptance_pipeline_stack_engine_runtime_default_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 1, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'Fixture GPU'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_check_count': 0, 'integration_dq_contract': True, 'pixel_verification_enabled': True}
- PASS: pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_stack_engine_runtime_default_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0}
- PASS: pipeline_rejection_sample_accounting_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'pixel_verification_enabled': True, 'accounted_output_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_sample_accounting_closure_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'present_count': 1, 'required_count': 1, 'failed_count': 0, 'failed_items': []}
