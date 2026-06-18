# GLASS Windows GitHub Release Plan

- Status: `release_plan_ready`
- Passed: `True`
- Publication ready: `True`
- Recommendation: `run_release_command`
- Tag: `v0.1.0-gate311-preflight`
- Title: `GLASS Windows Gate311 Preflight`
- Source stamps: `aa63510`
- GitHub CLI available: `False`
- GitHub CLI auth OK: `False`
- Publish script: `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_311_publish_release_direct_publication_guard.ps1`
- Publish script mode: `dry_run_requires_publish_switch`
- Windows release matrix: `release_matrix_ready`

## Assets

| Label | Size bytes | SHA256 | Path |
| --- | ---: | --- | --- |
| cuda13 | 341358345 | `bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip` |
| cuda12 | 341223006 | `72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip` |
| cuda11 | 342200540 | `2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip` |
| cpu | 296231852 | `32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip` |

## Windows Release Matrix Handoff

- Matrix path: `runs\checkpoints\s2_gate_310_windows_release_matrix_direct_publication_guard.json`
- Matrix status: `release_matrix_ready`
- Matrix passed: `True`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`
- Default promotion: `default_promotion_ready` passed `True`
- Default route contract/checks: `True`/`4`
- Release direct publication guard: ready=`True` check=`True` source=`explicit_resident_artifacts_json`/`resident_artifacts_json_fallback` lights=`200`
- Default-promotion release direct guard: ready=`True` check=`True` lights=`200`
- StackEngine default contract: ready=`True` phase2-check=`True` gaps=`0` blockers=`0`
- Rejection sample accounting: `passed` failed `0`
- Sample accounting closure: `passed` present=`0` failed=`0`

## Phase 2 Handoff Preflight

- Phase 2 status path: `runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_handoff.json`
- Phase 2 status: `green`
- Phase 2 latest gate: `310`
- Resident registration fast path: `present`
- Resident registration fast path contract: `passed` checks `24` failed `0`
- Resident registration fast path mode: `similarity_cuda_triangle`
- Descriptor fit batch: `True` mode `native_batch_shared_reference_device`
- Descriptor device reuse: `{'moving': True, 'output': True, 'reference': True}`
- Pixel refine batch: `True` metric `flattened_frame_candidate_grid`
- Triangle warp batch: `True` mode `native_matrix_lanczos3_frames` frames `188`
- Resident warp copy mode: `default_stream_async_device_to_device`
- Resident warp scratch bytes: `493209636`
- Pipeline contract: `passed`
- Pipeline contract passed: `True`
- Pipeline contract failed checks: `0`
- Pipeline integration outputs/maps: `1`/`6`
- Pipeline integration DQ contract: `True`
- Pipeline StackEngine result contract: `True`
- Pipeline resident result contract: `True`
- Pipeline pixel verification: `True`
- Pipeline DQ pixels match summary: `True`
- Pipeline coverage pixels match DQ: `True`
- Pipeline rejection pixels match DQ: `True`
- Pipeline rejection sample accounting: `passed` check `True` failed `0`
- Pipeline sample accounting closure: `passed` check `True` failed `0`
- StackEngine default contract: `passed` check `True` gaps `0` blockers `0`
- StackEngine default recommendations: `stack_engine_default_ready`/`stack_engine_default_ready`
- Release decision: `default_change_ready`
- Release recommendation: `promote_default_candidate`
- Default change ready: `True`
- Runtime repeat runs: `3`
- Runtime repeat best: `gate218_default_repeat02` `22.598500299995067` s
- Runtime repeat ratio vs best: `1.053510511049479`
- Phase 2 status compare path: `runs\checkpoints\s2_gate_310_phase2_status_direct_publication_guard_compare.json`
- Phase 2 status compare: `passed`
- Phase 2 compare baseline gate: `309`
- Phase 2 compare candidate gate: `310`

## Command

```powershell
gh release create v0.1.0-gate311-preflight 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip' --title 'GLASS Windows Gate311 Preflight' --notes-file 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_311_github_release_notes_direct_publication_guard.md' --draft
```

## Checks

- PASS: `manifest_passed` - {'manifest_status': 'release_manifest_ready', 'failed_checks': []}
- PASS: `assets_present` - {'asset_count': 4}
- PASS: `asset_exists:cuda13` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip'}
- PASS: `asset_has_sha256:cuda13` - {'sha256': 'bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273'}
- PASS: `asset_nonempty:cuda13` - {'size_bytes': 341358345}
- PASS: `asset_exists:cuda12` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda12.zip'}
- PASS: `asset_has_sha256:cuda12` - {'sha256': '72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31'}
- PASS: `asset_nonempty:cuda12` - {'size_bytes': 341223006}
- PASS: `asset_exists:cuda11` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda11.zip'}
- PASS: `asset_has_sha256:cuda11` - {'sha256': '2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681'}
- PASS: `asset_nonempty:cuda11` - {'size_bytes': 342200540}
- PASS: `asset_exists:cpu` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cpu.zip'}
- PASS: `asset_has_sha256:cpu` - {'sha256': '32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d'}
- PASS: `asset_nonempty:cpu` - {'size_bytes': 296231852}
- PASS: `same_source_stamp` - {'source_stamps': ['aa63510']}
- PASS: `phase2_status_present` - {'path': 'runs\\checkpoints\\s2_gate_310_phase2_status_direct_publication_guard_handoff.json'}
- PASS: `phase2_status_type` - {'artifact_type': 'glass_phase2_status', 'required': 'glass_phase2_status'}
- PASS: `phase2_status_green` - {'status': 'green', 'passed': True, 'latest_gate': 310}
- PASS: `phase2_pipeline_rejection_sample_accounting_passed` - {'check': True, 'status': 'passed', 'failed_count': 0}
- PASS: `phase2_pipeline_sample_accounting_closure_passed` - {'check': True, 'status': 'passed', 'present_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `phase2_stack_engine_default_contract_ready` - {'present': True, 'phase2_check_passed': True, 'audit_type': 'stack_engine_default_contract', 'status': 'passed', 'passed': True, 'scope': 'all', 'default_promotion_ready': True, 'default_promotion_status': 'ready', 'adoption_recommendation': 'stack_engine_default_ready', 'default_promotion_recommendation': 'stack_engine_default_ready', 'default_gap_count': 0, 'blocker_count': 0, 'blockers': []}
- PASS: `phase2_status_compare_present` - {'path': 'runs\\checkpoints\\s2_gate_310_phase2_status_direct_publication_guard_compare.json'}
- PASS: `phase2_status_compare_type` - {'artifact_type': 'glass_phase2_status_compare', 'required': 'glass_phase2_status_compare'}
- PASS: `phase2_status_compare_passed` - {'status': 'passed', 'passed': True, 'baseline_gate': 309, 'candidate_gate': 310}
- PASS: `windows_release_matrix_present` - {'path': 'runs\\checkpoints\\s2_gate_310_windows_release_matrix_direct_publication_guard.json', 'required': True}
- PASS: `windows_release_matrix_type` - {'artifact_type': 'windows_release_matrix', 'required': 'windows_release_matrix'}
- PASS: `windows_release_matrix_ready` - {'status': 'release_matrix_ready', 'passed': True}
- PASS: `windows_release_matrix_default_promotion_ready` - {'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True}
- PASS: `windows_release_matrix_default_route_passed` - {'default_route_passed': True, 'route_contract_passed': True, 'route_check_count': 4}
- PASS: `windows_release_matrix_rejection_sample_accounting_passed` - {'check': True, 'status': 'passed', 'failed_count': 0}
- PASS: `windows_release_matrix_sample_accounting_closure_passed` - {'check': True, 'status': 'passed', 'present_count': 0, 'failed_count': 0, 'failed_items': []}
- PASS: `windows_release_matrix_stack_engine_contract_ready` - {'present': True, 'ready': True, 'phase2_check_passed': True, 'status': 'passed', 'passed': True, 'scope': 'all', 'adoption_recommendation': 'stack_engine_default_ready', 'default_gap_count': 0, 'blocker_count': 0, 'blockers': []}
- PASS: `windows_release_matrix_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200}
- PASS: `windows_release_matrix_default_promotion_release_decision_direct_runtime_publication_guard_passed` - {'present': True, 'ready': True, 'decision_check_passed': True, 'source_ready': True, 'count_ready': True, 'leaf_checks_ready': True, 'acceptance_source': 'explicit_resident_artifacts_json', 'calibration_source': 'resident_artifacts_json_fallback', 'resident_lights': 200}
- PASS: `windows_release_matrix_assets_present` - {'matrix_labels': ['cuda11', 'cuda12', 'cuda13', 'cpu'], 'asset_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'missing': []}
- PASS: `windows_release_matrix_try_order_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
- PASS: `phase2_release_matrix_stack_engine_contract_agree` - {'phase2_ready': True, 'matrix_ready': True, 'phase2_gap_count': 0, 'matrix_gap_count': 0, 'phase2_blocker_count': 0, 'matrix_blocker_count': 0}
