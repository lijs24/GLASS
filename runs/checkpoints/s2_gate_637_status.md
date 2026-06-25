# S2-Gate 637 Status: Resident DQ Lifecycle Contract

## Gate

- Gate: S2-Gate 637
- Date: 2026-06-25
- Status: green checkpoint
- Purpose: mainline framework hardening, not a micro-optimization or
  report-only gate

## Completed Content

- Added a resident DQ lifecycle contract joining:
  - `resident_source_dq_execution.json`
  - `resident_frame_masks.json`
  - `resident_dq_pixel_closure.json`
  - `pipeline_contract.json`
  - `resident_regression_gate`
- Added `src/glass/engine/resident_dq_lifecycle.py`.
- Updated resident source-DQ accounting so integration `input_samples` are
  counted over active frames while all-frame counters remain available for
  registration/catalog audit.
- Updated resident CUDA runs to write and register
  `resident_dq_lifecycle.json`.
- Updated pipeline contract, resident regression gate, and CLI escape hatch.
- Added/updated tests for lifecycle validation, active-frame source-DQ
  accounting, resident CUDA outputs, regression-gate requirements, pipeline
  contract, and guardrails auto-discovery.
- Updated Phase 2 docs, validation record, and algorithm-source log.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_dq_lifecycle.py src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\report\pipeline_contract.py src\glass\report\resident_regression_gate.py src\glass\cli.py tests\test_resident_dq_lifecycle.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py tests\test_resident_regression_gate.py tests\test_pipeline_contract.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_dq_lifecycle.py tests\test_resident_source_dq.py tests\test_pipeline_contract.py tests\test_resident_regression_gate.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "resident_cuda_run_smoke or applies_plan_source_dq_sidecar or science_output_maps"
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
.\.venv\Scripts\python.exe -c "import glass_cuda as g; print('cuda_available', g.cuda_available()); print(g.list_devices())"
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_guardrails_auto_discovers_run_resident_result_contract
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_dq_lifecycle.py src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\report\pipeline_contract.py src\glass\report\resident_regression_gate.py src\glass\cli.py tests\test_resident_dq_lifecycle.py tests\test_resident_source_dq.py tests\test_resident_cuda_run.py tests\test_resident_regression_gate.py tests\test_pipeline_contract.py tests\test_cli_smoke.py
```

Real 200-light command:

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle" --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final"
```

Regression/acceptance commands:

```powershell
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt --candidate-run C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle --out C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_vs_gate636_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_vs_gate636_regression_gate.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_vs_wbpp_compare.html --glass-scale 8.7644349571156089E-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json" --glass-run C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle --wbpp-result "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\warp_quality_contract.json --require-warp-quality-contract
```

## Test Results

- Focused lifecycle/source-DQ/pipeline/regression tests: `69 passed`.
- Focused resident CUDA smoke/science-output tests:
  `3 passed, 124 deselected`.
- Fixed guardrails fixture after full-test discovery:
  `tests/test_cli_smoke.py::test_cli_guardrails_auto_discovers_run_resident_result_contract`
  passed.
- Full test suite: `1336 passed in 57.75 s`.
- Ruff over touched files: passed.

## CUDA Availability

- CUDA available to GLASS: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- Driver: `596.21`.
- VRAM: `97886 MiB` reported by GLASS, `97887 MiB` reported by `nvidia-smi`.

## Real 200-light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle`.
- Evidence root:
  `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833`.
- GLASS elapsed: `12.156182300066575 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `89.87533857517228x`.
- Frame accounting: `200` planned lights, `193` active weighted frames,
  `7` zero-weight/masked frames.
- Calibration frame counts in acceptance audit: `20` bias, `20` dark,
  `20` flat.
- Resident DQ lifecycle: passed.
- Lifecycle active/masked counts: `193 / 7`.
- Lifecycle active-frame source input samples: `11898681600`.
- Regression versus Gate636: passed, elapsed ratio `0.9990383208570693`,
  zero output differences and zero numerical drift.
- Coverage-masked compare at coverage >= `190`:
  - shape match: true
  - RMS difference: `0.0056241382952344435`
  - p99 absolute difference: `0.002143551869085057`
  - coverage fraction: `0.9749333995120938`
  - compared pixels: `60105814`
- Pipeline contract: passed.
- StackEngine contract: passed.
- Warp quality contract: passed.
- Acceptance audit: passed.

## Main Artifacts

- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\resident_dq_lifecycle.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\resident_source_dq_execution.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\resident_frame_masks.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\resident_dq_pixel_closure.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle\pipeline_contract.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_vs_gate636_regression_gate.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_vs_wbpp_compare.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_wbpp_speedup_summary.json`
- `C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\gate637_acceptance_audit.json`

## Known Limitations

- This gate changes audit/accounting semantics and contract enforcement only;
  it does not improve image math or throughput.
- The real M38 dataset had zero source-DQ invalid samples, so nonzero
  source-DQ behavior is validated by focused/synthetic tests rather than the
  real run.
- The next gate should return to Phase 2 execution substance: StackEngine
  default path completion, DQ/mask pipeline semantics, resident
  registration/warp batching, or the resident integration reducer.

## Next Step

Run a substantive gate on the mainline execution path. Recommended:
S2-Gate 638, focused on making the DQ/mask pipeline contract and StackEngine
default-readiness evidence complete for resident outputs while preserving the
Gate637 200-light runtime/result baseline.

## Clean-room Compliance

- Input image directories were read-only.
- This gate used GLASS artifacts, GLASS tests, and user-generated external
  reference timing/output metadata only.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked for this gate.
