# S2-Gate 625 Status: Opt-In Radix-Select CUDA Reducer For Over-512 Active Samples

## Gate

S2-Gate 625

## Completed Content

- Added an opt-in resident CUDA hardened `winsorized_sigma` reducer for groups
  with more than `512` finite positive-weight samples.
- Implemented device-side sortable-float radix/order-statistic selection for
  exact q25/median/q75 without a per-thread `values[MaxFrames]` local sample
  array.
- Added float32 and `uint16` count-map native launch wrappers for the radix path.
- Added native profile fields:
  `percentile_strategy=radix_select_order_statistics_scan`,
  `native_kernel_capacity_selector=radix_select_unbounded_positive_samples`,
  `radix_select_requested`, `radix_select_enabled`, and
  `radix_select_positive_sample_count`.
- Kept the path explicit behind `GLASS_CUDA_RADIX_SELECT_WINSORIZED=1`; default
  resident runs still use the Gate624 `<=512` native exact kernels or the
  segmented CPUStackEngine fallback.
- Extended the resident runtime contract so an over-512 active-count group can
  late-promote to native radix-select only when the environment gate is set.
- Added focused CUDA and runtime-contract tests, updated integration/Phase 2
  docs, known limitations, and algorithm-source audit notes.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8'
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_over_limit_active_count_rejects tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_radix_select_over_512_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_over_limit_active_count_native tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_over_limit_nonunit_active_count_native tests/test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_keeps_segmented_when_active_count_over_limit tests/test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_radix_select_promotes_over_limit_active_count tests/test_resident_cuda_run.py::test_resident_hardened_winsorized_contract_late_promotes_active_count_native
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma"
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "resident_hardened_winsorized_contract"
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate625_radix_select\real_200_default_gate625_20260625_125620 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate624_active_count_native\real_200_default_gate624_20260625_123824 --candidate-run C:\glass_runs\phase2_s2_gate625_radix_select\real_200_default_gate625_20260625_125620 --out C:\glass_runs\phase2_s2_gate625_radix_select\resident_regression_gate_gate625_vs_gate624.json --markdown C:\glass_runs\phase2_s2_gate625_radix_select\resident_regression_gate_gate625_vs_gate624.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\python.exe -m pytest -q
```

Additional synthetic radix probe:

```powershell
# inline Python probe wrote:
C:\glass_runs\phase2_s2_gate625_radix_select\radix_select_synthetic_probe.json
```

## Test Results

- Native rebuild: passed with existing Windows/CUDA Toolkit header encoding
  warnings.
- Focused direct CUDA/runtime contract suite: `7 passed in 3.01 s`.
- Hardened resident CUDA suite: `13 passed, 52 deselected`.
- Resident hardened runtime-contract suite: `5 passed, 122 deselected`.
- Ruff over touched Python files: passed.
- Full pytest: `1316 passed in 58.52 s`.

## Synthetic Over-512 Probe

- Artifact:
  `C:\glass_runs\phase2_s2_gate625_radix_select\radix_select_synthetic_probe.json`.
- Shape: `545 x 24 x 24`, finite stack, `545` positive-weight samples.
- CUDA radix profile:
  - `radix_select_enabled=true`.
  - `native_kernel_capacity_selector=radix_select_unbounded_positive_samples`.
  - `kernel_sync_s=0.0257003`.
  - `total_s=0.025942100095562637`.
- CPU baseline time: `0.007896299939602613 s`.
- Result: passed.
- Max/RMS differences for master, weight, coverage, low-reject, high-reject:
  all `0.0`.

## Real 200-Light Regression

- Candidate run:
  `C:\glass_runs\phase2_s2_gate625_radix_select\real_200_default_gate625_20260625_125620`.
- Baseline run:
  `C:\glass_runs\phase2_s2_gate624_active_count_native\real_200_default_gate624_20260625_123824`.
- Regression artifact:
  `C:\glass_runs\phase2_s2_gate625_radix_select\resident_regression_gate_gate625_vs_gate624.json`.
- Status: passed.
- Failed checks: none.
- Elapsed ratio: `1.0066770649740113` against max `1.15`.
- Determinism differences: artifact `0`, frame signature `0`,
  registration `0`, frame accounting `0`, output `0`, numerical drift `0`.
- Candidate frame accounting: `193` active, `7` masked.
- Candidate total elapsed: `11.484555400093086 s`.
- Candidate resident integration: `3.3958331999601796 s`.

## CUDA Availability

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- CUDA Toolkit used by native build: `13.2`.

## Known Limitations

- Radix-select is opt-in, not default.
- The radix kernel rereads the resident frame axis many times per percentile and
  is correctness-first rather than throughput-optimized.
- The real 200-light default run does not exercise radix-select because the
  default active positive-weight count is `193`.
- A NaN-containing stress probe exposed rare one-sample rejection-boundary drift
  when a sample lies exactly on a threshold and CPU vectorized `nanmean`/`nanstd`
  order differs from device frame-axis accumulation. This is documented as a
  parity-hardening follow-up, not hidden behind a threshold tolerance.

## Next Step

Benchmark radix-select against segmented CPUStackEngine fallback on larger
active-count synthetic or real groups, then optimize the device reducer with
cooperative/block-level selection or segmented batching before any default
promotion.

## Clean-Room Compliance

Compliant. This gate is derived from GLASS-owned CUDA kernels, GLASS resident
frame-weight/runtime contracts, GLASS CPU-baseline comparisons, and
GLASS-generated synthetic/real-data validation. It does not inspect, copy,
summarize, or rework external proprietary implementation source, and it does not
modify input image directories.
