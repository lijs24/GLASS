# S2-Gate 23 Status: Geometric Warp Coverage Reporting

## Gate

S2-Gate 23: Geometric warp coverage reporting.

## Completed Content

- Added a first-class `Geometric warp coverage` section to the HTML report.
- The new table surfaces resident and integration artifact coverage signals
  without requiring nested JSON inspection.
- Reported fields include:
  - active frame count
  - geometric coverage frame count
  - frame-count match status
  - warped/full-frame counts from resident artifacts
  - coverage min/max/mean
  - geometric zero/partial/full pixel counts
  - DQ `WARP_EDGE` and `NO_DATA` counts
  - partial-edge inference mode
  - native source string when available
- Older runs without the S2-Gate 22 schema remain reportable and show `No rows`.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests/test_pipeline_fixture.py::test_pipeline_fixture_audit`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\glass.exe report --run C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531 --out C:\\glass_runs\\phase2_s2_gate_22_200\\resident_geometric_warp_coverage_20260531\\s2_gate_23_report.html`
- HTML token check for:
  - `Geometric warp coverage`
  - `available_from_geometric_warp_coverage`
  - `5396832`
  - `ResidentCalibratedStack warp coverage accumulator`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`

## Test Results

- Focused report/pipeline tests: `2 passed in 0.35s`
- Ruff: `All checks passed`
- Full pytest: `239 passed in 11.34s`
- Real 200-light report regeneration: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Artifact

- Source run reused from S2-Gate 22:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531`
- New HTML report:
  `C:\glass_runs\phase2_s2_gate_22_200\resident_geometric_warp_coverage_20260531\s2_gate_23_report.html`

## Real-Data Report Evidence

The regenerated HTML report contains:

- `Geometric warp coverage`
- `available_from_geometric_warp_coverage`
- `5396832`
- `ResidentCalibratedStack warp coverage accumulator`

This confirms the report exposes the S2-Gate 22 geometric coverage signal for
the accepted 200-light run.

## Performance Or Numerical Regression Note

This is a reporting-only gate. No compute path, master-light output, DQ map, or
resident CUDA kernel changed. The full test suite stayed green, and the latest
200-light run was not rerun because the accepted S2-Gate 22 compute artifacts
were reused only for HTML regeneration.

## Known Limitations

- The report is still static HTML and displays table values rather than plots.
- The geometric coverage map itself is summarized but not visualized as an
  image preview.
- External comparison reports remain separate HTML files and are not yet
  embedded into the main run report.

## Next Step

Proceed to a compute-facing gate: either reduce the S2-Gate 22 coverage
accumulation overhead, or start moving resident DQ/mask semantics closer to the
formal StackEngine/DQ contract for calibration and local normalization.

## Clean-Room Compliance

Compliant. This gate consumed GLASS-owned JSON artifacts and regenerated a
GLASS HTML report. No proprietary source code was read, copied, summarized, or
reworked.
