# S2-Gate 671 Status: Master Calibration DQ Artifacts

## Gate

- Gate: S2-Gate 671
- Status: green checkpoint
- Scope: CPU/tile master calibration DQ artifact pipeline
- Branch: `main`

## Completed Work

- Added explicit master DQ FITS artifacts for CPU/tile StackEngine-built master
  bias, dark, and flat frames.
- `_stack_mean_master_with_engine` and `_stack_normalized_flat_master` now
  accept an optional `dq_path`. When present, the StackEngine tile requests
  include DQ, coverage, and low/high rejection maps.
- `run_calibration_stages` now writes:
  - `calib_cache/dq/dq_master_bias_<group>.fits`
  - `calib_cache/dq/dq_master_dark_<group>.fits`
  - `calib_cache/dq/dq_master_flat_<group>.fits`
- Master records in `calibration_artifacts.json` now include:
  - `dq_mask_path`
  - `dq_summary`
  - matching `stack_engine_metrics.master_dq_path`
  - matching `stack_engine_metrics.master_dq_summary`
  - matching `stack_engine_dq_provenance.output_dq_summary`
- `stack_engine_master_streaming_result_contract` now validates requested
  master DQ path existence and DQ-summary presence.
- Updated Phase 2, calibration model, validation, known limitations, and
  algorithm-source documentation.

## Commands Run

- Syntax check:
  `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\pipeline.py`
- Ruff:
  `.\.venv\Scripts\ruff.exe check src\glass\engine\pipeline.py tests\test_pipeline_fixture.py`
- Focused master/calibration tests:
  `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_stack_engine_master_matches_legacy_streaming tests\test_pipeline_fixture.py::test_stack_engine_master_rejection_removes_extreme_samples tests\test_pipeline_fixture.py::test_pipeline_fixture_run_calibration tests\test_stack_engine_contract.py::test_stack_engine_contract_passes_for_cpu_audit_run`
- Synthetic dataset:
  `.\.venv\Scripts\python.exe -m glass.cli synthetic --out C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_data --frames 4 --width 32 --height 32 --filter H --known-shift`
- Synthetic scan:
  `.\.venv\Scripts\python.exe -m glass.cli scan --root C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_data --out C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_audit\manifest.json`
- Synthetic plan:
  `.\.venv\Scripts\python.exe -m glass.cli plan --manifest C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_audit\manifest.json --out C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_audit\processing_plan.json`
- Synthetic CPU calibration:
  `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_audit\processing_plan.json --out C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_cpu_calibration --backend cpu --until-stage calibration --tile-size 9 --flat-floor 0.05`
- Calibration StackEngine contract:
  `.\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_cpu_calibration --out C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_stack_engine_contract.md --scope calibration`
- Real 200-light resident guard:
  `.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --out C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\resident_default_guard`
- Real 200-light regression versus Gate670:
  `.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\resident_default_guard --candidate-run C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\resident_default_guard --out C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\gate671_vs_gate670_regression.json --markdown C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\gate671_vs_gate670_regression.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Full test suite:
  `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Syntax check: passed.
- Ruff: passed.
- Focused master/calibration tests: `4 passed in 0.85 s`.
- Full pytest: `1410 passed in 63.10 s`.

## Synthetic Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000`
- Synthetic scan: 13 frames:
  - bias: `3`
  - dark: `3`
  - flat: `3`
  - light: `4`
- Synthetic CPU calibration run:
  `C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_cpu_calibration`
- Master count: `3`.
- Master DQ files: `3`.
- Calibrated-light DQ files: `4`.
- Each master recorded:
  - existing `dq_mask_path`
  - `dq_summary={"valid": 1024}`
  - `stack_engine_dq_provenance.output_dq_summary={"valid": 1024}`
  - `result_contract.contract_type=stack_engine_master_streaming_result_contract`
  - `result_contract.passed=true`
- Calibration-only StackEngine contract:
  `C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_stack_engine_contract.json`
- Contract status: passed.
- `strict_native_stack_engine_ready=true`.

## Real 200-Light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\resident_default_guard`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\resident_default_guard`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\gate671_vs_gate670_regression.json`
- Regression status: passed.
- Failed checks: `[]`.
- Total elapsed:
  - Gate670 baseline: `11.706245199893601 s`
  - Gate671 candidate: `11.097927200025879 s`
  - elapsed ratio: `0.9480347464554004`
- Determinism summary:
  - artifact differences: `0`
  - frame-accounting differences: `0`
  - frame-signature differences: `0`
  - registration differences: `0`
  - output differences: `0`
  - output numerical drift: `0`
- Component timing in candidate:
  - light read/upload/calibrate: `3.1634445999516174 s`
  - registration/warp: `0.26053649955429137 s`
  - local normalization: `0.3465078000444919 s`
  - resident integration: `3.2750763000221923 s`
  - output write: `0.24216460005845875 s`
- Interpretation: this gate changes CPU/tile master DQ artifact generation. The
  real resident guard confirms the high-VRAM mainline still runs and preserves
  outputs. The improved elapsed ratio is treated as normal run variance, not as
  a claimed performance gain from this gate.

## CUDA

- CUDA available: yes.
- Native backend: available.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- Master DQ FITS artifacts are guaranteed for CPU/tile StackEngine-built
  masters in the default calibration path.
- Direct `_stack_mean_master` API calls keep DQ optional through `dq_path`.
- Explicit legacy master fallback remains diagnostic and does not promise
  master DQ artifacts.
- Resident CUDA master-cache DQ semantics remain represented by resident
  calibration contracts, not by these CPU/tile FITS sidecars.

## Next Step

- Return to a substantive Phase 2 performance target: resident
  I/O/upload/calibration overlap, resident registration/warp orchestration, or
  a redesigned scalable CUDA order-statistic reducer.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned StackEngine code, GLASS DQ flags, GLASS
calibration policy, GLASS FITS tile writers, GLASS tests, synthetic fixtures,
and user-owned real benchmark artifacts. It did not inspect, copy, summarize,
or rework external proprietary implementation source, and it did not modify
input directories.
