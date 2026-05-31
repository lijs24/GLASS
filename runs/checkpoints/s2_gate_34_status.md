# S2-Gate 34 Status: Report Noise Reduction With Focused Summaries

## Gate

S2-Gate 34 reduces HTML report noise by replacing broad nested integration and
DQ table cells with focused summary tables. Detailed artifacts remain on disk
as JSON; the report now presents the high-signal fields directly.

## Completed Content

- Replaced the raw `integration_outputs` table in `Integration summary` with a
  compact integration-output summary containing:
  - source stage
  - backend
  - memory mode
  - frame count and active frame count
  - weighting and rejection modes
  - master path
  - StackEngine flag
  - resident integration time
  - estimated peak GiB
- Added an `Output diagnostics` table that flattens integration and resident
  diagnostics into range, finite-pixel, clipping, and normalization-probe
  columns.
- Replaced the `DQ/mask summary` nested provenance cell with compact columns
  for DQ flags, source terms, active frame count, and coverage inference.
- Renamed geometric coverage report columns to expose
  `geometric_zero_pixels`, `geometric_partial_pixels`, and
  `geometric_full_pixels` directly.
- Updated the resident report smoke test to assert that nested keys such as
  `output_diagnostics` and `clipping_probe` no longer appear in the HTML.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_34_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_34_report.html`
- Gate 33 report size: `296024` bytes.
- Gate 34 report size: `289787` bytes.
- The regenerated report contains:
  - `Output diagnostics`
  - `normalization_scale`
  - `gt_65535_count`
  - `Resident output maps`
  - `geometric_partial_pixels`
- The regenerated report does not contain raw nested keys:
  - `output_diagnostics`
  - `clipping_probe`

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_audit tests\test_pipeline_fixture.py::test_pipeline_fixture_run_integration`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\html_report.py tests\test_cli_smoke.py`
- real-data report regeneration command above
- `Select-String` verification against the regenerated report
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`

## Test Results

- Targeted resident report test: `1 passed in 0.11s`.
- Targeted pipeline report tests: `2 passed in 1.50s`.
- Targeted lint: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `248 passed in 11.61s`.
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
- The report still includes full input frame tables and may remain large for
  hundreds of frames; this gate targets nested artifact-cell noise rather than
  input inventory pagination.
- `resident_dq_coverage_provenance` still appears as a source schema value,
  which is intentional and not a nested artifact dump.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The next useful report/audit step is to add an explicit benchmark comparison
section that pulls speedup, RMS, P99, coverage fraction, and acceptance-audit
status into the main report when compare/audit JSON artifacts are present.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned artifact JSON and output files only. No
external implementation source was read or used.
