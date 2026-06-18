# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 338 (green)
- Checkpoint path: runs\checkpoints\s2_gate_338_fixture\checkpoints\s2_gate_338_status.md

## CUDA

- CUDA available: False
- Native extension loaded: False
- Primary GPU: None
- Compute capability: None
- VRAM MiB: None
- Driver: None

## Pipeline Contract

- Status: passed
- Passed: True
- Check count: 1
- Failed checks: 0
- Integration outputs: 1
- Integration maps: 0
- Integration DQ contract: None
- Integration StackEngine result contract: None
- Integration resident result contract: True
- Integration resident result detail: passed check=True required=1 failed=0 failed_checks=[]
- Integration engine policy: not_available check=None nonresident=0 failed=0
- StackEngine runtime default: not_available check=None legacy=None failed_masters=0 failed_outputs=0 explicit_cuda=None
- Pixel verification enabled: None
- DQ pixels match summary: None
- Coverage pixels match DQ: None
- Rejection pixels match DQ: None
- Rejection sample counts match maps: None
- Rejection sample accounting: not_available failed=0
- Sample accounting closure: not_available present=0 failed=0

## Checks

- PASS: latest_checkpoint_green - {'gate': 338, 'status': 'green'}
- FAIL: cuda_doctor_available - {'cuda_available': False, 'primary_gpu': None}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_check_count': 0, 'integration_dq_contract': None, 'pixel_verification_enabled': None}
- PASS: pipeline_resident_result_contract_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'required_count': 1, 'failed_count': 0, 'failed_check_count': 0, 'failed_checks': [], 'failed_items': []}
- FAIL: pipeline_integration_engine_policy_passed - {'status': 'not_available', 'check_present': False, 'check_passed': None, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- FAIL: pipeline_stack_engine_runtime_default_passed - {'status': 'not_available', 'check_present': False, 'check_passed': None, 'legacy_master_count': None, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': None}
- PASS: pipeline_rejection_sample_accounting_passed - {'status': 'not_available', 'check_present': False, 'check_passed': None, 'pixel_verification_enabled': False, 'accounted_output_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_sample_accounting_closure_passed - {'status': 'not_available', 'check_present': False, 'check_passed': None, 'present_count': 0, 'required_count': 0, 'failed_count': 0, 'failed_items': []}
