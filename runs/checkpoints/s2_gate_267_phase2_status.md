# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 267 (green)
- Checkpoint path: runs\checkpoints\s2_gate_267_status.md

## CUDA

- CUDA available: True
- Native extension loaded: True
- Primary GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM MiB: 97886
- Driver: 596.21

## Resident Winsorized Benchmark Audit

- Status: passed
- Passed: True
- Contract: s2_gate_266_default_resident_winsorized_microbenchmark
- Benchmark: runs\checkpoints\s2_gate_265_resident_winsorized_benchmark.json
- Check count: 21
- Failed checks: []
- Frame count: 8
- Shape: [16, 16]
- Hardened master RMS: 5.781343294611998e-06
- Hardened master max abs: 1.52587890625e-05
- Fast approximation master RMS: 0.566935986706338
- CUDA hardened seconds: 0.000185800003237091

## Checks

- PASS: latest_checkpoint_green - {'gate': 267, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: resident_winsorized_benchmark_audit_passed - {'status': 'passed', 'contract_name': 's2_gate_266_default_resident_winsorized_microbenchmark', 'check_count': 21, 'failed_check_count': 0, 'failed_checks': [], 'hardened_master_rms': 5.781343294611998e-06, 'hardened_master_max_abs': 1.52587890625e-05, 'fast_approx_master_rms': 0.566935986706338}
