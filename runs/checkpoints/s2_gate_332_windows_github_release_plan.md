# GLASS Windows GitHub Release Plan

- Status: `release_plan_ready`
- Passed: `True`
- Publication ready: `True`
- Recommendation: `run_release_command`
- Tag: `v0.1.0-gate332`
- Title: `GLASS Gate332 Windows Fixture`
- Source stamps: `abc1234`
- GitHub CLI available: `False`
- GitHub CLI auth OK: `False`
- Publish script: `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_332_publish_dry_run.ps1`
- Publish script mode: `dry_run_requires_publish_switch`
- Windows release matrix: `release_matrix_ready`

## Assets

| Label | Size bytes | SHA256 | Path |
| --- | ---: | --- | --- |
| cuda13 | 27 | `0000000000000000000000000000000000000000000000000000000000000001` | `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_332_fixture\GLASS-Portable-win64-cuda13.zip` |

## Windows Release Matrix Handoff

- Matrix path: `runs\checkpoints\s2_gate_332_fixture\windows_release_matrix.json`
- Matrix status: `release_matrix_ready`
- Matrix passed: `True`
- Primary package: `cuda13`
- Try order: `cuda13, cpu`
- Default promotion: `default_promotion_ready` passed `True`
- Default route contract/checks: `True`/`4`
- Release direct publication guard: ready=`True` check=`True` source=`explicit_resident_artifacts_json`/`resident_artifacts_json_fallback` lights=`200`
- Default-promotion release direct guard: ready=`True` check=`True` lights=`200`
- StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`
- Resident fastpath release handoff: ready=`True` raw=`passed` phase2=`passed` agreement=`True` checks=`23`
- Rejection sample accounting: `passed` failed `0`
- Sample accounting closure: `passed` present=`1` failed=`0`

## Command

```powershell
gh release create v0.1.0-gate332 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_332_fixture\GLASS-Portable-win64-cuda13.zip' --title 'GLASS Gate332 Windows Fixture' --notes-file 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_332_release_notes.md' --draft
```

## Checks

- PASS: `manifest_passed` - {'manifest_status': 'release_manifest_ready', 'failed_checks': []}
- PASS: `assets_present` - {'asset_count': 1}
- PASS: `asset_exists:cuda13` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\runs\\checkpoints\\s2_gate_332_fixture\\GLASS-Portable-win64-cuda13.zip'}
- PASS: `asset_has_sha256:cuda13` - {'sha256': '0000000000000000000000000000000000000000000000000000000000000001'}
- PASS: `asset_nonempty:cuda13` - {'size_bytes': 27}
- PASS: `same_source_stamp` - {'source_stamps': ['abc1234']}
- PASS: `windows_release_matrix_present` - {'path': 'runs\\checkpoints\\s2_gate_332_fixture\\windows_release_matrix.json', 'required': True}
- PASS: `windows_release_matrix_type` - {'artifact_type': 'windows_release_matrix', 'required': 'windows_release_matrix'}
- PASS: `windows_release_matrix_ready` - {'status': 'release_matrix_ready', 'passed': True}
- PASS: `windows_release_matrix_default_promotion_ready` - {'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True}
- PASS: `windows_release_matrix_default_route_passed` - {'default_route_passed': True, 'route_contract_passed': True, 'route_check_count': 4}
- PASS: `windows_release_matrix_rejection_sample_accounting_passed` - {'check': True, 'status': 'passed', 'failed_count': 0}
- PASS: `windows_release_matrix_sample_accounting_closure_passed` - {'check': True, 'status': 'passed', 'present_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: `windows_release_matrix_stack_engine_contract_ready` - {'present': True, 'ready': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'adoption_recommendation': 'stack_engine_default_ready', 'default_gap_count': 0, 'blocker_count': 0, 'blockers': []}
- PASS: `windows_release_matrix_resident_fastpath_release_handoff_ready` - {'present': True, 'ready': True, 'raw_ready': True, 'phase2_ready': True, 'agreement': True, 'decision_check_passed': True, 'phase2_check_passed': True, 'raw_status': 'passed', 'phase2_status': 'passed', 'raw_required': True, 'phase2_required': True, 'raw_mode': 'similarity_cuda_triangle', 'phase2_mode': 'similarity_cuda_triangle', 'raw_passed_check_count': 23, 'phase2_passed_check_count': 23, 'raw_failed_check_count': 0, 'phase2_failed_check_count': 0, 'raw_failed_checks': [], 'phase2_failed_checks': []}
- PASS: `windows_release_matrix_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200}
- PASS: `windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200}
- PASS: `windows_release_matrix_assets_present` - {'matrix_labels': ['cuda13'], 'asset_labels': ['cuda13'], 'missing': []}
- PASS: `windows_release_matrix_try_order_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cpu']}
