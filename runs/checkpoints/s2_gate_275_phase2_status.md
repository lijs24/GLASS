# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 274 (green)
- Checkpoint path: runs\checkpoints\s2_gate_274_status.md

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

## Windows Publish Preflight

- Preflight status: publish_preflight_ready
- Passed: True
- Recommendation: publish_release_bundle
- Release tag: v0.1.0-gate274-preflight
- Assets/packages: 4/4
- Primary package: cuda13
- Try order: ['cuda13', 'cuda12', 'cuda11', 'cpu']
- Default promotion: default_promotion_ready
- Default route checks: 4
- Default route speedup vs reference: 58.099101701945926
- Rejection sample accounting statuses: phase2=passed, plan-matrix=passed, matrix=passed, default-promotion=passed
- Rejection sample accounting checks: phase2=True, plan-matrix=True, matrix=True, default-promotion=True, matrix-match=True
- Sample accounting closure statuses: phase2=passed, plan-matrix=passed, matrix=passed, default-promotion=passed
- Sample accounting closure checks: phase2=True, plan-matrix=True, matrix=True, default-promotion=True, matrix-match=True
- StackEngine default contract statuses: phase2=passed, plan-matrix=passed, matrix=passed, default-promotion=passed
- StackEngine default contract checks: phase2=True, plan-matrix=True, agreement=True, matrix=True, default-promotion=True, plan-matrix-match=True, default-promotion-match=True
- StackEngine default gaps: matrix=0, default-promotion=0
- Resident winsorized sweep statuses: matrix=passed, default-promotion=passed
- Resident winsorized sweep required frame: matrix=200/True, default-promotion=200/True
- Resident winsorized sweep checks: matrix-count=27, default-promotion-count=27, matrix-audit=True, matrix-frame=True, matrix-count-check=True, default-promotion-audit=True, default-promotion-frame=True, default-promotion-match=True

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

## Checks

- PASS: latest_checkpoint_green - {'gate': 274, 'status': 'green'}
- PASS: acceptance_audit_passed - {'status': 'passed', 'speedup_vs_reference': 58.099101701945926}
- PASS: default_route_acceptance_passed - {'status': 'passed', 'acceptance_passed': True, 'speedup_vs_reference': 28.75107894736842}
- PASS: default_route_acceptance_route_contract_passed - {'route_check_count': 4, 'route_failed_checks': []}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: release_manifest_ready - {'status': 'release_manifest_ready', 'package_count': 4}
- PASS: github_release_plan_ready - {'status': 'release_plan_ready', 'publication_ready': True, 'gh_auth_ok': False}
- PASS: windows_publish_preflight_ready - {'status': 'publish_preflight_ready', 'passed': True, 'asset_count': 4, 'package_count': 4, 'primary_package': 'cuda13', 'default_route_check_count': 4, 'failed_checks': []}
- PASS: windows_publish_preflight_rejection_sample_accounting_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_sample_accounting_closure_passed - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'phase2_check': True, 'plan_matrix_check': True, 'matrix_check': True, 'default_promotion_check': True, 'matrix_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_stack_engine_default_contract_ready - {'phase2_status': 'passed', 'plan_matrix_status': 'passed', 'matrix_status': 'passed', 'default_promotion_status': 'passed', 'matrix_default_gap_count': 0, 'default_promotion_default_gap_count': 0, 'phase2_check': True, 'plan_matrix_check': True, 'agreement_check': True, 'matrix_check': True, 'default_promotion_check': True, 'plan_matrix_match_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
- PASS: windows_publish_preflight_resident_winsorized_sweep_passed - {'matrix_status': 'passed', 'matrix_required_frame_count': 200, 'matrix_required_frame_count_passed': True, 'matrix_check_count': 27, 'default_promotion_status': 'passed', 'default_promotion_required_frame_count': 200, 'default_promotion_required_frame_count_passed': True, 'default_promotion_check_count': 27, 'matrix_audit_check': True, 'matrix_required_frame_check': True, 'matrix_check_count_check': True, 'default_promotion_audit_check': True, 'default_promotion_required_frame_check': True, 'default_promotion_match_check': True, 'failed_checks': []}
- PASS: resident_winsorized_sweep_audit_passed - {'status': 'passed', 'contract_name': 's2_gate_269_default_resident_winsorized_sweep', 'check_count': 27, 'failed_check_count': 0, 'failed_checks': [], 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3066304440398834e-05, 'required_frame_master_max_abs': 6.103515625e-05, 'max_hardened_master_rms': 2.3066304440398834e-05}
