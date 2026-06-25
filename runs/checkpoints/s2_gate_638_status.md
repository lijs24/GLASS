# S2-Gate 638 Status: Frame Accounting Resident DQ Lifecycle Bridge

## Gate

- Gate: S2-Gate 638
- Date: 2026-06-25
- Status: green checkpoint
- Purpose: mainline DQ/mask and StackEngine framework hardening

## Completed Content

- Connected `resident_dq_lifecycle.json` into canonical
  `frame_accounting.json`.
- Added per-frame frame-accounting fields for resident DQ lifecycle
  availability, status, pass/fail state, filter, active/masked group counts,
  and source input sample count.
- Added frame-accounting summary fields for resident DQ lifecycle presence,
  status, group count, row count, passed/failed rows, active/masked counts,
  and source input samples.
- Added `frame_accounting_resident_dq_lifecycle_contract` to pipeline
  contract.
- Updated resident CUDA smoke tests to assert production frame accounting
  carries lifecycle evidence and pipeline contract validates it.
- Updated Phase 2 control docs, validation notes, and algorithm-source log.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_accounting.py tests\test_pipeline_contract.py tests\test_resident_dq_lifecycle.py tests\test_resident_cuda_run.py -k "frame_accounting or dq_lifecycle or resident_cuda_run_smoke or science_output_maps"
.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_accounting.py tests\test_pipeline_contract.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "resident_cuda_run_smoke or science_output_maps or applies_plan_source_dq_sidecar"
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\frame_accounting.py src\glass\report\pipeline_contract.py tests\test_frame_accounting.py tests\test_pipeline_contract.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
.\.venv\Scripts\python.exe -c "import glass_cuda as g; print('cuda_available', g.cuda_available()); print(g.list_devices())"
```

Real 200-light command:

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle" --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir "C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final"
```

Regression/acceptance commands:

```powershell
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate637_dq_lifecycle\runs_20260625_153833\candidate_dq_lifecycle --candidate-run C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle --out C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_vs_gate637_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_vs_gate637_regression_gate.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_vs_wbpp_compare.html --glass-scale 8.7644349571156089E-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json" --glass-run C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle --wbpp-result "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\warp_quality_contract.json --require-warp-quality-contract
```

## Test Results

- Focused frame-accounting/pipeline/resident tests:
  `13 passed, 168 deselected`.
- Full frame-accounting and pipeline-contract tests: `54 passed`.
- Resident CUDA focused smoke/science-output tests:
  `3 passed, 124 deselected`.
- Full test suite: `1337 passed in 57.91 s`.
- Ruff over touched files: passed.

## CUDA Availability

- CUDA available to GLASS: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- Driver: `596.21`.
- VRAM: `97886 MiB` reported by GLASS, `97887 MiB` reported by `nvidia-smi`.

## Real 200-light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle`.
- Evidence root:
  `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638`.
- GLASS elapsed: `12.560182699817233 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `86.98448311710449x`.
- Frame accounting lifecycle bridge:
  - rows: `200`
  - passed rows: `200`
  - active frames: `193`
  - masked frames: `7`
  - source input samples: `11898681600`
- Regression versus Gate637: passed, elapsed ratio `1.0332341511321728`,
  zero output differences, zero frame-accounting differences, and zero
  numerical drift.
- Coverage-masked compare at coverage >= `190`:
  - shape match: true
  - RMS difference: `0.0056241382952344435`
  - p99 absolute difference: `0.002143551869085057`
  - coverage fraction: `0.9749333995120938`
  - compared pixels: `60105814`
- Pipeline contract: passed, including
  `frame_accounting_resident_dq_lifecycle_contract`.
- StackEngine contract: passed.
- Warp quality contract: passed.
- Acceptance audit: passed.

## Main Artifacts

- `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\frame_accounting.json`
- `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\pipeline_contract.json`
- `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\candidate_frame_accounting_lifecycle\resident_dq_lifecycle.json`
- `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_vs_gate637_regression_gate.json`
- `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_vs_wbpp_compare.json`
- `C:\glass_runs\phase2_s2_gate638_frame_accounting_lifecycle\runs_20260625_155638\gate638_acceptance_audit.json`

## Known Limitations

- This gate changes accounting and contract evidence only; it does not improve
  image math or throughput.
- Pipeline contract validates the frame-accounting lifecycle bridge when
  frame accounting advertises lifecycle evidence. Partial old fixtures that do
  not advertise the bridge remain readable for targeted tests.
- The next gate should return to execution substance: resident registration/
  warp batching, resident integration reducer work for heavier stacks, or a
  still-legacy StackEngine default execution path.

## Clean-room Compliance

- Input image directories were read-only.
- This gate used GLASS artifacts, GLASS tests, and user-generated external
  reference timing/output metadata only.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked for this gate.
