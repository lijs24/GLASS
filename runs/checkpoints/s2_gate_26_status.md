# S2-Gate 26 Status: StackEngine DQ Provenance Artifacts

## Gate

S2-Gate 26: StackEngine DQ provenance artifacts and report bridge.

## Completed Content

- Wrote StackEngine DQ provenance into CPU integration outputs as
  `stack_engine_dq_provenance`.
- Wrote StackEngine DQ provenance into master calibration artifacts when bias,
  dark, and flat masters use CPU StackEngine.
- Preserved the existing `stack_engine_metrics` field and embedded a copy of
  `dq_provenance` there for internal traceability.
- Added a first-class `StackEngine DQ provenance` table to the HTML report.
- The report table covers master calibration and CPU integration StackEngine
  paths and surfaces:
  - input sample counts
  - source DQ flagged sample counts
  - non-finite sample counts
  - zero-coverage pixel counts
  - low/high rejected pixel counts
  - selected source DQ flag counts
  - output DQ summaries
- Kept resident CUDA DQ provenance on its existing resident artifact schema.
- Updated Phase 2 gate planning and algorithm source tracking.

## Commands Run

- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine.py tests/test_pipeline_fixture.py::test_pipeline_fixture_audit tests/test_pipeline_fixture.py::test_pipeline_fixture_run_calibration tests/test_pipeline_fixture.py::test_pipeline_fixture_run_integration tests/test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results

- Ruff: `All checks passed`
- Focused StackEngine/pipeline/report tests: `13 passed in 1.65s`
- Full pytest: `240 passed in 11.53s`

## CUDA Availability

CUDA is available, but this gate did not change or exercise the resident CUDA
fast path.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver version: 596.21
- Native backend: available

## Real-Data Benchmark

The 200-light benchmark was not rerun for this gate.

Reason: S2-Gate 26 changes CPU StackEngine artifact/report plumbing only. It
does not change resident CUDA kernels, resident pipeline routing, default
200-light benchmark options, FITS/XISF readers, calibration math, registration,
warp, integration math, or resident output artifacts.

The latest preserved real-data benchmark remains S2-Gate 24:

- Run directory:
  `C:\glass_runs\phase2_s2_gate_24_200\resident_fused_warp_coverage_20260531`
- Runtime: `30.949304700363427 s`
- Speedup vs reference: `35.30098690673237x`
- RMS difference: `0.001558294284488301`
- P99 absolute difference: `0.00043095467146486016`
- Acceptance audit: passed

## Performance Or Numerical Regression Note

No resident CUDA, default pipeline routing, or image math path changed. This
gate copies already-computed StackEngine DQ provenance into JSON artifacts and
renders it in HTML. Focused tests and full pytest passed.

## Known Limitations

- The new report table is a compact audit table, not a graphical DQ map view.
- Resident CUDA DQ provenance still uses its resident schema; full schema
  unification remains a later gate.
- Source DQ flags are counted for StackEngine audit but are not yet projected
  as persistent source-flag output pixels.
- The default 200-light resident path is not StackEngine-backed yet.

## Next Step

Continue unifying DQ provenance schemas between CPU StackEngine and resident
CUDA, then move toward making StackEngine the default master/light contract
while preserving the resident CUDA fast path and 200-light benchmark.

## Clean-Room Compliance

Compliant. This gate only connects GLASS-owned StackEngine DQ accounting to
GLASS-owned artifacts and HTML report rendering. No proprietary source code was
read, copied, summarized, or reworked.
