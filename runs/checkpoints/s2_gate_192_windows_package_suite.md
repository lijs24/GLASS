# GLASS Windows Package Suite

- Status: `package_suite_ready`
- Passed: `True`
- Recommendation: `publish_package_suite`
- Source stamps: `245c2f9, 260c832, a1604b0, fbf454a`

## Packages

| Label | Passed | Source | Zip size | CUDA required | CUDA available |
| --- | --- | --- | --- | --- | --- |
| cuda13 | True | 245c2f9 | 339732356 | True | True |
| cuda12 | True | fbf454a | 341206870 | True | True |
| cuda11 | True | 260c832 | 342183616 | True | True |
| cpu | True | a1604b0 | 296215418 | False | False |

## Checks

- PASS: `smoke_present:cuda13` - {'path': 'runs\\checkpoints\\s2_gate_184_cuda13_portable_smoke.json'}
- PASS: `smoke_passed:cuda13` - {'status': 'package_smoke_passed', 'failed_checks': []}
- PASS: `package_label_matches:cuda13` - {'actual': 'cuda13', 'required': 'cuda13'}
- PASS: `zip_nonempty:cuda13` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda13.zip', 'zip_size_bytes': 339732356}
- PASS: `smoke_present:cuda12` - {'path': 'runs\\checkpoints\\s2_gate_188_cuda12_portable_smoke.json'}
- PASS: `smoke_passed:cuda12` - {'status': 'package_smoke_passed', 'failed_checks': []}
- PASS: `package_label_matches:cuda12` - {'actual': 'cuda12', 'required': 'cuda12'}
- PASS: `zip_nonempty:cuda12` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda12.zip', 'zip_size_bytes': 341206870}
- PASS: `smoke_present:cuda11` - {'path': 'runs\\checkpoints\\s2_gate_190_cuda11_portable_smoke.json'}
- PASS: `smoke_passed:cuda11` - {'status': 'package_smoke_passed', 'failed_checks': []}
- PASS: `package_label_matches:cuda11` - {'actual': 'cuda11', 'required': 'cuda11'}
- PASS: `zip_nonempty:cuda11` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cuda11.zip', 'zip_size_bytes': 342183616}
- PASS: `smoke_present:cpu` - {'path': 'runs\\checkpoints\\s2_gate_191_cpu_portable_smoke.json'}
- PASS: `smoke_passed:cpu` - {'status': 'package_smoke_passed', 'failed_checks': []}
- PASS: `package_label_matches:cpu` - {'actual': 'cpu', 'required': 'cpu'}
- PASS: `zip_nonempty:cpu` - {'zip_path': 'C:\\Users\\ljs\\WORK\\astro\\gpuwbpp\\.release\\windows\\GLASS-Portable-win64-cpu.zip', 'zip_size_bytes': 296215418}
