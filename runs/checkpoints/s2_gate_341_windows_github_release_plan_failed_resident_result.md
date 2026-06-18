# GLASS Windows GitHub Release Plan

- Status: `blocked`
- Passed: `False`
- Publication ready: `False`
- Recommendation: `fix_release_plan_blockers`
- Tag: `s2-gate-341-failed`
- Title: `GLASS S2 Gate 341 Failed Fixture`
- Source stamps: `s2-gate-341`
- GitHub CLI available: `False`
- GitHub CLI auth OK: `False`
- Publish script: `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_publish_release_failed_resident_result.ps1`
- Publish script mode: `dry_run_requires_publish_switch`
- Windows release matrix: `blocked`

## Assets

| Label | Size bytes | SHA256 | Path |
| --- | ---: | --- | --- |
| cuda13 | 20 | `81ef7633b1c7d700aff468c131055ee625b5f2efcc31b67ebaa1a1b35efb3d98` | `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cuda13.zip` |
| cuda12 | 20 | `a661671be01d3028d5580c506adf858600c1252c621cdc8d6dfc4a462e3b7fd6` | `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cuda12.zip` |
| cuda11 | 20 | `ca9d8a29bf75e27ef6e0d7eab2d6ee23496e78314be793293f219f2aa9918256` | `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cuda11.zip` |
| cpu | 17 | `843662196aad1d87a22bfff89308b04f5b579a43a9c945d823ae7a91a634a48e` | `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cpu.zip` |

## Windows Release Matrix Handoff

- Matrix path: `runs\checkpoints\s2_gate_340_windows_release_matrix_failed_resident_result.json`
- Matrix status: `blocked`
- Matrix passed: `False`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`
- Default promotion: `blocked` passed `False`
- Default route contract/checks: `True`/`4`
- Release direct publication guard: ready=`True` check=`True` source=`explicit_resident_artifacts_json`/`resident_artifacts_json_fallback` lights=`200`
- Default-promotion release direct guard: ready=`True` check=`True` lights=`200`
- StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`
- Resident fastpath release handoff: ready=`True` raw=`passed` phase2=`passed` agreement=`True` checks=`23`
- Resident result contract: ready=`False` status=`failed` phase2=`False` required=`1` failed=`1`
- Rejection sample accounting: `passed` failed `0`
- Sample accounting closure: `passed` present=`1` failed=`0`

## Command

```powershell
gh release create s2-gate-341-failed 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cuda13.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cuda12.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cuda11.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_fixture\GLASS-Portable-win64-cpu.zip' --title 'GLASS S2 Gate 341 Failed Fixture' --notes-file 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_341_release_notes_failed_resident_result.md' --draft
```

## Checks

- PASS: `manifest_passed` - {'manifest_status': 'release_manifest_ready', 'failed_checks': []}
- PASS: `assets_present` - {'asset_count': 4}
- PASS: `asset_exists:cuda13` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_341_fixture\\GLASS-Portable-win64-cuda13.zip'}
- PASS: `asset_has_sha256:cuda13` - {'sha256': '81ef7633b1c7d700aff468c131055ee625b5f2efcc31b67ebaa1a1b35efb3d98'}
- PASS: `asset_nonempty:cuda13` - {'size_bytes': 20}
- PASS: `asset_exists:cuda12` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_341_fixture\\GLASS-Portable-win64-cuda12.zip'}
- PASS: `asset_has_sha256:cuda12` - {'sha256': 'a661671be01d3028d5580c506adf858600c1252c621cdc8d6dfc4a462e3b7fd6'}
- PASS: `asset_nonempty:cuda12` - {'size_bytes': 20}
- PASS: `asset_exists:cuda11` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_341_fixture\\GLASS-Portable-win64-cuda11.zip'}
- PASS: `asset_has_sha256:cuda11` - {'sha256': 'ca9d8a29bf75e27ef6e0d7eab2d6ee23496e78314be793293f219f2aa9918256'}
- PASS: `asset_nonempty:cuda11` - {'size_bytes': 20}
- PASS: `asset_exists:cpu` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_341_fixture\\GLASS-Portable-win64-cpu.zip'}
- PASS: `asset_has_sha256:cpu` - {'sha256': '843662196aad1d87a22bfff89308b04f5b579a43a9c945d823ae7a91a634a48e'}
- PASS: `asset_nonempty:cpu` - {'size_bytes': 17}
- PASS: `same_source_stamp` - {'source_stamps': ['s2-gate-341']}
- PASS: `windows_release_matrix_present` - {'path': 'runs\\checkpoints\\s2_gate_340_windows_release_matrix_failed_resident_result.json', 'required': True}
- PASS: `windows_release_matrix_type` - {'artifact_type': 'windows_release_matrix', 'required': 'windows_release_matrix'}
- FAIL: `windows_release_matrix_ready` - {'status': 'blocked', 'passed': False}
- FAIL: `windows_release_matrix_default_promotion_ready` - {'status': 'blocked', 'passed': False, 'default_change_ready': False}
- PASS: `windows_release_matrix_default_route_passed` - {'default_route_passed': True, 'route_contract_passed': True, 'route_check_count': 4}
- PASS: `windows_release_matrix_rejection_sample_accounting_passed` - {'check': True, 'status': 'passed', 'failed_count': 0}
- PASS: `windows_release_matrix_sample_accounting_closure_passed` - {'check': True, 'status': 'passed', 'present_count': 1, 'failed_count': 0, 'failed_items': []}
- FAIL: `windows_release_matrix_resident_result_contract_handoff_passed` - {'present': True, 'ready': False, 'status': 'failed', 'top_level_check': False, 'check_present': True, 'check_passed': False, 'phase2_check_passed': False, 'required_count': 1, 'failed_count': 1, 'failed_check_count': 1, 'failed_checks': ['source_terms_present'], 'failed_items': [{'backend': 'cuda_resident_stack', 'failed_checks': [{'evidence': {'actual': [], 'available': False, 'required': True}, 'name': 'source_terms_present'}], 'item': 'H', 'memory_mode': 'resident', 'passed': False, 'required': True, 'status': 'failed'}]}
- PASS: `windows_release_matrix_stack_engine_contract_ready` - {'present': True, 'ready': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'adoption_recommendation': 'stack_engine_default_ready', 'default_gap_count': 0, 'blocker_count': 0, 'blockers': []}
- PASS: `windows_release_matrix_resident_fastpath_release_handoff_ready` - {'present': True, 'ready': True, 'raw_ready': True, 'phase2_ready': True, 'agreement': True, 'decision_check_passed': True, 'phase2_check_passed': True, 'raw_status': 'passed', 'phase2_status': 'passed', 'raw_required': True, 'phase2_required': True, 'raw_mode': 'similarity_cuda_triangle', 'phase2_mode': 'similarity_cuda_triangle', 'raw_passed_check_count': 23, 'phase2_passed_check_count': 23, 'raw_failed_check_count': 0, 'phase2_failed_check_count': 0, 'raw_failed_checks': [], 'phase2_failed_checks': []}
- PASS: `windows_release_matrix_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200}
- PASS: `windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200}
- PASS: `windows_release_matrix_assets_present` - {'matrix_labels': ['cuda11', 'cuda12', 'cuda13', 'cpu'], 'asset_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'missing': []}
- PASS: `windows_release_matrix_try_order_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
