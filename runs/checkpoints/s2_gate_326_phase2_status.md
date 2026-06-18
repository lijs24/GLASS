# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 326 (green)
- Checkpoint path: runs\checkpoints\s2_gate_326_phase2_checkpoint_fixture\s2_gate_326_status.md

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

- PASS: latest_checkpoint_green - {'gate': 326, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: release_decision_default_change_ready - {'status': 'default_change_ready', 'release_candidate_ready': True, 'default_change_ready': True, 'recommendation': 'promote_default_candidate', 'runtime_repeat_elapsed_ratio_vs_best': 1.0140280561122246}
- PASS: release_decision_warp_quality_handoff_ready - {'present': True, 'status': 'passed', 'ready': True, 'contract_passed': True, 'output_count': 1, 'failed_checks': [], 'failed_acceptance_checks': [], 'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json'}
- PASS: release_decision_runtime_repeat_evidence_ready - {'required': True, 'ready': True, 'status': 'passed', 'reason': 'stable repeat-runtime evidence supports the default change', 'present': True, 'run_count': 3, 'considered_run_count': 3, 'elapsed_ratio_vs_best': 1.0140280561122246, 'max_elapsed_ratio_vs_best': 1.25, 'recommendation': 'best_observed:repeat03'}
