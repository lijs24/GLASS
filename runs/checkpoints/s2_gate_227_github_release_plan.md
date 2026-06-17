# GLASS Windows GitHub Release Plan

- Status: `release_plan_ready`
- Passed: `True`
- Publication ready: `True`
- Recommendation: `run_release_command`
- Tag: `v0.1.0-phase2-gate227`
- Title: `GLASS Phase 2 Gate 227 Windows packages`
- Source stamps: `aa63510`
- GitHub CLI available: `False`
- GitHub CLI auth OK: `False`
- Publish script: `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_227_publish_release.ps1`
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

- Matrix path: `runs\checkpoints\s2_gate_226_windows_release_matrix.json`
- Matrix status: `release_matrix_ready`
- Matrix passed: `True`
- Primary package: `cuda13`
- Try order: `cuda13, cuda12, cuda11, cpu`
- Default promotion: `default_promotion_ready` passed `True`
- Default route contract/checks: `True`/`4`

## Phase 2 Handoff Preflight

- Phase 2 status path: `runs\checkpoints\s2_gate_226_phase2_status.json`
- Phase 2 status: `green`
- Phase 2 latest gate: `226`
- Native guardrails bundle: `present`
- Native resident contract source: `run_default`
- Native resident result run default: `True`
- Native resident result contract: `C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view\resident_result_contract.json`
- Native calibration artifact: `True`
- Native calibration masters: `3`
- Native calibrated lights: `200`
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
- Release decision: `default_change_ready`
- Release recommendation: `promote_default_candidate`
- Default change ready: `True`
- Runtime repeat runs: `3`
- Runtime repeat best: `gate218_default_repeat02` `22.598500299995067` s
- Runtime repeat ratio vs best: `1.053510511049479`
- Phase 2 status compare path: `runs\checkpoints\s2_gate_226_phase2_status_compare.json`
- Phase 2 status compare: `passed`
- Phase 2 compare baseline gate: `225`
- Phase 2 compare candidate gate: `226`

## Command

```powershell
gh release create v0.1.0-phase2-gate227 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip' --title 'GLASS Phase 2 Gate 227 Windows packages' --notes-file 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_227_github_release_notes.md' --draft
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
- PASS: `phase2_status_present` - {'path': 'runs\\checkpoints\\s2_gate_226_phase2_status.json'}
- PASS: `phase2_status_type` - {'artifact_type': 'glass_phase2_status', 'required': 'glass_phase2_status'}
- PASS: `phase2_status_green` - {'status': 'green', 'passed': True, 'latest_gate': 226}
- PASS: `phase2_status_compare_present` - {'path': 'runs\\checkpoints\\s2_gate_226_phase2_status_compare.json'}
- PASS: `phase2_status_compare_type` - {'artifact_type': 'glass_phase2_status_compare', 'required': 'glass_phase2_status_compare'}
- PASS: `phase2_status_compare_passed` - {'status': 'passed', 'passed': True, 'baseline_gate': 225, 'candidate_gate': 226}
- PASS: `windows_release_matrix_present` - {'path': 'runs\\checkpoints\\s2_gate_226_windows_release_matrix.json', 'required': True}
- PASS: `windows_release_matrix_type` - {'artifact_type': 'windows_release_matrix', 'required': 'windows_release_matrix'}
- PASS: `windows_release_matrix_ready` - {'status': 'release_matrix_ready', 'passed': True}
- PASS: `windows_release_matrix_default_promotion_ready` - {'status': 'default_promotion_ready', 'passed': True, 'default_change_ready': True}
- PASS: `windows_release_matrix_default_route_passed` - {'default_route_passed': True, 'route_contract_passed': True, 'route_check_count': 4}
- PASS: `windows_release_matrix_assets_present` - {'matrix_labels': ['cuda11', 'cuda12', 'cuda13', 'cpu'], 'asset_labels': ['cpu', 'cuda11', 'cuda12', 'cuda13'], 'missing': []}
- PASS: `windows_release_matrix_try_order_has_cpu_fallback` - {'ordered_try_list': ['cuda13', 'cuda12', 'cuda11', 'cpu']}
