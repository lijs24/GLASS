# GLASS Phase 2 Status

- Status: green
- Latest checkpoint: S2-Gate 271 (green)
- Checkpoint path: runs\checkpoints\s2_gate_271_status.md

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

## Resident Winsorized Sweep Audit

- Status: passed
- Passed: True
- Contract: s2_gate_269_default_resident_winsorized_sweep
- Sweep: runs\checkpoints\s2_gate_268_resident_winsorized_sweep.json
- Check count: 27
- Failed checks: []
- Frame counts: [8, 32, 128, 200]
- Run count: 4
- Required frame count: 200
- Required frame count passed: True
- Required frame master RMS: 2.3066304440398834e-05
- Required frame master max abs: 6.103515625e-05
- Max hardened master RMS: 2.3066304440398834e-05
- Required frame hardened CUDA seconds: 0.0012743999977828935

## Checks

- PASS: latest_checkpoint_green - {'gate': 271, 'status': 'green'}
- PASS: cuda_doctor_available - {'cuda_available': True, 'primary_gpu': 'NVIDIA RTX PRO 6000 Blackwell Workstation Edition'}
- PASS: resident_winsorized_benchmark_audit_passed - {'status': 'passed', 'contract_name': 's2_gate_266_default_resident_winsorized_microbenchmark', 'check_count': 21, 'failed_check_count': 0, 'failed_checks': [], 'hardened_master_rms': 5.781343294611998e-06, 'hardened_master_max_abs': 1.52587890625e-05, 'fast_approx_master_rms': 0.566935986706338}
- PASS: resident_winsorized_sweep_audit_passed - {'status': 'passed', 'contract_name': 's2_gate_269_default_resident_winsorized_sweep', 'check_count': 27, 'failed_check_count': 0, 'failed_checks': [], 'required_frame_count': 200, 'required_frame_count_passed': True, 'required_frame_master_rms': 2.3066304440398834e-05, 'required_frame_master_max_abs': 6.103515625e-05, 'max_hardened_master_rms': 2.3066304440398834e-05}
