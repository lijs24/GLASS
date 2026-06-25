# S2-Gate 624 Status: Native Active-Count Admission For Over-Limit Hardened Groups

## Gate

S2-Gate 624

## Completed Content

- Changed native resident hardened winsorized CUDA admission from total frame
  count only to finite positive-weight sample count.
- Native CUDA now rejects all-inactive groups and groups with more than `512`
  positive-weight samples, but can process total-frame groups above `512` when
  the final active positive-weight count is within the exact prototype limit.
- Unit-positive over-limit groups automatically use the existing active-index
  CUDA kernel with a recorded reason:
  `native_active_count_admission_over_frame_limit`.
- The CUDA launch selector now chooses `small_256` or `large_512` from the
  positive-weight admission count.
- The Python wrapper reads native profile capacity fields instead of guessing
  only from resident stack total frame count.
- The resident pipeline applies a late native promotion after registration,
  frame-mask, and weighting decisions are final.
- Added focused contract and CUDA tests, updated Phase 2/integration/known
  limitations/algorithm-source docs, and ran real 200-light regression.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8'
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_late_promotes_active_count_native tests/test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_keeps_segmented_when_active_count_over_limit
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_over_limit_active_count_native tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_over_limit_nonunit_active_count_native tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_over_limit_active_count_rejects
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_matches_cpu_baseline tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_260_frames_matches_cpu_baseline tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_active_index_default_off tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_unit_weight_local_reuse_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_compact_count_maps_match_float_maps tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_master_only_matches_full_master tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_honors_rejection_guard
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate624_active_count_native\real_200_default_gate624_20260625_123824 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate621_ordered_sample_reuse\real_200_default_audit_guarded_20260625_022933 --candidate-run C:\glass_runs\phase2_s2_gate624_active_count_native\real_200_default_gate624_20260625_123824 --out C:\glass_runs\phase2_s2_gate624_active_count_native\resident_regression_gate_gate624_vs_gate621.json --markdown C:\glass_runs\phase2_s2_gate624_active_count_native\resident_regression_gate_gate624_vs_gate621.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
```

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native rebuild: passed with existing Windows/CUDA header encoding warnings.
- Late-promotion contract tests: `2 passed in 0.84 s`.
- Focused CUDA active-count tests: `2 passed in 0.78 s`, then expanded
  unit/non-unit/reject coverage: `3 passed in 0.40 s`.
- Existing hardened CUDA parity/guard tests: `8 passed in 0.22 s`.
- Ruff over touched Python files: passed.
- Diff hygiene: passed, with Windows LF-to-CRLF warnings only.
- Full pytest: `1314 passed in 56.73 s`.
- Real 200-light candidate run:
  `C:\glass_runs\phase2_s2_gate624_active_count_native\real_200_default_gate624_20260625_123824`.
- Real regression gate:
  `C:\glass_runs\phase2_s2_gate624_active_count_native\resident_regression_gate_gate624_vs_gate621.json`.
  - Status: passed.
  - Failed checks: none.
  - Candidate/baseline elapsed ratio: `1.0874700202251362`.
  - Determinism differences: artifact `0`, frame signatures `0`,
    registration `0`, frame accounting `0`, output `0`, numerical drift `0`.
  - Candidate frame accounting: `193` active, `7` masked.
  - Candidate total elapsed: `11.408380899578333 s`.
  - Candidate resident integration: `3.3215715000405908 s`.
  - Candidate hardened kernel sync: `3.1951047 s`.
  - Candidate active-count admission on 200-light run: false, because total
    frame count is already below the native limit.

## CUDA Availability

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA Toolkit used by native build: 13.2.

## Known Limitations

- Gate624 does not remove the 512 positive-sample native exact prototype limit.
- Groups with more than 512 positive-weight samples still use the segmented
  CPUStackEngine resident tile fallback.
- The true final target remains a scalable device-resident segmented or
  cooperative order-statistic reducer.
- The 200-light real benchmark does not exercise the over-limit branch because
  its total input count is 200.

## Next Step

Implement or prototype a true over-512 positive-sample device-side segmented
order-statistic reducer, then validate against CPUStackEngine on synthetic
large-active-count groups before any default promotion.

## Clean-Room Compliance

Compliant. This gate is derived from GLASS-owned CUDA kernels, GLASS resident
frame-weight contracts, GLASS CPU-baseline comparisons, and GLASS-generated
synthetic/real-data validation. It does not inspect, copy, summarize, or rework
external proprietary implementation source, and it does not modify input image
directories.
