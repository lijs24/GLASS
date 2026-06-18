# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 325 (green)
- Checkpoint path: runs\checkpoints\s2_gate_325_phase2_checkpoint_fixture\s2_gate_325_status.md

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
- Registration fast path: missing
- Registration fast path contract: not_requested checks=0 failed=0
- Registration fast path mode: None
- Descriptor fit batch: None
- Descriptor fit batch mode: None
- Descriptor device reuse: {'reference': None, 'moving': None, 'output': None}
- Pixel refine batch: None
- Pixel refine metric mode: None
- Triangle warp batch: None
- Triangle warp batch mode: None
- Triangle warp batch frames: None
- Resident warp copy mode: None
- Resident warp scratch bytes: None
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

- Status: release_candidate_ready
- Recommendation: repeat_benchmark_before_default_change
- Release candidate ready: True
- Default change ready: False
- Speedup: 10.0
- Runtime repeat runs: None
- Runtime repeat ratio vs best: None
- Runtime repeat best: None None s
- Pipeline handoff source: acceptance_pipeline_contract
- Pipeline handoff pixel verification: True
- Warp quality handoff: passed ready=True outputs=1 failed=[]

## Checks

- PASS: latest_checkpoint_green - {'gate': 325, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 10.0}
- PASS: acceptance_pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 1, 'failed_count': 0}
- PASS: acceptance_pipeline_stack_engine_runtime_default_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0}
- PASS: acceptance_warp_quality_contract_passed - {'status': 'passed', 'passed': True, 'output_count': 1, 'failed_checks': [], 'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- FAIL: release_decision_default_change_ready - {'status': 'release_candidate_ready', 'release_candidate_ready': True, 'default_change_ready': False, 'recommendation': 'repeat_benchmark_before_default_change', 'runtime_repeat_elapsed_ratio_vs_best': None}
- PASS: release_decision_warp_quality_handoff_ready - {'present': True, 'status': 'passed', 'ready': True, 'contract_passed': True, 'output_count': 1, 'failed_checks': [], 'failed_acceptance_checks': [], 'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json'}
