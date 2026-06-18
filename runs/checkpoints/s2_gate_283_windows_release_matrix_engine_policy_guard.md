# GLASS Windows Release Matrix

- Status: `release_matrix_ready`
- Recommendation: `publish_windows_cuda_matrix`
- Passed: `True`
- Default resident runtime preset: `throughput-v1`

## Current Machine

- CUDA available: `True`
- Native extension loaded: `True`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`
- Guidance: Try cuda13 first for native performance; if it fails to load, try cuda12, cuda11, cpu. Newer GPUs may run older CUDA packages through PTX JIT.

## Default Promotion Manifest

- Present: `True`
- Status: `default_promotion_ready`
- Passed: `True`
- Default route passed: `True`
- Default route contract/checks: `True`/`4`
- Rejection sample accounting: `passed` failed=`0`
- Sample accounting closure: `passed` present=`1` failed=`0`
- Integration engine policy: ready=`True` acceptance=`passed` pipeline=`passed`
- StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`
- Resident winsorized sweep: passed=`True` phase2-check=`True` required-frame=`200` required-pass=`True` checks=`27`

## Packages

| Package | Artifact | Compatible | Match | Role |
| --- | --- | --- | --- | --- |
| cuda11 | GLASS-Portable-win64-cuda11.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda12 | GLASS-Portable-win64-cuda12.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda13 | GLASS-Portable-win64-cuda13.zip | True | native_cubin | primary_cuda_package |
| cpu | GLASS-Portable-win64-cpu.zip | True | cpu_fallback | universal_cpu_fallback |

## Checks

- PASS: `doctor_schema_version` - {'actual': 1, 'required': 1, 'path': 'synthetic://gate283/fixture/doctor.json'}
- PASS: `cuda_probe_completed` - {'probe_skipped': False}
- PASS: `cuda_available_for_release_machine` - {'actual': True, 'required': True, 'wrapper_importable': True, 'native_extension_loaded': True}
- PASS: `windows_package_recommendation_present` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'package_count': 3}
- PASS: `ordered_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `primary_package_matches_expected` - {'actual': 'cuda13', 'required': 'cuda13'}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'required': True, 'status': 'default_change_ready', 'recommendation': 'promote_default_candidate'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `default_promotion_manifest_present` - {'present': True, 'required': True}
- PASS: `default_promotion_manifest_ready` - {'artifact_type': 'default_promotion_manifest', 'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True}
- PASS: `default_promotion_default_route_passed` - {'default_route_passed': True, 'route_contract_passed': True, 'route_check_count': 4}
- PASS: `default_promotion_rejection_sample_accounting_passed` - {'pipeline_contract_status': 'passed', 'pipeline_contract_passed': True, 'check': True, 'status': 'passed', 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_sample_accounting_closure_passed` - {'pipeline_contract_status': 'passed', 'pipeline_contract_passed': True, 'check': True, 'status': 'passed', 'present_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_acceptance_integration_engine_policy_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_pipeline_integration_engine_policy_passed` - {'status': 'passed', 'check_present': True, 'check_passed': True, 'phase2_check_passed': True, 'default_engine_policy': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `default_promotion_stack_engine_contract_ready` - {'present': True, 'ready': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'adoption_recommendation': 'stack_engine_default_ready', 'default_gap_count': 0, 'blocker_count': 0, 'blockers': []}
- PASS: `default_promotion_resident_winsorized_sweep_audit_passed` - {'present': True, 'status': 'passed', 'passed': True, 'phase2_check_passed': True, 'failed_checks': []}
- PASS: `default_promotion_resident_winsorized_required_frame_passed` - {'actual_frame_count': 200, 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3e-05, 'required_frame_master_max_abs': 6.1e-05}
- PASS: `default_promotion_resident_winsorized_sweep_check_count` - {'actual': 27, 'required_min': 27, 'failed_check_count': 0}
- PASS: `default_runtime_preset` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `runtime_repeat_ratio_within_release_bound` - {'actual': 1.0140343433372492, 'required_max': 1.25}
- PASS: `acceptance_audit_passed` - {'status': 'passed', 'path': 'synthetic://gate283/fixture/acceptance.json'}
- PASS: `required_cuda_package_present:cuda13` - {'label': 'cuda13', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda13` - {'label': 'cuda13', 'compatible': True, 'match': 'native_cubin'}
- PASS: `required_cuda_package_present:cuda12` - {'label': 'cuda12', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda12` - {'label': 'cuda12', 'compatible': True, 'match': 'ptx_jit_forward'}
- PASS: `required_cuda_package_present:cuda11` - {'label': 'cuda11', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda11` - {'label': 'cuda11', 'compatible': True, 'match': 'ptx_jit_forward'}
