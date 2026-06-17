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

## Packages

| Package | Artifact | Compatible | Match | Role |
| --- | --- | --- | --- | --- |
| cuda11 | GLASS-Portable-win64-cuda11.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda12 | GLASS-Portable-win64-cuda12.zip | True | ptx_jit_forward | cuda_fallback_candidate |
| cuda13 | GLASS-Portable-win64-cuda13.zip | True | native_cubin | primary_cuda_package |
| cpu | GLASS-Portable-win64-cpu.zip | True | cpu_fallback | universal_cpu_fallback |

## Checks

- PASS: `doctor_schema_version` - {'actual': 1, 'required': 1, 'path': 'runs\\checkpoints\\s2_gate_219_doctor.json'}
- PASS: `cuda_probe_completed` - {'probe_skipped': False}
- PASS: `cuda_available_for_release_machine` - {'actual': True, 'required': True, 'wrapper_importable': True, 'native_extension_loaded': True}
- PASS: `windows_package_recommendation_present` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'package_count': 3}
- PASS: `ordered_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `primary_package_matches_expected` - {'actual': 'cuda13', 'required': 'cuda13'}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'required': True, 'status': 'default_change_ready', 'recommendation': 'promote_default_candidate'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `default_runtime_preset` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `runtime_repeat_ratio_within_release_bound` - {'actual': 1.053510511049479, 'required_max': 1.25}
- PASS: `acceptance_audit_passed` - {'status': 'passed', 'path': 'runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json'}
- PASS: `required_cuda_package_present:cuda13` - {'label': 'cuda13', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda13` - {'label': 'cuda13', 'compatible': True, 'match': 'native_cubin'}
- PASS: `required_cuda_package_present:cuda12` - {'label': 'cuda12', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda12` - {'label': 'cuda12', 'compatible': True, 'match': 'ptx_jit_forward'}
- PASS: `required_cuda_package_present:cuda11` - {'label': 'cuda11', 'available': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
- PASS: `required_cuda_package_compatible:cuda11` - {'label': 'cuda11', 'compatible': True, 'match': 'ptx_jit_forward'}
