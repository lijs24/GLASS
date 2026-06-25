# S2-Gate 669 Status: StackEngine Streaming Integration Sink

## Gate

- Gate: S2-Gate 669
- Status: green checkpoint
- Scope: CPU/tile StackEngine integration output memory model
- Branch: `main`

## Completed Work

- Changed the default CPU/tile integration StackEngine path from full-frame
  `StackEngineResult` serialization to a streaming FITS tile sink.
- Added tile-local `_WindowedCoverageImageSource` wrappers so each global
  output tile can be processed by the existing `CPUStackEngine` science logic
  without materializing the full output result arrays in the integration sink.
- Added `stack_engine_streaming_result_contract`, compatible with the existing
  `stack_engine_result_contract`, to validate per-tile contracts, requested
  map streaming, output shape coverage, and sample-accounting closure.
- Integration artifacts now record:
  - `execution_path=stack_engine_streaming_tile_sink`
  - `full_output_arrays_materialized=false`
  - `streaming_tile_contract_count`
  - `streaming_tile_contract_failed_count`
- Added regression tests for the streaming sink default path and for disabled
  optional variance maps.
- Updated Phase 2, integration model, validation, known limitations, and
  algorithm-source documentation.

## Commands Run

- Syntax check:
  `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\integration.py`
- Focused integration tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_integration_auto_keeps_stack_engine_default_when_cuda_is_available tests\test_pipeline_fixture.py::test_integration_cuda_backend_keeps_stack_engine_default_without_policy tests\test_pipeline_fixture.py::test_stack_engine_streaming_sink_accepts_disabled_variance_map tests\test_pipeline_fixture.py::test_pipeline_fixture_audit`
- StackEngine contract tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine_contract.py`
- Combined focused fixture/contract tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py tests\test_stack_engine_contract.py`
- Ruff:
  `.\.venv\Scripts\ruff.exe check src\glass\engine\integration.py tests\test_pipeline_fixture.py`
- Diff check:
  `git diff --check`
- CUDA device probe:
  `.\.venv\Scripts\python.exe -c "import glass_cuda; print('cuda_available', glass_cuda.cuda_available()); print(glass_cuda.list_devices())"`
- Real 200-light resident guard:
  `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --out C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\resident_default_guard`
- Real 200-light regression versus Gate668:
  `.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted --candidate-run C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\resident_default_guard --out C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\gate669_vs_gate668_regression.json --markdown C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\gate669_vs_gate668_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Full test suite:
  `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Syntax check: passed.
- Focused integration tests: `4 passed in 0.80 s`.
- StackEngine contract tests: `17 passed in 0.95 s`.
- Combined fixture/contract tests: `40 passed in 7.28 s`.
- Ruff: passed.
- `git diff --check`: passed; only Windows line-ending warnings were printed.
- Full pytest: `1410 passed in 62.32 s`.

## Synthetic Validation

- `test_pipeline_fixture_audit` generated a synthetic FITS dataset and ran the
  CPU audit pipeline through integration and report generation.
- The integration output recorded:
  - `execution_path=stack_engine_streaming_tile_sink`
  - `full_output_arrays_materialized=false`
  - `streaming_tile_contract_failed_count=0`
  - `result_contract.contract_type=stack_engine_streaming_result_contract`
  - `result_contract.passed=true`
- The disabled-variance-map test verified that `requested_maps.variance=false`
  is not treated as a missing requested output.

## Real 200-Light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\resident_default_guard`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\gate669_vs_gate668_regression.json`
- Regression status: passed.
- Failed checks: `[]`.
- Total elapsed:
  - Gate668 baseline: `11.097266299999319 s`
  - Gate669 candidate: `11.61158230016008 s`
  - elapsed ratio: `1.046346188895259`
- Determinism summary:
  - artifact differences: `0`
  - frame-accounting differences: `0`
  - frame-signature differences: `0`
  - registration differences: `0`
  - output differences: `0`
  - output numerical drift: `0`
- Component timing in candidate:
  - light read/upload/calibrate: `3.3856848999857903 s`
  - registration/warp: `0.2651259994599968 s`
  - local normalization: `0.34654980001505464 s`
  - resident integration: `3.2716861999360844 s`
  - output write: `0.2615312000270933 s`
- Interpretation: this gate did not change resident CUDA code; the real guard
  confirms the high-VRAM mainline still runs and preserves outputs. The
  observed total-time increase is inside the 15 percent gate budget and is
  attributable to normal read/upload/calibration timing variation. Resident
  integration itself was effectively unchanged with ratio `1.0003156861106162`.

## CUDA

- CUDA available: yes.
- Native backend: available.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- SM count: `188`.
- Driver: `596.21`.

## Known Limitations

- This removes full-frame materialization from the outer integration sink only.
- Direct `CPUStackEngine.stack(...)` API calls still return in-memory result
  arrays by design.
- Some calibration/master-frame StackEngine surfaces can still materialize full
  arrays and should receive sink-oriented APIs in later gates.
- This is not a resident CUDA hot-path speedup; resident registration/warp,
  I/O/upload/calibration overlap, and the hardened reducer remain the largest
  performance targets.

## Next Step

- Return to a substantive Phase 2 mainline performance target:
  resident registration/warp orchestration, I/O/upload/calibration overlap, or
  a redesigned scalable CUDA order-statistic reducer.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned StackEngine code, GLASS DQ contracts,
GLASS FITS tile writers, GLASS tests, synthetic fixtures, and user-owned real
benchmark artifacts. It did not inspect, copy, summarize, or rework external
proprietary implementation source, and it did not modify input directories.
