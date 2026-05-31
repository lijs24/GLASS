# S2-Gate 38 Status: Large Report Table Limits

## Gate

S2-Gate 38 adds static preview limits for high-cardinality HTML report tables.
The authoritative JSON/FITS artifacts remain complete; the HTML report now
stays easier to open and inspect on large runs.

## Completed Content

- Added a shared report table preview helper with a default limit of `200`
  rows.
- Applied preview limits to:
  - input frames
  - light plans
  - frame quality rows
  - registration rows
  - local normalization rows
  - timing rows
- Added a visible note when a table is limited:
  - displayed row count
  - total row count
  - authoritative artifact path
- Added CLI smoke coverage that builds large manifest and quality fixtures and
  verifies:
  - only the first `200` rows are rendered
  - row `200` is omitted from the preview
  - the report points back to `manifest.json` and `frame_quality.json`
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_38_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_38_report.html`
- Report size: `242293` bytes.
- Verified report content:
  - `Report navigation`: present once
  - `Showing first 200 of 260 input frames`: present once
  - `Full details remain in <code>manifest.json</code>`: present once
  - benchmark speedup `34.3178020369665`: present
  - acceptance status `passed`: present

The real-data manifest has `260` total input frames because it includes
calibration frames plus the 200 selected light frames, so this run exercises the
input-frame preview limit without rerunning image processing.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_report_limits_large_audit_tables tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\html_report.py tests\test_cli_smoke.py`
- real-data report regeneration command above
- Python verification against the regenerated report
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`

## Test Results

- Targeted report tests: `2 passed in 0.15s`.
- Targeted lint: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `250 passed in 11.54s`.
- `git diff --check`: no whitespace errors.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Performance And Numerical Regression Note

This gate is report-only. It does not change scan, planning, calibration,
quality metrics, registration, warp, local normalization, integration,
comparison, acceptance audit, or any FITS/XISF artifacts. The 200-light report
was regenerated from existing artifacts; no numerical benchmark rerun was
required.

## Known Limitations

- The preview limit is static and always shows the first `200` rows.
- There is no client-side search, sorting, pagination, or downloadable table
  export from the HTML yet.
- JSON and FITS artifacts remain the authoritative complete data sources.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The next useful direction is to return from report usability to algorithm
hardening, especially quality/registration/LN details that affect frame
selection and final weights.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned report sections and GLASS artifact JSON
only. No external implementation source was read or used.
