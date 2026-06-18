# S2-Gate 266 Status: Resident Winsorized Microbenchmark Contract Audit

## Gate

S2-Gate 266: Resident Winsorized Microbenchmark Contract Audit

## Completed

- Added the default machine-readable resident winsorized microbenchmark contract:
  `benchmarks/resident_winsorized_microbenchmark_contract.json`.
- Added `glass.report.resident_winsorized_benchmark_contract`, which audits a
  Gate265 benchmark artifact for:
  - benchmark pass status;
  - CUDA availability evidence;
  - deterministic synthetic configuration drift;
  - hardened resident CUDA vs CPU RMS and max-absolute tolerances;
  - required CPU/fast/hardened timing fields;
  - hardened native method and `hardened_cpu_parity` timing mode;
  - fast-approximation context presence without treating it as CPU parity.
- Added CLI command:
  `glass resident-winsorized-benchmark-audit`.
- Added focused tests and CLI help coverage.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.
- Generated audit artifacts from the Gate265 microbenchmark:
  - `runs/checkpoints/s2_gate_266_resident_winsorized_benchmark_audit.json`
  - `runs/checkpoints/s2_gate_266_resident_winsorized_benchmark_audit.md`

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\resident_winsorized_benchmark_contract.py src\glass\cli.py tests\test_resident_winsorized_benchmark_contract.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_benchmark_contract.py

.\.venv\Scripts\python.exe -m glass.cli resident-winsorized-benchmark-audit --artifact runs\checkpoints\s2_gate_265_resident_winsorized_benchmark.json --out runs\checkpoints\s2_gate_266_resident_winsorized_benchmark_audit.json --markdown runs\checkpoints\s2_gate_266_resident_winsorized_benchmark_audit.md --fail-on-failure

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_benchmark_contract.py tests\test_resident_winsorized_benchmark.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q

@'
import glass_cuda
print('cuda_available', glass_cuda.cuda_available())
if glass_cuda.cuda_available():
    print('devices', glass_cuda.list_devices())
'@ | .\.venv\Scripts\python.exe -
```

## Test Results

- Ruff: passed.
- Focused contract tests: `6 passed in 0.22s`.
- Related benchmark/CLI tests: `30 passed in 2.54s`.
- Full pytest: `608 passed in 27.70s`.
- Gate266 benchmark audit: passed, with no failed checks.

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.

## Audit Summary

- Contract: `s2_gate_266_default_resident_winsorized_microbenchmark`.
- Source benchmark:
  `runs/checkpoints/s2_gate_265_resident_winsorized_benchmark.json`.
- Benchmark status: passed.
- Frame count: 8.
- Shape: 16 x 16.
- Hardened master RMS vs CPU: `5.781343294611998e-06`.
- Hardened master max abs vs CPU: `1.52587890625e-05`.
- Fast approximation master RMS vs CPU: `0.566935986706338`.
- Audit status: passed.

## Known Limitations

- This gate audits the synthetic Gate265 microbenchmark only.
- It does not replace the 200-light real-data benchmark.
- The default contract requires timing fields to exist but does not enforce a
  wall-time upper bound, because microbenchmark timing is hardware and load
  sensitive.
- The fast resident winsorized approximation remains context-only and is not
  treated as CPU parity.
- No CUDA kernel, image math, runtime default, package build, package upload,
  release update, or real-data run was performed.

## Next Step

Use the new contract audit as the small regression guard before future
hardened winsorized optimization or any attempt to promote the hardened mode.

## Clean-Room Compliance

Compliant. This gate used only GLASS-generated JSON artifacts, GLASS CPU/CUDA
code, and a GLASS-owned benchmark contract. It did not inspect or use external
proprietary source code and did not read or modify user image directories.
