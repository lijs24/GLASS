# S2-Gate 37 Status: Report Navigation Anchors

## Gate

S2-Gate 37 adds stable navigation anchors to the main HTML report. The report
has grown into a real audit surface, so this gate makes large benchmark reports
easier to inspect without changing artifact schemas or image math.

## Completed Content

- Added a static `Report navigation` table of contents near the top of the
  report.
- Added stable `id` attributes to every major report section.
- Added lightweight per-section anchor links for shareable diagnostics.
- Covered timing, benchmark comparison, resident output maps, acceptance
  failures, and the other report sections already present in the HTML.
- Added CLI smoke assertions for:
  - the report navigation container
  - section anchor links
  - benchmark comparison anchors
  - resident output-map anchors
  - acceptance-failure anchors
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_37_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_37_report.html`
- Report size: `297458` bytes.
- Verified anchors and report content:
  - `Report navigation`: present once
  - `href="#benchmark-comparison"`: present
  - `id="benchmark-comparison"`: present
  - `href="#resident-output-maps"`: present
  - `id="resident-output-maps"`: present
  - `href="#runtime-summary"`: present
  - `id="runtime-summary"`: present
  - benchmark speedup `34.3178020369665`: present
  - acceptance status `passed`: present

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

- Targeted report tests: `2 passed in 0.13s`.
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

- This gate is report-only and does not change CUDA execution, science
  calculations, compare metrics, or artifact schemas.
- Navigation is static HTML only; collapsible sections, table pagination, and
  client-side report search remain future report usability work.
- Anchors point to current major report sections. Any future section rename
  should preserve or intentionally migrate the stable id.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The next useful direction is richer report usability for large tables, such as
pagination or summary-first frame tables, while keeping the static artifact
auditable.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned report sections and GLASS artifact JSON
only. No external implementation source was read or used.
