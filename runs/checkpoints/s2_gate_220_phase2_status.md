# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 220 (green)
- Checkpoint path: runs\checkpoints\s2_gate_220_status.md

## Acceptance

- Status: passed
- Speedup vs reference: 58.099101701945926
- Active frames: 193
- RMS diff: 0.0014945534429799121
- Coverage fraction: 0.9577924192878646
- Contract bundle schema: passed
- Resident calibration contract: None
- Resident result contract: True
- Native guardrails bundle: present
- Native resident result source: run_default
- Native resident result run default: True
- Native resident result contract: C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view\resident_result_contract.json
- Native calibration artifact: True
- Native calibration masters: 3
- Native calibrated lights: 200
- Registration fast path: present
- Registration fast path contract: passed checks=24 failed=0
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

- PASS: latest_checkpoint_green - {'gate': 220, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 58.099101701945926}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: release_manifest_ready - {'status': 'release_manifest_ready', 'package_count': 4}
- PASS: github_release_plan_ready - {'status': 'release_plan_ready', 'publication_ready': True, 'gh_auth_ok': False}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_check_count': 0, 'integration_dq_contract': True, 'pixel_verification_enabled': True}
- PASS: release_decision_default_change_ready - {'status': 'default_change_ready', 'release_candidate_ready': True, 'default_change_ready': True, 'recommendation': 'promote_default_candidate', 'runtime_repeat_elapsed_ratio_vs_best': 1.053510511049479}
