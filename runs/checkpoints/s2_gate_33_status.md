# S2-Gate 33 Status: Resident Output Map Report Provenance

## Gate

S2-Gate 33 surfaces resident CUDA output-map provenance in the HTML report.
Gate 32 made `resident_artifacts.json` self-contained; this gate makes those
paths and storage details visible to humans without opening the JSON files.

## Completed Content

- Added a `Resident output maps` HTML report section.
- Each resident output-map row records:
  - filter
  - map name
  - output-map policy status
  - artifact path
  - path existence at report-generation time
  - storage dtype
  - estimated payload MiB
  - per-map write seconds when available
- Report generation now passes the run directory to the HTML writer so relative
  artifact paths can be resolved safely.
- Updated the resident report CLI smoke test with real placeholder artifact
  paths, storage records, and write timings.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Real-Data Report Regeneration

Command:

```powershell
.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531 --out C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_33_report.html
```

Result:

- Report path:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_33_report.html`
- Report size: `296024` bytes.
- The report contains `Resident output maps`.
- The real 200-light resident maps show `exists=True` for:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`
  - `resident_dq_map_H.fits`
- Storage is visible as `float32` for master/weight and `int16` for count/DQ
  maps.
- Estimated payload sizes are visible as `235.181 MiB` for float32 master/weight
  maps and `117.59 MiB` for int16 maps.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- `.venv\Scripts\python.exe -m ruff check src\glass\report\html_report.py src\glass\cli.py tests\test_cli_smoke.py`
- real-data report regeneration command above
- `Select-String` verification against the regenerated report
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- CUDA device probe
- `git diff --check`

## Test Results

- Targeted report test: `1 passed in 0.12s`.
- Targeted lint: `All checks passed!`.
- Full lint: `All checks passed!`.
- Full pytest: `248 passed in 11.67s`.
- `git diff --check`: no whitespace errors.

## CUDA

CUDA is available.

- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver: `596.21`
- Native backend: `true`

## Known Limitations

- This gate is report-only and does not change resident CUDA image math,
  registration, rejection, or output pixels.
- Path existence is a static report-generation snapshot. If files are moved or
  deleted after the report is written, the report will not update itself.
- The report still includes large nested JSON tables for some integration and
  resident records; a later report polish gate should split those into smaller
  purpose-built tables.

## Next Step

Proceed to the next Phase 2 gate in `docs/phase2_algorithm_hardening.md`.
The most useful follow-up is to reduce report noise by replacing broad nested
artifact dumps with focused summary tables now that resident map provenance has
its own report section.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned artifact JSON and output files only. No
external implementation source was read or used.
