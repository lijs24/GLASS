# GLASS Phase 2 Status Compare

- Status: passed
- Baseline: runs\checkpoints\s2_gate_208_phase2_status.json
- Candidate: runs\checkpoints\s2_gate_209_phase2_status.json

## Summary

- Baseline: {'status': 'green', 'latest_gate': 208, 'acceptance_status': 'passed', 'cuda_available': True, 'release_manifest_status': 'release_manifest_ready', 'github_release_plan_status': 'release_plan_ready'}
- Candidate: {'status': 'green', 'latest_gate': 209, 'acceptance_status': 'passed', 'cuda_available': True, 'release_manifest_status': 'release_manifest_ready', 'github_release_plan_status': 'release_plan_ready'}

## Checks

- PASS: baseline_artifact_type - {'baseline': 'glass_phase2_status', 'candidate': 'glass_phase2_status'}
- PASS: candidate_artifact_type - {'baseline': 'glass_phase2_status', 'candidate': 'glass_phase2_status'}
- PASS: latest_checkpoint_gate_not_decreased - {'baseline': 208, 'candidate': 209}
- PASS: overall_status_green_preserved - {'baseline': 'green', 'candidate': 'green'}
- PASS: latest_checkpoint_green_preserved - {'baseline': True, 'candidate': True}
- PASS: acceptance_audit_passed_preserved - {'baseline': True, 'candidate': True}
- PASS: acceptance_status_preserved - {'baseline': 'passed', 'candidate': 'passed'}
- PASS: cuda_available_preserved - {'baseline': True, 'candidate': True}
- PASS: release_manifest_ready_preserved - {'baseline': 'release_manifest_ready', 'candidate': 'release_manifest_ready'}
- PASS: github_release_plan_ready_preserved - {'baseline': 'release_plan_ready', 'candidate': 'release_plan_ready'}
