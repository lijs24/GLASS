# S2-Gate 27 Status: Unified DQ Provenance Summary Contract

## Gate

S2-Gate 27: Unified DQ provenance summary contract.

## Completed Content

- Added a compact `dq_provenance_summary` bridge schema for report and audit
  consumers.
- Added helper builders for:
  - CPU StackEngine provenance:
    `dq_provenance_summary_from_stack_engine`
  - resident CUDA provenance:
    `dq_provenance_summary_from_resident`
- Kept detailed source schemas intact:
  - `stack_engine_dq_provenance`
  - `dq_coverage_provenance`
- CPU master calibration artifacts now include `dq_provenance_summary` when
  StackEngine is used.
- CPU integration outputs now include `dq_provenance_summary` when StackEngine
  is used.
- Resident CUDA artifacts and resident integration outputs now include
  `dq_provenance_summary`.
- HTML reports now include a `DQ provenance contract` table that can show both
  StackEngine and resident CUDA summary rows.
- Added direct helper tests and extended pipeline/report/resident CUDA tests.
- Updated Phase 2 gate planning and algorithm source tracking.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q tests/test_dq_provenance.py tests/test_pipeline_fixture.py::test_pipeline_fixture_audit tests/test_pipeline_fixture.py::test_pipeline_fixture_run_calibration tests/test_pipeline_fixture.py::test_pipeline_fixture_run_integration tests/test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests/test_resident_cuda_run.py::test_cli_resident_cuda_science_output_maps_skip_rejection_count_files`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results

- Ruff: `All checks passed`
- Focused DQ/pipeline/report/resident CUDA tests: `7 passed in 2.80s`
- Full pytest: `242 passed in 18.94s`

## CUDA Availability

CUDA is available. A small resident CUDA smoke test was included in the focused
test set.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Benchmark

The 200-light benchmark was not rerun for this gate.

Reason: S2-Gate 27 changes DQ provenance JSON/report contracts and helper
normalization only. It does not change resident CUDA kernels, image math,
registration/warp algorithms, FITS/XISF readers, default 200-light benchmark
options, or benchmark routing. A focused resident CUDA smoke test verified the
new resident artifact field on a small synthetic dataset.

The latest preserved real-data benchmark remains S2-Gate 24:

- Run directory:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531`
- Runtime: `30.949304700363427 s`
- Speedup vs reference: `35.30098690673237x`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Acceptance audit: passed

## Performance Or Numerical Regression Note

No image math path changed. The new summary is derived from already-computed
StackEngine or resident DQ provenance artifacts. Focused tests, a resident CUDA
smoke test, ruff, and full pytest passed.

## Known Limitations

- The compact summary is a bridge, not a replacement for detailed
  `stack_engine_dq_provenance` or resident `dq_coverage_provenance`.
- Some summary fields are `null` when a source schema cannot provide them.
- Source DQ flags are still counted for StackEngine audit but are not projected
  as persistent output source-flag pixels.
- The 200-light resident path is still not StackEngine-backed.

## Next Step

Use the shared `dq_provenance_summary` as the report/audit contract while
continuing toward deeper DQ schema unification and StackEngine-backed default
master/light execution.

## Clean-Room Compliance

Compliant. This gate normalizes GLASS-owned DQ artifact fields and report
rendering. No proprietary source code was read, copied, summarized, or
reworked.
