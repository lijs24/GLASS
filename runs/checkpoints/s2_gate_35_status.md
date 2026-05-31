# S2-Gate 35 Status: Benchmark Comparison In Main Report

## Gate

S2-Gate 35 brings benchmark comparison and acceptance-audit evidence into the
main HTML report. Compare and audit JSON files remain authoritative; the report
now surfaces their high-signal fields near the top of the page.

## Completed Content

- Added a `Benchmark comparison` HTML report section.
- `glass report` now auto-discovers the newest matching JSON artifacts in the
  run directory:
  - `*compare*.json`
  - `*acceptance_audit*.json`
- Added explicit report CLI overrides:
  - `--compare-json`
  - `--acceptance-audit`
- The report summary includes:
  - acceptance status
  - benchmark contract name
  - compare JSON path
  - acceptance-audit JSON path
  - GLASS elapsed seconds
  - reference elapsed seconds
  - speedup
  - shape-match status
  - RMS difference
  - P99 absolute difference
  - coverage fraction
  - compared pixels
  - active and zero-weight frames
  - light/bias/dark/flat frame counts
  - passed/failed check counts
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`
  - `tests/test_cli_smoke.py`

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_35_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_35_report.html`
- Gate 34 report size: `289787` bytes.
- Gate 35 report size: `291110` bytes.
- Benchmark comparison row shows:
  - acceptance status: `passed`
  - contract: `phase2_m38_h_200_resident_cuda_audit_maps`
  - GLASS time: `31.835984100122005 s`
  - reference time: `1092.541 s`
  - speedup: `34.3178020369665x`
  - RMS diff: `0.001558294284488301`
  - P99 absolute diff: `0.00043095467146486016`
  - coverage fraction: `0.9574613308418977`
  - compared pixels: `59028640`
  - active frames: `193`
  - zero-weight frames: `7`
  - light/bias/dark/flat frames: `200/20/20/20`
  - checks passed/failed: `86/0`

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests\test_cli_smoke.py::test_cli_help_commands`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\html_report.py src\glass\cli.py tests\test_cli_smoke.py`
- real-data report regeneration command above
- `Select-String` verification against the regenerated report
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`

## Test Results

- Targeted report/help tests: `2 passed in 0.19s`.
- Targeted lint: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `248 passed in 34.20s`.
- `git diff --check`: no whitespace errors.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Known Limitations

- This gate is report-only and does not change image math, artifact schemas, or
  resident CUDA execution.
- Auto-discovery chooses the newest matching compare/audit JSON by file mtime
  and name. Use explicit CLI paths when a run directory contains multiple
  benchmark comparisons that must be pinned exactly.
- The report summarizes compare/audit JSON fields; those JSON artifacts remain
  the authoritative evidence for audits.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The most useful follow-up is to add a compact acceptance-check failure table
when checks fail, so failed contracts are easy to triage from the main report.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned compare/audit artifacts and user-generated
reference timing/output metadata already captured by those artifacts. No
external implementation source was read or used.
