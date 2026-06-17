# GLASS Phase 2 Status Compare

- Status: passed
- Baseline: runs\checkpoints\s2_gate_217_phase2_status.json
- Candidate: runs\checkpoints\s2_gate_218_phase2_status.json

## Summary

- Baseline: {'status': 'green', 'latest_gate': 217, 'acceptance_status': 'passed', 'cuda_available': True, 'release_manifest_status': 'release_manifest_ready', 'github_release_plan_status': 'release_plan_ready', 'pipeline_contract_status': 'passed', 'pipeline_contract_passed': True}
- Candidate: {'status': 'green', 'latest_gate': 218, 'acceptance_status': 'passed', 'cuda_available': True, 'release_manifest_status': 'release_manifest_ready', 'github_release_plan_status': 'release_plan_ready', 'pipeline_contract_status': 'passed', 'pipeline_contract_passed': True}

## Checks

- PASS: baseline_artifact_type - {'baseline': 'glass_phase2_status', 'candidate': 'glass_phase2_status'}
- PASS: candidate_artifact_type - {'baseline': 'glass_phase2_status', 'candidate': 'glass_phase2_status'}
- PASS: latest_checkpoint_gate_not_decreased - {'baseline': 217, 'candidate': 218}
- PASS: overall_status_green_preserved - {'baseline': 'green', 'candidate': 'green'}
- PASS: latest_checkpoint_green_preserved - {'baseline': True, 'candidate': True}
- PASS: acceptance_audit_passed_preserved - {'baseline': True, 'candidate': True}
- PASS: acceptance_status_preserved - {'baseline': 'passed', 'candidate': 'passed'}
- PASS: cuda_available_preserved - {'baseline': True, 'candidate': True}
- PASS: release_manifest_ready_preserved - {'baseline': 'release_manifest_ready', 'candidate': 'release_manifest_ready'}
- PASS: github_release_plan_ready_preserved - {'baseline': 'release_plan_ready', 'candidate': 'release_plan_ready'}
- PASS: pipeline_contract_passed_preserved - {'baseline': True, 'candidate': True}
- PASS: pipeline_integration_dq_contract_preserved - {'baseline': True, 'candidate': True}
- PASS: pipeline_pixel_verification_preserved - {'baseline': True, 'candidate': True}
