# GLASS Windows Publish Preflight

- Status: `publish_preflight_ready`
- Passed: `True`
- Recommendation: `publish_release_bundle`
- Release tag: `v0.1.0-phase2-gate228`
- Assets/packages: `4`/`4`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`
- Source stamps: `aa63510`
- Default promotion: `default_promotion_ready`
- Default route checks/speedup: `4`/`28.75107894736842`

## Inputs

- release_manifest: `runs\checkpoints\s2_gate_228_windows_release_manifest.json`
- github_release_plan: `runs\checkpoints\s2_gate_228_github_release_plan.json`
- windows_release_matrix: `runs\checkpoints\s2_gate_226_windows_release_matrix.json`
- default_promotion_manifest: `runs\checkpoints\s2_gate_226_default_promotion_manifest.json`

## Checks

- PASS: `release_manifest_ready` - {'artifact_type': 'windows_release_manifest', 'status': 'release_manifest_ready', 'passed': True}
- PASS: `github_release_plan_ready` - {'artifact_type': 'windows_github_release_plan', 'status': 'release_plan_ready', 'passed': True}
- PASS: `github_release_plan_publication_ready` - {'publication_ready': True, 'required': True}
- PASS: `windows_release_matrix_ready` - {'artifact_type': 'windows_release_matrix', 'status': 'release_matrix_ready', 'passed': True, 'primary_package': 'cuda13', 'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'package_labels': ['cuda11', 'cuda12', 'cuda13', 'cpu'], 'default_promotion_status': 'default_promotion_ready', 'default_promotion_passed': True, 'default_promotion_default_change_ready': True, 'default_route_passed': True, 'default_route_route_contract_passed': True, 'default_route_route_check_count': 4, 'default_route_speedup_vs_reference': 28.75107894736842}
- PASS: `default_promotion_ready` - {'artifact_type': 'default_promotion_manifest', 'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True, 'recommendation': 'promote_resident_cuda_default', 'default_route_status': 'passed', 'default_route_passed': True, 'default_route_route_contract_passed': True, 'default_route_route_check_count': 4, 'default_route_speedup_vs_reference': 28.75107894736842}
- PASS: `default_route_contract_passed` - {'default_route_passed': True, 'route_contract_passed': True, 'route_check_count': 4}
- PASS: `manifest_references_matrix` - {'manifest_matrix_path': 'runs\\checkpoints\\s2_gate_226_windows_release_matrix.json', 'matrix_path': 'runs\\checkpoints\\s2_gate_226_windows_release_matrix.json'}
- PASS: `github_plan_references_manifest` - {'plan_manifest_artifact': 'runs\\checkpoints\\s2_gate_228_windows_release_manifest.json', 'manifest_path': 'runs\\checkpoints\\s2_gate_228_windows_release_manifest.json'}
- PASS: `github_plan_references_matrix` - {'plan_matrix_path': 'runs\\checkpoints\\s2_gate_226_windows_release_matrix.json', 'matrix_path': 'runs\\checkpoints\\s2_gate_226_windows_release_matrix.json'}
- PASS: `matrix_default_promotion_matches_manifest` - {'matrix': {'artifact_type': 'windows_release_matrix', 'status': 'release_matrix_ready', 'passed': True, 'primary_package': 'cuda13', 'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'package_labels': ['cuda11', 'cuda12', 'cuda13', 'cpu'], 'default_promotion_status': 'default_promotion_ready', 'default_promotion_passed': True, 'default_promotion_default_change_ready': True, 'default_route_passed': True, 'default_route_route_contract_passed': True, 'default_route_route_check_count': 4, 'default_route_speedup_vs_reference': 28.75107894736842}, 'default_promotion': {'artifact_type': 'default_promotion_manifest', 'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True, 'recommendation': 'promote_resident_cuda_default', 'default_route_status': 'passed', 'default_route_passed': True, 'default_route_route_contract_passed': True, 'default_route_route_check_count': 4, 'default_route_speedup_vs_reference': 28.75107894736842}}
- PASS: `matrix_default_route_matches_manifest` - {'matrix': {'artifact_type': 'windows_release_matrix', 'status': 'release_matrix_ready', 'passed': True, 'primary_package': 'cuda13', 'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'package_labels': ['cuda11', 'cuda12', 'cuda13', 'cpu'], 'default_promotion_status': 'default_promotion_ready', 'default_promotion_passed': True, 'default_promotion_default_change_ready': True, 'default_route_passed': True, 'default_route_route_contract_passed': True, 'default_route_route_check_count': 4, 'default_route_speedup_vs_reference': 28.75107894736842}, 'default_promotion': {'artifact_type': 'default_promotion_manifest', 'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True, 'recommendation': 'promote_resident_cuda_default', 'default_route_status': 'passed', 'default_route_passed': True, 'default_route_route_contract_passed': True, 'default_route_route_check_count': 4, 'default_route_speedup_vs_reference': 28.75107894736842}}
- PASS: `manifest_assets_match_github_plan` - {'manifest_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'asset_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'missing_assets': [], 'mismatched_assets': []}
- PASS: `matrix_packages_match_manifest` - {'matrix_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'manifest_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'missing_manifest_rows': []}
- PASS: `cpu_fallback_preserved` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu'], 'manifest_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'asset_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13']}
