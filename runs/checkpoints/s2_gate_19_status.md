# S2-Gate 19 Status: Resident Output Policy Reporting

## Gate

S2-Gate 19: Resident output policy reporting.

## Completed Content

- Added an HTML report section for output-map policy decisions.
- Report now surfaces policy mode, available maps, written maps, and skipped
  maps from both `integration_results.json` and `resident_artifacts.json`.
- Kept report behavior compatible with runs that have no resident output policy.
- Added CLI report smoke coverage for resident policy rows.
- Updated Phase 2 plan and algorithm source tracking.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cli_smoke.py tests\\test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cuda_import.py tests\\test_cuda_device_info.py tests\\test_cuda_smoke.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\glass.exe report --run C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531 --out C:\\glass_runs\\phase2_s2_gate_18_200\\resident_science_maps_20260531\\s2_gate_19_resident_policy_report.html`

## Test Results

- Focused report/pipeline tests: `22 passed in 16.74s`
- Ruff: `All checks passed`
- Full pytest: `235 passed in 14.61s`
- CUDA targeted sanity tests: `39 passed in 1.45s`
- Real resident report generation: passed

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Artifact

- Source run:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531`
- Generated report:
  `C:\glass_runs\phase2_s2_gate_18_200\resident_science_maps_20260531\s2_gate_19_resident_policy_report.html`

The generated report contains:

- `Output map policy`
- `science`
- `master, weight, dq, coverage`
- `low_rejection, high_rejection`

## Performance Or Numerical Regression Note

This gate changes reporting only. It does not alter calibration, registration,
warp, local normalization, integration, rejection, output map writing, or CUDA
execution. The S2-Gate 18 200-light benchmark remains the current performance
and numerical baseline.

## Known Limitations

- The report renders map lists as comma-separated text; richer collapsible
  artifact panels remain future work.
- The report does not yet embed the compare/acceptance-audit JSON panels.

## Next Step

Continue Phase 2 with deeper DQ propagation and StackEngine parity work:
resident CUDA should start carrying calibration and warp-edge DQ semantics, and
master-frame/light integration paths should continue converging on the shared
StackEngine contract.

## Clean-Room Constraint

Compliant. The report displays GLASS-owned JSON artifacts and does not rely on
or encode proprietary implementation behavior.
