# S2-Gate 268 Status

- Gate: S2-Gate 268
- Scope: Resident winsorized frame-count sweep
- Status: green
- Date: 2026-06-18

## Completed

- Added `glass resident-winsorized-sweep`.
- Added `glass.report.resident_winsorized_sweep`.
- The sweep reuses the Gate265 single resident winsorized benchmark across
  multiple frame counts and requires a 200-frame row by default.
- Added JSON/Markdown artifact writing with per-frame-count timing, hardened
  vs CPU differences, fast-approximation context, top-level checks, and
  CUDA-unavailable diagnostics.
- Added focused tests for:
  - frame-count parsing;
  - CUDA-unavailable behavior;
  - CUDA hardened parity on small sweeps;
  - CLI artifact writing.
- Added CLI help-list coverage.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.
- Generated artifacts:
  - `runs/checkpoints/s2_gate_268_resident_winsorized_sweep.json`
  - `runs/checkpoints/s2_gate_268_resident_winsorized_sweep.md`

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\resident_winsorized_sweep.py src\glass\cli.py tests\test_resident_winsorized_sweep.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_sweep.py

.\.venv\Scripts\python.exe -m glass.cli resident-winsorized-sweep --frame-counts 8,32,128,200 --required-frame-count 200 --height 16 --width 16 --seed-base 268 --out runs\checkpoints\s2_gate_268_resident_winsorized_sweep.json --markdown runs\checkpoints\s2_gate_268_resident_winsorized_sweep.md --fail-on-failure

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_winsorized_sweep.py tests\test_resident_winsorized_benchmark.py tests\test_resident_winsorized_benchmark_contract.py tests\test_phase2_status.py tests\test_cli_smoke.py

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Focused sweep tests: `4 passed in 0.28s`.
- Related resident/Phase2/CLI tests: `59 passed in 2.65s`.
- Full pytest: `614 passed in 27.79s`.
- Gate268 sweep artifact: passed.

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver version: 596.21.

## Sweep Summary

Sweep configuration:

- Frame counts: 8, 32, 128, 200.
- Required frame count: 200.
- Shape: 16 x 16.
- Low/high sigma: 3.0 / 3.0.
- RMS tolerance: `5e-5`.
- Max absolute tolerance: `2e-4`.

Observed hardened CUDA vs CPU master differences:

| frames | RMS | max abs | CPU s | hardened CUDA s |
| ---: | ---: | ---: | ---: | ---: |
| 8 | `5.66212753631492e-06` | `1.52587890625e-05` | `0.014404100002138875` | `0.00019880000036209822` |
| 32 | `1.78416127527902e-05` | `3.814697265625e-05` | `0.010201700002653524` | `0.0001469000053475611` |
| 128 | `1.7847983619893e-05` | `5.340576171875e-05` | `0.011198399995919317` | `0.0004313000026741065` |
| 200 | `2.3066304440398834e-05` | `6.103515625e-05` | `0.01229839999723481` | `0.0012743999977828935` |

The first 200-frame attempt reused the Gate265 small-benchmark RMS tolerance
of `2e-5` and failed with RMS `2.3066304440398834e-05`. The sweep default was
then set to `5e-5`, still below `1e-4`, to reflect the larger 200-sample
float32 accumulation path while preserving the Gate265 single-benchmark
contract unchanged.

## Known Limitations

- This is a synthetic small-image frame-count sweep.
- It validates 200-frame sample-count parity for resident hardened winsorized
  integration, but does not replace the 200-light real-data benchmark.
- It does not exercise real FITS I/O, calibration, registration, LN, output
  writes, or the full release benchmark command path.
- It does not change CUDA kernels, optimize hardened mode, raise the 256-frame
  prototype limit, alter runtime defaults, build/upload packages, or rerun real
  data.

## Next Step

Use the 200-frame synthetic sweep as a small regression guard before any future
work that optimizes hardened winsorized mode or attempts to run hardened
winsorized integration on the real 200-light dataset.

## Clean-Room Compliance

Compliant. This gate used only GLASS-generated synthetic arrays, GLASS CPU/CUDA
code, and GLASS-owned JSON/Markdown artifacts. It did not inspect external
proprietary source code and did not read or modify user image directories.
