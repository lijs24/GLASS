# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 304 (Green)
- Checkpoint path: runs\checkpoints\s2_gate_304_status.md

## Acceptance

- Status: passed
- Speedup vs reference: 58.099101701945926
- Active frames: 193
- RMS diff: 0.0014945534429799121
- Coverage fraction: 0.9577924192878646
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
- Pipeline integration engine policy: passed check=True nonresident=0 failed=0
- Pipeline StackEngine runtime default: passed check=True masters=3 legacy=0 failed_masters=0 failed_outputs=0 explicit_cuda=0

## Default Route Acceptance

- Status: passed
- Passed: True
- Route contract passed: True
- Contract: s2_gate_222_default_route_contract
- Speedup vs reference: 28.75107894736842
- Active frames: 193
- Route check count: 4
- Route failed checks: []

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## StackEngine Publication Audit

- Status: passed
- Passed: True
- Recommendation: publication_chain_ready
- Layers/checks: 15/28
- Failed checks: []
- Publish-preflight policy layer: {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Phase2 policy layer: {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Policy checks: raw=True, phase2=True, agreement=True
- Resident winsorized layers: raw={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, phase2={'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}
- Resident winsorized checks: raw=True, phase2=True, agreement=True

## Pipeline Contract

- Status: passed
- Passed: True
- Check count: 19
- Failed checks: 0
- Integration outputs: 1
- Integration maps: 6
- Integration DQ contract: True
- Integration StackEngine result contract: True
- Integration resident result contract: True
- Integration engine policy: passed check=True nonresident=0 failed=0
- StackEngine runtime default: passed check=True legacy=0 failed_masters=0 failed_outputs=0 explicit_cuda=0
- Pixel verification enabled: True
- DQ pixels match summary: True
- Coverage pixels match DQ: True
- Rejection pixels match DQ: True
- Rejection sample counts match maps: True
- Rejection sample accounting: passed failed=0
- Sample accounting closure: passed present=0 failed=0

## StackEngine Default Contract

- Status: passed
- Passed: True
- Scope: all
- Expected integration engine: cuda_resident_stack
- Adoption recommendation: stack_engine_default_ready
- Adoption surfaces: 4 ready=4
- StackEngine/resident surfaces: 0/4
- Phase 2 default gaps: 0
- Default promotion: ready ready=True blockers=0

## Resident Winsorized Sweep Audit

- Status: passed
- Passed: True
- Contract: s2_gate_269_default_resident_winsorized_sweep
- Sweep: runs\checkpoints\s2_gate_268_resident_winsorized_sweep.json
- Check count: 27
- Failed checks: []
- Frame counts: [8, 32, 128, 200]
- Run count: 4
- Required frame count: 200
- Required frame count passed: True
- Required frame master RMS: 2.3066304440398834e-05
- Required frame master max abs: 6.103515625e-05
- Max hardened master RMS: 2.3066304440398834e-05
- Required frame hardened CUDA seconds: 0.0012743999977828935

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

- PASS: latest_checkpoint_green - {'gate': 304, 'status': 'Green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 58.099101701945926}
- PASS: acceptance_pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0}
- PASS: acceptance_pipeline_stack_engine_runtime_default_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0}
- PASS: default_route_acceptance_passed - {'status': 'passed', 'acceptance_passed': True, 'speedup_vs_reference': 28.75107894736842}
- PASS: default_route_acceptance_route_contract_passed - {'route_check_count': 4, 'route_failed_checks': []}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: stack_engine_publication_audit_passed - {'status': 'passed', 'passed': True, 'recommendation': 'publication_chain_ready', 'check_count': 28, 'failed_check_count': 0, 'failed_checks': []}
- PASS: stack_engine_publication_audit_policy_chain_passed - {'raw_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: stack_engine_publication_audit_resident_winsorized_chain_passed - {'raw_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'phase2_layer': {'status': 'publish_preflight_ready', 'ready': True, 'gap_count': None}, 'raw_ready_check': True, 'phase2_ready_check': True, 'agreement_check': True, 'failed_checks': []}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_check_count': 0, 'integration_dq_contract': True, 'pixel_verification_enabled': True}
- PASS: pipeline_integration_engine_policy_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_stack_engine_runtime_default_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'legacy_master_count': 0, 'failed_master_count': 0, 'failed_output_count': 0, 'explicit_cuda_fast_path_count': 0}
- PASS: pipeline_rejection_sample_accounting_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'pixel_verification_enabled': True, 'accounted_output_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_sample_accounting_closure_passed - {'status': 'passed', 'check_present': True, 'check_passed': True, 'present_count': 0, 'required_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: stack_engine_default_contract_ready - {'status': 'passed', 'passed': True, 'scope': 'all', 'expected_integration_engine': 'cuda_resident_stack', 'adoption_recommendation': 'stack_engine_default_ready', 'adoption_gap_count': 0, 'default_promotion_ready': True, 'default_promotion_status': 'ready', 'default_promotion_blocker_count': 0, 'failed_checks': [], 'blockers': []}
- PASS: resident_winsorized_sweep_audit_passed - {'status': 'passed', 'contract_name': 's2_gate_269_default_resident_winsorized_sweep', 'check_count': 27, 'failed_check_count': 0, 'failed_checks': [], 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3066304440398834e-05, 'required_frame_master_max_abs': 6.103515625e-05, 'max_hardened_master_rms': 2.3066304440398834e-05}
- PASS: release_decision_default_change_ready - {'status': 'default_change_ready', 'release_candidate_ready': True, 'default_change_ready': True, 'recommendation': 'promote_default_candidate', 'runtime_repeat_elapsed_ratio_vs_best': 1.053510511049479}
- PASS: resident_registration_fastpath_contract_passed_for_default - {'status': 'passed', 'check_count': 24, 'failed_check_count': 0, 'fastpath_status': 'present', 'mode': 'similarity_cuda_triangle'}
