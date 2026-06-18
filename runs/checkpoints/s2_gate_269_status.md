# S2-Gate 269 Status

- Gate: S2-Gate 269
- Scope: Resident winsorized sweep contract audit
- Status: green
- Date: 2026-06-18

## Completed

- Added the default machine-readable resident winsorized sweep contract:
  `benchmarks/resident_winsorized_sweep_contract.json`.
- Added `glass.report.resident_winsorized_sweep_contract`, which audits a
  Gate268 sweep artifact for:
  - artifact type and pass status;
  - deterministic sweep configuration;
  - expected frame-count rows `8, 32, 128, 200`;
  - required 200-frame row presence and pass status;
  - hardened-vs-CPU RMS and max-absolute tolerances for the required row;
  - map agreement for weight, coverage, low rejection, and high rejection;
  - maximum hardened master RMS across the sweep;
  - required CPU/fast/hardened timing fields;
  - hardened native method and `hardened_cpu_parity` mode.
- Added CLI command:
  `glass resident-winsorized-sweep-audit`.
- Added focused contract tests and CLI help coverage.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.
- Generated audit artifacts from the Gate268 sweep:
  - `runs/checkpoints/s2_gate_269_resident_winsorized_sweep_audit.json`
  - `runs/checkpoints/s2_gate_269_resident_winsorized_sweep_audit.md`

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\resident_winsorized_sweep_contract.py src\glass\cli.py tests\test_resident_winsorized_sweep_contract.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_sweep_contract.py

.\.venv\Scripts\python.exe -m glass.cli resident-winsorized-sweep-audit --artifact runs\checkpoints\s2_gate_268_resident_winsorized_sweep.json --out runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.json --markdown runs\checkpoints\s2_gate_269_resident_winsorized_sweep_audit.md --fail-on-failure

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_sweep_contract.py tests\test_resident_winsorized_sweep.py tests\test_cli_smoke.py

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
- Focused sweep contract tests: `5 passed in 0.19s`.
- Related sweep/CLI tests: `30 passed in 2.54s`.
- Full pytest: `619 passed in 27.43s`.
- Gate269 sweep audit artifact: passed, with no failed checks.

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.

## Audit Summary

- Contract: `s2_gate_269_default_resident_winsorized_sweep`.
- Source sweep:
  `runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json`.
- Sweep status: passed.
- Required frame count: 200.
- Required 200-frame hardened master RMS vs CPU:
  `2.3066304440398834e-05`.
- Required 200-frame hardened master max abs vs CPU:
  `6.103515625e-05`.
- Maximum hardened master RMS across sweep:
  `2.3066304440398834e-05`.
- Required 200-frame CPU baseline:
  `0.01229839999723481 s`.
- Required 200-frame hardened CUDA:
  `0.0012743999977828935 s`.

## Known Limitations

- This gate audits the synthetic Gate268 frame-count sweep only.
- It does not replace the 200-light real-data benchmark.
- It does not exercise real FITS I/O, calibration, registration, LN,
  output-write behavior, or the full release benchmark command path.
- Timing fields are required to exist, but no wall-time upper bound is imposed.
- No CUDA kernel, image math, runtime default, package build/upload, release
  update, status handoff, status-compare change, or real-data run was
  performed.

## Next Step

Carry the Gate269 sweep-audit evidence into Phase 2 status or release-readiness
artifacts so 200-frame hardened winsorized parity drift remains visible before
future real-data hardened winsorized runs.

## Clean-Room Compliance

Compliant. This gate used only GLASS-generated sweep JSON, a GLASS-owned
contract, GLASS tests, and GLASS CLI code. It did not inspect external
proprietary source code and did not read or modify user image directories.
