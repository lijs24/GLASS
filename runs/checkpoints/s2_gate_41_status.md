# S2 Gate 41 Status: Shared Accepted-Frame Accounting Summary

## Gate

S2-Gate 41: Shared Accepted-Frame Accounting Summary

## Completed Content

- Added `src/glass/engine/frame_accounting.py` to build `frame_accounting.json`
  from processing-plan, calibration, quality, registration, warp, local
  normalization, resident, and integration artifacts.
- Integrated accounting generation after tiled integration and resident CUDA
  integration.
- Added a compact HTML report section with frame-accounting summary and a
  per-light table that keeps verbose warnings in the JSON artifact.
- Added direct accounting tests for tiled and resident artifact shapes.
- Extended pipeline fixture tests to require the new artifact after integration.
- Updated Phase 2 gate planning and algorithm-source documentation.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\frame_accounting.py src\\glass\\engine\\integration.py src\\glass\\engine\\resident_cuda.py src\\glass\\report\\html_report.py src\\glass\\cli.py tests\\test_frame_accounting.py tests\\test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_frame_accounting.py tests\\test_pipeline_fixture.py::test_pipeline_fixture_audit tests\\test_pipeline_fixture.py::test_pipeline_fixture_run_integration`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -c "from pathlib import Path; from glass.engine.frame_accounting import build_frame_accounting; p=Path(r'C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531'); a=build_frame_accounting(p); print(a['summary'])"`
- `.\\.venv\\Scripts\\glass.exe report --run "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531" --out "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\s2_gate_41_report.html"`
- `.\\.venv\\Scripts\\python.exe -c "from glass.capabilities import capability_report; import json; print(json.dumps(capability_report(), indent=2))"`
- `.\\.venv\\Scripts\\python.exe -c "import glass_cuda, json; print(json.dumps(glass_cuda.get_device_info(0), indent=2))"`

## Test Results

- Focused pytest: `5 passed in 1.25s`
- Full pytest: `255 passed in 11.81s`
- Ruff: all checks passed

## CUDA Availability

- CUDA extension importable: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native resident stack available: yes

## Real Artifact Validation

- Rebuilt accounting for
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531`.
- Real 200-light accounting summary:
  - input lights: 200
  - resident-calibrated frames: 200
  - registration accepted frames: 193
  - integrated frames: 193
  - zero-weight frames: 7
- Regenerated report:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_41_report.html`
- Generated/updated accounting artifact:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\frame_accounting.json`

## Known Limitations

- The artifact is diagnostic-only and does not alter image math.
- Resident local-normalization artifacts are still group-level; frame accounting
  summarizes resident LN as enabled/disabled rather than carrying per-frame LN
  coefficients.
- HTML report intentionally keeps only compact per-frame accounting fields;
  full reasons and warnings remain in `frame_accounting.json`.

## Next Step

S2-Gate 42 should tighten resident accepted-frame parity checks: make benchmark
acceptance explicitly compare `frame_accounting.json` counts with integration
weights, resident registration rows, and output-map provenance.

## Clean-Room Compliance

Compliant. This gate derives only from GLASS-owned artifacts and project
requirements. No official PixInsight/WBPP/PJSR source code was read, copied, or
summarized.
