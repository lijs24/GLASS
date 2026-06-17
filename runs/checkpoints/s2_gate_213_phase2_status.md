# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 213 (green)
- Checkpoint path: runs\checkpoints\s2_gate_213_status.md

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
- Publication ready: False
- GitHub auth OK: False
- Script path: None

## Checks

- PASS: latest_checkpoint_green - {'gate': 213, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 58.099101701945926}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: release_manifest_ready - {'status': 'release_manifest_ready', 'package_count': 4}
- PASS: github_release_plan_ready - {'status': 'release_plan_ready', 'publication_ready': False, 'gh_auth_ok': False}
