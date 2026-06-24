# S2-Gate 618 Status: Resident Result Contract Runtime Gate

## Gate

- Gate: S2-Gate 618
- Status: green
- Branch: `main`
- Date: 2026-06-25

## Completed Contents

- Promoted resident CUDA result-contract validation into the resident runtime
  path.
- `run_resident_calibration_integration` now raises before frame accounting and
  final run-state publication when `resident_result_contract.json` contains a
  fatal structural, map, DQ, provenance, or sample-accounting failure.
- Kept admission-only failures such as `active_frame_count_not_degenerate`
  nonfatal at runtime so low-quality registration diagnostics can still
  generate artifacts; those failures remain visible in the contract and are
  blocked by resident regression thresholds.
- Tightened `glass resident-regression-gate` so candidate runs now require, by
  default:
  - `pipeline_contract.json`
  - `stack_engine_contract.json`
  - `resident_result_contract.json`
  - `resident_frame_masks.json`
  - `resident_dq_pixel_closure.json`
  - `resident_source_dq_execution.json`
  - `resident_master_cache.json`
- Added explicit `--allow-missing-*` diagnostic escape hatches for old run
  directories.
- Updated Phase 2 control docs and algorithm-source log.

## Real 200-Light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\real_200_default_contract_gate`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate617_pipelined_warp\real_200_default_guarded_chunked_direct_launch`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\resident_regression_gate_vs_gate617_default.json`
- Regression markdown:
  `C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\resident_regression_gate_vs_gate617_default.md`
- Result: passed.
- Candidate/baseline elapsed ratio: `1.023597059132631`.
- Candidate total elapsed: `10.867765199625865 s`.
- Candidate resident integration: `3.4178823999827728 s`.
- Frame admission: `193 / 200` active, `7` masked.
- Determinism differences: output differences `0`, output numerical drift `0`.
- Candidate `resident_result_contract.json`: passed.
- Candidate `resident_dq_pixel_closure.json`: passed.

## Commands Run

- Focused tests:
  - `python -m pytest -q tests\test_resident_regression_gate.py tests\test_resident_cuda_run.py::test_resident_result_contract_payload_validation_accepts_passed tests\test_resident_cuda_run.py::test_resident_result_contract_payload_validation_raises_failed_checks`
  - `python -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_rejects_low_quality_matrix tests\test_resident_cuda_run.py::test_resident_result_contract_payload_validation_accepts_passed tests\test_resident_cuda_run.py::test_resident_result_contract_payload_validation_raises_failed_checks tests\test_resident_cuda_run.py::test_resident_result_contract_payload_validation_allows_admission_only_failure tests\test_resident_regression_gate.py`
- Ruff:
  - `ruff check src\glass\engine\resident_cuda.py src\glass\report\resident_regression_gate.py src\glass\cli.py tests\test_resident_regression_gate.py tests\test_resident_cuda_run.py`
- Real 200-light validation:
  - `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\real_200_default_contract_gate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
  - `glass resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate617_pipelined_warp\real_200_default_guarded_chunked_direct_launch --candidate-run C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\real_200_default_contract_gate --out C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\resident_regression_gate_vs_gate617_default.json --markdown C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\resident_regression_gate_vs_gate617_default.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Full validation:
  - `python -m pytest -q`
  - `git diff --check`

## Test Results

- Focused tests: passed.
- Ruff: passed.
- Full pytest: `1302 passed in 52.84 s`.
- `git diff --check`: passed; only existing CRLF conversion warnings.

## CUDA

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Multiprocessors: `188`.
- Driver version: `596.21`.
- Native backend: available.

## Known Limits

- This gate strengthens default-path failure behavior and real A/B evidence
  completeness. It does not accelerate resident registration, warp, local
  normalization, or integration kernels.
- Runtime validation intentionally treats `active_frame_count_not_degenerate`
  as nonfatal so diagnostic low-quality registration runs can complete and
  expose their rejection artifacts. Real default candidates are still blocked by
  resident regression thresholds and contract checks.
- The next performance gate should target the measured 200-light bottlenecks:
  resident integration kernel time and resident read/upload/calibration
  scheduling.

## Clean-Room Compliance

- Input image directories were treated as read-only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- The gate uses GLASS-owned artifact schemas, GLASS runtime code, GLASS tests,
  and user-owned real benchmark outputs.

## Next Step

- Return to a performance-producing mainline gate: either improve the resident
  hardened integration reducer or reduce the read/upload/calibration pipeline
  time without changing output pixels.
