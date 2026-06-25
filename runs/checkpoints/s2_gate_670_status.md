# S2-Gate 670 Status: StackEngine Streaming Master Calibration Sink

## Gate

- Gate: S2-Gate 670
- Status: green checkpoint
- Scope: CPU/tile StackEngine master calibration output memory model
- Branch: `main`

## Completed Work

- Changed CPU/tile bias, dark, and per-flat normalized flat master construction
  from full-frame `StackEngineResult` serialization to a streaming FITS tile
  sink.
- Added `_WindowedImageSource` so each output master tile can be presented to
  the existing `CPUStackEngine` as a tile-local source set.
- `_stack_mean_master_with_engine` now streams each bias/dark/raw master tile,
  applies optional post-stack subtraction tile-by-tile, writes the tile, and
  discards the tile result.
- `_stack_normalized_flat_master` now streams each normalized flat master tile,
  applies `flat_floor` tile-by-tile, writes the tile, and discards the tile
  result.
- Added `stack_engine_master_streaming_result_contract`, compatible with the
  existing StackEngine result contract, to validate per-tile contracts, written
  master finiteness, output-shape coverage, and sample-accounting closure.
- Calibration master artifacts now record:
  - `execution_path=stack_engine_master_streaming_tile_sink`
  - `full_output_arrays_materialized=false`
  - `streaming_tile_contract_count`
  - `streaming_tile_contract_failed_count`
- Updated Phase 2, calibration model, validation, known limitations, and
  algorithm-source documentation.

## Commands Run

- Syntax check:
  `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\pipeline.py`
- Focused master/calibration tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_stack_engine_master_matches_legacy_streaming tests\test_pipeline_fixture.py::test_stack_engine_master_rejection_removes_extreme_samples tests\test_pipeline_fixture.py::test_pipeline_fixture_run_calibration tests\test_stack_engine_contract.py::test_stack_engine_contract_passes_for_cpu_audit_run`
- Ruff:
  `.\.venv\Scripts\ruff.exe check src\glass\engine\pipeline.py tests\test_pipeline_fixture.py`
- Combined fixture/contract tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py tests\test_stack_engine_contract.py`
- Diff check:
  `git diff --check`
- Synthetic dataset:
  `.\.venv\Scripts\python.exe -m glass.cli synthetic --out C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_data --frames 4 --width 32 --height 32 --filter H --known-shift`
- Synthetic scan:
  `.\.venv\Scripts\python.exe -m glass.cli scan --root C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_data --out C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_audit\manifest.json`
- Synthetic plan:
  `.\.venv\Scripts\python.exe -m glass.cli plan --manifest C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_audit\manifest.json --out C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_audit\processing_plan.json`
- Synthetic CPU calibration:
  `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_audit\processing_plan.json --out C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_cpu_calibration --backend cpu --until-stage calibration --tile-size 9 --flat-floor 0.05`
- Calibration StackEngine contract:
  `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_cpu_calibration --out C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_stack_engine_contract.md --scope calibration`
- Real 200-light resident guard:
  `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --out C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\resident_default_guard`
- Real 200-light regression versus Gate669:
  `.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\resident_default_guard --candidate-run C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\resident_default_guard --out C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\gate670_vs_gate669_regression.json --markdown C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\gate670_vs_gate669_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Full test suite:
  `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Syntax check: passed.
- Focused master/calibration tests: `4 passed in 0.80 s`.
- Ruff: passed.
- Combined fixture/contract tests: `40 passed in 7.40 s`.
- `git diff --check`: passed; only Windows line-ending warnings were printed.
- Full pytest: `1410 passed in 62.66 s`.

## Synthetic Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000`
- Synthetic scan: 13 frames:
  - bias: `3`
  - dark: `3`
  - flat: `3`
  - light: `4`
- Synthetic CPU calibration run:
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_cpu_calibration`
- Master count: `3`.
- Each master recorded:
  - `execution_path=stack_engine_master_streaming_tile_sink`
  - `full_output_arrays_materialized=false`
  - `streaming_tile_contract_count=16`
  - `streaming_tile_contract_failed_count=0`
  - `result_contract.contract_type=stack_engine_master_streaming_result_contract`
  - `result_contract.passed=true`
- Calibration-only StackEngine contract:
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_stack_engine_contract.json`
- Contract status: passed.
- `strict_native_stack_engine_ready=true`.

## Real 200-Light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\resident_default_guard`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\resident_default_guard`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\gate670_vs_gate669_regression.json`
- Regression status: passed.
- Failed checks: `[]`.
- Total elapsed:
  - Gate669 baseline: `11.61158230016008 s`
  - Gate670 candidate: `11.706245199893601 s`
  - elapsed ratio: `1.0081524547892338`
- Determinism summary:
  - artifact differences: `0`
  - frame-accounting differences: `0`
  - frame-signature differences: `0`
  - registration differences: `0`
  - output differences: `0`
  - output numerical drift: `0`
- Component timing in candidate:
  - light read/upload/calibrate: `3.320315600023605 s`
  - registration/warp: `0.2691957000643015 s`
  - local normalization: `0.37488160002976656 s`
  - resident integration: `3.2789314999245107 s`
  - output write: `0.2674127999925986 s`
- Interpretation: this gate changes CPU/tile master calibration. The real
  resident guard confirms the high-VRAM mainline still runs and preserves
  outputs; the `0.8%` elapsed change is inside normal run variance and the
  gate budget.

## CUDA

- CUDA available: yes.
- Native backend: available.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- This removes full-frame materialization from the outer CPU/tile master
  calibration sink only.
- Direct `CPUStackEngine.stack(...)` API calls intentionally still return
  in-memory result arrays.
- Resident CUDA master-cache construction is a separate high-VRAM path and is
  unchanged by this gate.
- The next major performance targets remain resident I/O/upload/calibration
  overlap and the hardened winsorized reducer.

## Next Step

- Return to a substantive Phase 2 mainline performance target:
  resident I/O/upload/calibration overlap, resident registration/warp
  orchestration, or a redesigned scalable CUDA order-statistic reducer.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned StackEngine code, GLASS calibration
policy, GLASS DQ contracts, GLASS FITS tile writers, GLASS tests, synthetic
fixtures, and user-owned real benchmark artifacts. It did not inspect, copy,
summarize, or rework external proprietary implementation source, and it did
not modify input directories.
