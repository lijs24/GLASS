# S2-Gate 36 Status: Acceptance Failure Triage In Main Report

## Gate

S2-Gate 36 adds a compact failed-check triage table to the main HTML report.
Gate 35 made benchmark comparison visible; this gate makes failed acceptance
checks immediately actionable when a contract breaks.

## Completed Content

- Added an `Acceptance check failures` HTML report section.
- The section lists only failed acceptance-audit checks.
- Each failed check row includes:
  - check name
  - note
  - actual value
  - required value/threshold
  - compact remaining evidence fields
- Green runs show no failure rows while keeping the full authoritative check
  list in the acceptance-audit JSON.
- Added a failed-audit CLI report fixture that verifies:
  - failed checks are rendered
  - passed checks are not rendered in the failure table
  - evidence is compactly exposed
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_36_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_36_report.html`
- Gate 35 report size: `291110` bytes.
- Gate 36 report size: `291325` bytes.
- Benchmark comparison remains visible and shows:
  - acceptance status: `passed`
  - contract: `phase2_m38_h_200_resident_cuda_audit_maps`
  - speedup: `34.3178020369665x`
  - checks passed/failed: `86/0`
- `Acceptance check failures` appears once.
- Because the real run is green, the failure table reports `No rows.`
- The real report does not list `maximum_rms_diff` as a failure.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests\test_cli_smoke.py::test_cli_report_lists_failed_acceptance_checks`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\html_report.py tests\test_cli_smoke.py`
- real-data report regeneration command above
- `Select-String` verification against the regenerated report
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`

## Test Results

- Targeted report tests: `2 passed in 0.14s`.
- Targeted lint: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `249 passed in 11.50s`.
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
- The failure table intentionally omits passed checks. Full pass/fail evidence
  remains in the acceptance-audit JSON.
- Evidence is flattened into a compact string for HTML readability; complex
  nested evidence should still be inspected in the JSON artifact.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The next useful direction is to improve report navigation for large frame
tables, since report content is now richer and the input frame inventory can be
large on real datasets.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned acceptance-audit JSON produced from GLASS
artifacts and user-generated reference/timing outputs. No external
implementation source was read or used.
