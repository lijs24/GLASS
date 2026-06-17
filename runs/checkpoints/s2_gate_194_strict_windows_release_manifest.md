# GLASS Windows Release Manifest

- Status: `release_manifest_ready`
- Passed: `True`
- Recommendation: `ready_for_upload`
- Suite artifact: `runs\checkpoints\s2_gate_194_strict_windows_package_suite.json`
- Source stamps: `aa63510`

## Packages

| Label | Size bytes | SHA256 | Source | Zip |
| --- | ---: | --- | --- | --- |
| cuda13 | 341358345 | `bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273` | aa63510 | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip` |
| cuda12 | 341223006 | `72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31` | aa63510 | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip` |
| cuda11 | 342200540 | `2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681` | aa63510 | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip` |
| cpu | 296231852 | `32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d` | aa63510 | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip` |

## Checks

- PASS: `suite_passed` - {'suite_status': 'package_suite_ready', 'suite_failed_checks': []}
- PASS: `suite_has_packages` - {'package_count': 4}
- PASS: `zip_exists:cuda13` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip'}
- PASS: `zip_nonempty:cuda13` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip', 'size_bytes': 341358345}
- PASS: `zip_size_matches_smoke:cuda13` - {'smoke_zip_size_bytes': 341358345, 'manifest_size_bytes': 341358345}
- PASS: `suite_row_passed:cuda13` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cuda13` - {'sha256': 'bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273'}
- PASS: `zip_exists:cuda12` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda12.zip'}
- PASS: `zip_nonempty:cuda12` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda12.zip', 'size_bytes': 341223006}
- PASS: `zip_size_matches_smoke:cuda12` - {'smoke_zip_size_bytes': 341223006, 'manifest_size_bytes': 341223006}
- PASS: `suite_row_passed:cuda12` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cuda12` - {'sha256': '72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31'}
- PASS: `zip_exists:cuda11` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda11.zip'}
- PASS: `zip_nonempty:cuda11` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda11.zip', 'size_bytes': 342200540}
- PASS: `zip_size_matches_smoke:cuda11` - {'smoke_zip_size_bytes': 342200540, 'manifest_size_bytes': 342200540}
- PASS: `suite_row_passed:cuda11` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cuda11` - {'sha256': '2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681'}
- PASS: `zip_exists:cpu` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cpu.zip'}
- PASS: `zip_nonempty:cpu` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cpu.zip', 'size_bytes': 296231852}
- PASS: `zip_size_matches_smoke:cpu` - {'smoke_zip_size_bytes': 296231852, 'manifest_size_bytes': 296231852}
- PASS: `suite_row_passed:cpu` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cpu` - {'sha256': '32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d'}
- PASS: `same_source_stamp` - {'source_stamps': ['aa63510']}
