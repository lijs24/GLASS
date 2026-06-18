# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 281 (green)
- Checkpoint path: synthetic://gate281/fixture/checkpoints\s2_gate_281_status.md

## Acceptance

- Status: passed
- Speedup vs reference: 58.0
- Active frames: 193
- RMS diff: 0.001
- Coverage fraction: 0.957
- Contract bundle schema: None
- Resident calibration contract: None
- Resident result contract: None
- Native guardrails bundle: None
- Native resident result source: None
- Native resident result run default: None
- Native resident result contract: None
- Native calibration artifact: None
- Native calibration masters: None
- Native calibrated lights: None
- Registration fast path: None
- Registration fast path contract: None checks=None failed=None
- Registration fast path mode: None
- Descriptor fit batch: None
- Descriptor fit batch mode: None
- Descriptor device reuse: None
- Pixel refine batch: None
- Pixel refine metric mode: None
- Triangle warp batch: None
- Triangle warp batch mode: None
- Triangle warp batch frames: None
- Resident warp copy mode: None
- Resident warp scratch bytes: None
- Pipeline integration engine policy: passed check=True nonresident=0 failed=0

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: synthetic CUDA device
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Pipeline Contract

- Status: passed
- Passed: True
- Check count: 1
- Failed checks: 0
- Integration outputs: 0
- Integration maps: 0
- Integration DQ contract: None
- Integration StackEngine result contract: None
- Integration resident result contract: None
- Integration engine policy: passed check=True nonresident=0 failed=0
- Pixel verification enabled: False
- DQ pixels match summary: None
- Coverage pixels match DQ: None
- Rejection pixels match DQ: None
- Rejection sample counts match maps: None
- Rejection sample accounting: not_available failed=0
- Sample accounting closure: not_available present=0 failed=0

## Checks

- PASS: latest_checkpoint_green - {'gate': 281, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 58.0}
- PASS: acceptance_pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'synthetic CUDA device'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_check_count': 0, 'integration_dq_contract': None, 'pixel_verification_enabled': False}
- PASS: pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_rejection_sample_accounting_passed - {'status': 'not_available', 'check_present': False, 'check_passed': None, 'pixel_verification_enabled': False, 'accounted_output_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_sample_accounting_closure_passed - {'status': 'not_available', 'check_present': False, 'check_passed': None, 'present_count': 0, 'required_count': 0, 'failed_count': 0, 'failed_items': []}
