# GLASS Windows Package Smoke

- Status: `package_smoke_passed`
- Passed: `True`
- Recommendation: `portable_package_ready_for_next_release_step`
- Package root: `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS`
- Zip: `C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip`
- Zip size bytes: `339732356`
- Source stamp: `245c2f9`

## Checks

- PASS: `package_root_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS'}
- PASS: `runtime_python_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\runtime\\python.exe'}
- PASS: `glass_cmd_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\glass.cmd'}
- PASS: `glass_doctor_cmd_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\glass-doctor.cmd'}
- PASS: `readme_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\README.md'}
- PASS: `license_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\LICENSE'}
- PASS: `docs_windows_release_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\docs\\windows_release.md'}
- PASS: `source_stamp_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\source'}
- PASS: `package_manifest_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS\\package_manifest.json'}
- PASS: `portable_zip_exists` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip'}
- PASS: `portable_zip_nonempty` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip', 'size_bytes': 339732356}
- PASS: `package_label_matches_expected` - {'actual': 'cuda13', 'required': 'cuda13'}
- PASS: `package_manifest_cuda_build` - {'actual': True, 'required': True}
- PASS: `source_stamp_matches_expected` - {'actual': '245c2f9', 'required': '245c2f9'}
- PASS: `portable_doctor_exit_zero` - {'returncode': 0}
- PASS: `portable_help_exit_zero` - {'returncode': 0}
- PASS: `portable_doctor_json_written` - {'path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\portable_doctor.json', 'exists': True}
- PASS: `portable_doctor_product` - {'actual': 'GLASS', 'required': 'GLASS'}
- PASS: `portable_cuda_requirement` - {'actual': True, 'required': True}
