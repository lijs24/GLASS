# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 328 (green)
- Checkpoint path: runs\checkpoints\s2_gate_328_phase2_checkpoint_fixture\s2_gate_328_status.md

## Acceptance

- Status: passed
- Speedup vs reference: 10.0
- Active frames: 193
- RMS diff: 0.001
- Coverage fraction: 0.97
- Contract bundle schema: passed
- Resident calibration contract: None
- Resident result contract: None
- Native guardrails bundle: present
- Native resident result source: missing
- Native resident result run default: False
- Native resident result contract: None
- Native calibration artifact: False
- Native calibration masters: 3
- Native calibrated lights: 0
- Warp quality contract: passed passed=True outputs=1 failed=[]
- Registration fast path: present
- Registration fast path contract: passed checks=23 failed=0
- Registration fast path mode: similarity_cuda_triangle
- Descriptor fit batch: True
- Descriptor fit batch mode: native_batch_shared_reference_device
- Descriptor device reuse: {'reference': True, 'moving': True, 'output': True}
- Pixel refine batch: True
- Pixel refine metric mode: flattened_frame_candidate_grid
- Triangle warp batch: True
- Triangle warp batch mode: native_matrix_lanczos3_frames
- Triangle warp batch frames: 3
- Resident warp copy mode: default_stream_async_device_to_device
- Resident warp scratch bytes: 4096
- Pipeline integration engine policy: passed check=True nonresident=1 failed=0
- Pipeline StackEngine runtime default: passed check=True masters=3 legacy=0 failed_masters=0 failed_outputs=0 explicit_cuda=0

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Release Decision

- Status: default_change_ready
- Recommendation: promote_default_candidate
- Release candidate ready: True
- Default change ready: True
- Speedup: 10.0
- Runtime repeat runs: 3
- Runtime repeat ratio vs best: 1.0140280561122246
- Runtime repeat closure: passed required=True ready=True runs=3 considered=3
- Runtime repeat best: repeat03 99.8 s
- Pipeline handoff source: acceptance_pipeline_contract
- Pipeline handoff pixel verification: True
- Warp quality handoff: passed ready=True outputs=1 failed=[]

## Checks

- PASS: latest_checkpoint_green - {'gate': 328, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 10.0}
- PASS: acceptance_pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 1, 'failed_count': 0}
- PASS: acceptance_pipeline_stack_engine_runtime_default_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0}
- PASS: acceptance_warp_quality_contract_passed - {'status': 'passed', 'passed': True, 'output_count': 1, 'failed_checks': [], 'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: release_decision_default_change_ready - {'status': 'default_change_ready', 'release_candidate_ready': True, 'default_change_ready': True, 'recommendation': 'promote_default_candidate', 'runtime_repeat_elapsed_ratio_vs_best': 1.0140280561122246}
- PASS: release_decision_warp_quality_handoff_ready - {'present': True, 'status': 'passed', 'ready': True, 'contract_passed': True, 'output_count': 1, 'failed_checks': [], 'failed_acceptance_checks': [], 'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json'}
- PASS: release_decision_runtime_repeat_evidence_ready - {'required': True, 'ready': True, 'status': 'passed', 'reason': 'stable repeat-runtime evidence supports the default change', 'present': True, 'run_count': 3, 'considered_run_count': 3, 'elapsed_ratio_vs_best': 1.0140280561122246, 'max_elapsed_ratio_vs_best': 1.25, 'recommendation': 'best_observed:repeat03'}
- PASS: resident_registration_fastpath_contract_passed_for_default - {'status': 'passed', 'check_count': 23, 'failed_check_count': 0, 'fastpath_status': 'present', 'mode': 'similarity_cuda_triangle'}
