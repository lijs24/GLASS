# GLASS Windows Release Manifest

- Status: `release_manifest_ready`
- Passed: `True`
- Recommendation: `ready_for_upload`
- Suite artifact: `runs\checkpoints\s2_gate_192_windows_package_suite.json`
- Source stamps: `245c2f9, 260c832, a1604b0, fbf454a`

## Packages

| Label | Size bytes | SHA256 | Source | Zip |
| --- | ---: | --- | --- | --- |
| cuda13 | 339732356 | `87023bac87deaec4298cb4351b250f40d4a53b8c55165b59d4cdb83dba7f5a54` | 245c2f9 | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip` |
| cuda12 | 341206870 | `5fd272b0525ddb1222115f2dfc2ae67fcdab80eadcdd522b6c89cd4d03d87242` | fbf454a | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip` |
| cuda11 | 342183616 | `d1d5a23a46e4e00cb95ce87c3a732f02863861ec934e6ad7d171166ce5f8f5a5` | 260c832 | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip` |
| cpu | 296215418 | `71ace05d2abde81acf2122b4d1891e1bff290b63f71f859bb2d1e60a71eb38a6` | a1604b0 | `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip` |

## Checks

- PASS: `suite_passed` - {'suite_status': 'package_suite_ready', 'suite_failed_checks': []}
- PASS: `suite_has_packages` - {'package_count': 4}
- PASS: `zip_exists:cuda13` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip'}
- PASS: `zip_nonempty:cuda13` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip', 'size_bytes': 339732356}
- PASS: `zip_size_matches_smoke:cuda13` - {'smoke_zip_size_bytes': 339732356, 'manifest_size_bytes': 339732356}
- PASS: `suite_row_passed:cuda13` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cuda13` - {'sha256': '87023bac87deaec4298cb4351b250f40d4a53b8c55165b59d4cdb83dba7f5a54'}
- PASS: `zip_exists:cuda12` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda12.zip'}
- PASS: `zip_nonempty:cuda12` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda12.zip', 'size_bytes': 341206870}
- PASS: `zip_size_matches_smoke:cuda12` - {'smoke_zip_size_bytes': 341206870, 'manifest_size_bytes': 341206870}
- PASS: `suite_row_passed:cuda12` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cuda12` - {'sha256': '5fd272b0525ddb1222115f2dfc2ae67fcdab80eadcdd522b6c89cd4d03d87242'}
- PASS: `zip_exists:cuda11` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda11.zip'}
- PASS: `zip_nonempty:cuda11` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda11.zip', 'size_bytes': 342183616}
- PASS: `zip_size_matches_smoke:cuda11` - {'smoke_zip_size_bytes': 342183616, 'manifest_size_bytes': 342183616}
- PASS: `suite_row_passed:cuda11` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cuda11` - {'sha256': 'd1d5a23a46e4e00cb95ce87c3a732f02863861ec934e6ad7d171166ce5f8f5a5'}
- PASS: `zip_exists:cpu` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cpu.zip'}
- PASS: `zip_nonempty:cpu` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cpu.zip', 'size_bytes': 296215418}
- PASS: `zip_size_matches_smoke:cpu` - {'smoke_zip_size_bytes': 296215418, 'manifest_size_bytes': 296215418}
- PASS: `suite_row_passed:cpu` - {'suite_row_passed': True}
- PASS: `sha256_recorded:cpu` - {'sha256': '71ace05d2abde81acf2122b4d1891e1bff290b63f71f859bb2d1e60a71eb38a6'}
