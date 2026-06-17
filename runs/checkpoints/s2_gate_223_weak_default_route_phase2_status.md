# GLASS Phase 2 Status

- Status: attention_required
- Latest checkpoint: S2-Gate 222 (green)
- Checkpoint path: runs\checkpoints\s2_gate_222_status.md

## Acceptance

- Status: passed
- Speedup vs reference: 28.75107894736842
- Active frames: 193
- RMS diff: 0.001
- Coverage fraction: 0.97
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
- Registration fast path: present
- Registration fast path contract: not_requested checks=0 failed=0
- Registration fast path mode: similarity_cuda_triangle
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

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Windows Release

- Manifest status: release_manifest_ready
- Package count: 4
- Recommendation: ready_for_upload

## GitHub Release Plan

- Plan status: release_plan_ready
- Tag: None
- Publication ready: True
- GitHub auth OK: False
- Script path: None

## Pipeline Contract

- Status: passed
- Passed: True
- Check count: 15
- Failed checks: 0
- Integration outputs: 1
- Integration maps: 6
- Integration DQ contract: True
- Integration StackEngine result contract: True
- Integration resident result contract: True
- Pixel verification enabled: True
- DQ pixels match summary: True
- Coverage pixels match DQ: True
- Rejection pixels match DQ: True

## Release Decision

- Status: default_change_ready
- Recommendation: promote_default_candidate
- Release candidate ready: True
- Default change ready: True
- Speedup: 58.099101701945926
- Runtime repeat runs: 3
- Runtime repeat ratio vs best: 1.053510511049479
- Runtime repeat best: gate218_default_repeat02 22.598500299995067 s
- Pipeline handoff source: explicit_pipeline_contract
- Pipeline handoff pixel verification: True

## Checks

- PASS: latest_checkpoint_green - {'gate': 222, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 28.75107894736842}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: release_manifest_ready - {'status': 'release_manifest_ready', 'package_count': 4}
- PASS: github_release_plan_ready - {'status': 'release_plan_ready', 'publication_ready': True, 'gh_auth_ok': False}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_check_count': 0, 'integration_dq_contract': True, 'pixel_verification_enabled': True}
- PASS: release_decision_default_change_ready - {'status': 'default_change_ready', 'release_candidate_ready': True, 'default_change_ready': True, 'recommendation': 'promote_default_candidate', 'runtime_repeat_elapsed_ratio_vs_best': 1.053510511049479}
- FAIL: resident_registration_fastpath_contract_passed_for_default - {'status': 'not_requested', 'check_count': 0, 'failed_check_count': 0, 'fastpath_status': 'present', 'mode': 'similarity_cuda_triangle'}
