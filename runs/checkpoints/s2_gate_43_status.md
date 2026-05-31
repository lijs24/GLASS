# S2 Gate 43 Status: Rejected-Frame Focused Accounting

## Gate

S2-Gate 43: Rejected-Frame Focused Accounting

## Completed Content

- Extended `frame_accounting.json` with a compact rejected/zero-weight frame
  diagnostic surface:
  - top-level `exception_summary`
  - top-level `exception_frames`
  - `summary.exception_frames`
- Each exception frame records:
  - frame id and filter
  - final status
  - primary stage and primary reason
  - stage statuses
  - integration weight
  - reason and warning counts
  - input path when available
- Zero-weight frames now get a clear integration-stage primary reason:
  `integration weight is zero`.
- Added an HTML report section, `Rejected/zero-weight frames`, with summary
  counts and a compact per-frame table.
- Acceptance-audit JSON and Markdown now include exception summary and the
  first rejected/zero-weight frame details.
- Updated Phase 2 planning and source documentation for this gate.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\frame_accounting.py src\\glass\\report\\html_report.py src\\glass\\report\\acceptance_audit.py src\\glass\\report\\benchmark_contract.py tests\\test_frame_accounting.py tests\\test_acceptance_audit.py tests\\test_pipeline_fixture.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_frame_accounting.py tests\\test_acceptance_audit.py tests\\test_pipeline_fixture.py::test_pipeline_fixture_run_integration tests\\test_pipeline_fixture.py::test_pipeline_fixture_audit`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -c "from pathlib import Path; from glass.engine.frame_accounting import build_frame_accounting; p=Path(r'C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531'); a=build_frame_accounting(p); print(a['exception_summary']); print(a['exception_frames'][:3])"`
- `.\\.venv\\Scripts\\glass.exe report --run "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531" --out "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\s2_gate_43_report.html"`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\s2_gate_32_compare.json" --benchmark-contract benchmarks\\phase2_m38_h_200_audit_maps_contract.json --out "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_43.json" --markdown "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_43.md"`
- `.\\.venv\\Scripts\\python.exe -c "from glass.io.json_io import read_json; p=r'C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\frame_accounting.json'; a=read_json(p); print(a.get('exception_summary')); print([x.get('frame_id') for x in a.get('exception_frames', [])])"`
- `.\\.venv\\Scripts\\python.exe -c "from glass.capabilities import capability_report; import json; print(json.dumps(capability_report(), indent=2))"`
- `.\\.venv\\Scripts\\python.exe -c "import glass_cuda, json; print(json.dumps(glass_cuda.get_device_info(0), indent=2))"`

## Test Results

- Focused tests: `14 passed in 1.53s`
- Full pytest: `257 passed in 11.94s`
- Ruff: all checks passed

## CUDA Availability

- CUDA extension importable: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native resident stack available: yes

## Real Artifact Validation

- Real GLASS run directory:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531`
- Regenerated report:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_43_report.html`
- Regenerated acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_43.json`
- Regenerated acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_43.md`
- Acceptance audit status: passed
- Speedup vs external reference: `34.3178020369665`
- Real exception summary:
  - count: 7
  - final status counts: `zero_weight=7`
  - primary stage counts: `integration=7`
- Real exception frame ids:
  `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`
- Verified HTML report and Markdown include the rejected/zero-weight frame
  section and the primary reason `integration weight is zero`.

## Known Limitations

- This gate is diagnostic/reporting only and does not change image math,
  rejection behavior, or runtime scheduling.
- The primary reason is intentionally compact; future gates may add richer
  multi-reason ranking or direct links to registration/quality thumbnails.
- Older run directories without the new exception fields still rely on
  regenerating `frame_accounting.json` from available stage artifacts.

## Next Step

S2-Gate 44 should start turning the rejected-frame diagnostics into a direct
optimization guide: connect exception reasons to per-stage timings and identify
whether the next major speed gain should target I/O/upload/calibration overlap
or resident registration/warp batching.

## Clean-Room Compliance

Compliant. The gate uses GLASS-owned diagnostics and user-generated benchmark
outputs only. No official PixInsight/WBPP/PJSR source code was read, copied, or
summarized.
