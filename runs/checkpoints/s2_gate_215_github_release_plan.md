# GLASS Windows GitHub Release Plan

- Status: `release_plan_ready`
- Passed: `True`
- Publication ready: `True`
- Recommendation: `run_release_command`
- Tag: `v0.1.0-phase2-gate215`
- Title: `GLASS Phase 2 Gate 215 Windows packages`
- Source stamps: `aa63510`
- GitHub CLI available: `False`
- GitHub CLI auth OK: `False`
- Publish script: `C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_215_publish_release.ps1`
- Publish script mode: `dry_run_requires_publish_switch`

## Assets

| Label | Size bytes | SHA256 | Path |
| --- | ---: | --- | --- |
| cuda13 | 341358345 | `bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip` |
| cuda12 | 341223006 | `72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip` |
| cuda11 | 342200540 | `2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip` |
| cpu | 296231852 | `32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d` | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip` |

## Phase 2 Handoff Preflight

- Phase 2 status path: `runs\checkpoints\s2_gate_215_phase2_status.json`
- Phase 2 status: `green`
- Phase 2 latest gate: `215`
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
- Phase 2 status compare path: `runs\checkpoints\s2_gate_215_phase2_status_compare.json`
- Phase 2 status compare: `passed`
- Phase 2 compare baseline gate: `214`
- Phase 2 compare candidate gate: `215`

## Command

```powershell
gh release create v0.1.0-phase2-gate215 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip' 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip' --title 'GLASS Phase 2 Gate 215 Windows packages' --notes-file 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_215_release_notes.md' --draft
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
- PASS: `phase2_status_present` - {'path': 'runs\\checkpoints\\s2_gate_215_phase2_status.json'}
- PASS: `phase2_status_type` - {'artifact_type': 'glass_phase2_status', 'required': 'glass_phase2_status'}
- PASS: `phase2_status_green` - {'status': 'green', 'passed': True, 'latest_gate': 215}
- PASS: `phase2_status_compare_present` - {'path': 'runs\\checkpoints\\s2_gate_215_phase2_status_compare.json'}
- PASS: `phase2_status_compare_type` - {'artifact_type': 'glass_phase2_status_compare', 'required': 'glass_phase2_status_compare'}
- PASS: `phase2_status_compare_passed` - {'status': 'passed', 'passed': True, 'baseline_gate': 214, 'candidate_gate': 215}
