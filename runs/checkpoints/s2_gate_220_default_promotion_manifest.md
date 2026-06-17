# GLASS Default Promotion Manifest

- Status: `default_promotion_ready`
- Recommendation: `promote_resident_cuda_default`
- Passed: `True`
- Default memory mode candidate: `resident`
- Fallback memory mode: `tile`
- Runtime preset: `throughput-v1`
- Integration engine: `cuda_resident_stack`

## Runtime Evidence

- Runs: `3`
- Best: `gate218_default_repeat02` `22.598500299995067` s
- Slowest: `23.807757599999604` s
- Slowest/best ratio: `1.053510511049479`

## Release Machine

- Doctor present: `True`
- CUDA available: `True`
- Native extension loaded: `True`
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`

## Checks

- PASS: `release_decision_artifact_type` - {'actual': 'release_promotion_decision', 'required': 'release_promotion_decision'}
- PASS: `phase2_status_artifact_type` - {'actual': 'glass_phase2_status', 'required': 'glass_phase2_status'}
- PASS: `phase2_status_green` - {'status': 'green', 'passed': True}
- PASS: `latest_checkpoint_green` - {'gate': 219, 'status': 'green', 'green': True}
- PASS: `release_decision_default_change_ready` - {'actual': True, 'status': 'default_change_ready'}
- PASS: `release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `phase2_embeds_same_release_decision` - {'input': 'runs\\checkpoints\\s2_gate_218_release_promotion_decision.json', 'phase2_release_decision_path': 'runs\\checkpoints\\s2_gate_218_release_promotion_decision.json'}
- PASS: `phase2_release_decision_default_change_ready` - {'actual': True}
- PASS: `phase2_release_decision_recommends_promotion` - {'actual': 'promote_default_candidate', 'required': 'promote_default_candidate'}
- PASS: `runtime_repeat_present` - {'present': True, 'recommendation': 'best_observed:gate218_default_repeat02'}
- PASS: `runtime_repeat_count` - {'actual': 3, 'required_min': 3}
- PASS: `runtime_repeat_ratio_within_bound` - {'actual': 1.053510511049479, 'required_max': 1.25}
- PASS: `pipeline_contract_passed` - {'status': 'passed', 'passed': True}
- PASS: `pipeline_dq_contract_passed` - {'actual': True}
- PASS: `pipeline_stack_and_resident_result_contracts_passed` - {'stack': True, 'resident': True}
- PASS: `pipeline_pixel_verification_enabled` - {'enabled': True, 'tile_size': 2048}
- PASS: `pipeline_pixel_maps_match_dq` - {'dq': True, 'coverage': True, 'rejection': True}
- PASS: `resident_calibration_artifact_present` - {'actual': True}
- PASS: `resident_light_count` - {'actual': 200, 'required_min': 200}
- PASS: `default_memory_mode_candidate` - {'actual': 'resident', 'required': 'resident'}
- PASS: `fallback_memory_mode_preserved` - {'actual': 'tile', 'required': 'tile'}
- PASS: `default_runtime_preset_candidate` - {'actual': 'throughput-v1', 'required': 'throughput-v1'}
- PASS: `integration_engine_candidate` - {'actual': 'cuda_resident_stack', 'required': 'cuda_resident_stack'}
- PASS: `doctor_artifact_available` - {'present': True, 'required': True}
- PASS: `doctor_cuda_available` - {'cuda_available': True, 'native_extension_loaded': True, 'wrapper_importable': True}
- PASS: `doctor_native_extension_loaded` - {'actual': True}
- PASS: `windows_package_try_list_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `windows_package_primary_present` - {'primary': 'cuda13'}
