# S2-Gate 626 Status: Deterministic Mixed-Valid Winsorized CPU Baseline

## Gate

S2-Gate 626

## Completed Content

- Replaced the mixed-valid CPU `winsorized_sigma` statistics path with a
  deterministic GLASS baseline.
- Mixed-valid tiles now filter finite valid samples, sort per pixel, and compute
  q25/median/q75 with `(count - 1) * fraction` float32 linear interpolation.
- Fallback standard deviation, winsorized mean, and winsorized standard
  deviation now use frame-axis-valid double accumulation followed by float32
  state, matching the resident radix-select CUDA contract.
- Kept strict final rejection comparisons (`< low`, `> high`); no threshold
  tolerance or hidden guard was added.
- Updated StackEngine rejection-policy provenance strings from `nan*` wording to
  deterministic percentile/mean/std wording.
- Added CPU tests for all-valid and mixed-valid deterministic winsorized paths.
- Added a resident CUDA radix-select mixed-valid test with `545` frames, one NaN
  sample, non-unit weights, and strict rejection-map parity.
- Updated Phase 2 docs, integration model, known limitations, and algorithm
  source log.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\rejection.py tests\test_stack_engine.py tests\test_cuda_resident_stack.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine.py -k winsorized_sigma
.\.venv\Scripts\python.exe -m pytest -q tests/test_cpu_integration.py -k winsorized
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_radix_select_over_512_matches_cpu tests/test_cuda_resident_stack.py::test_resident_stack_hardened_winsorized_sigma_radix_select_mixed_valid_matches_cpu
.\.venv\Scripts\python.exe -m pytest -q tests/test_stack_engine.py tests/test_cpu_integration.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma"
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\real_200_default_gate626_20260625_131241 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate625_radix_select\real_200_default_gate625_20260625_125620 --candidate-run C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\real_200_default_gate626_20260625_131241 --out C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\resident_regression_gate_gate626_vs_gate625.json --markdown C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\resident_regression_gate_gate626_vs_gate625.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\python.exe -m pytest -q
```

Additional inline Python probes wrote:

```powershell
C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\radix_select_nan_boundary_probe.json
```

## Test Results

- Ruff over touched Python files: passed.
- StackEngine winsorized focused tests: `4 passed, 13 deselected`.
- CPU integration winsorized focused tests: `2 passed, 5 deselected`.
- CUDA radix-select focused tests: `2 passed`.
- Wider StackEngine + CPU integration suite: `24 passed`.
- Resident CUDA hardened winsorized suite: `14 passed, 52 deselected`.
- Full pytest: `1318 passed in 61.45 s`.

## Synthetic Mixed-Valid Radix Probe

- Artifact:
  `C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\radix_select_nan_boundary_probe.json`.
- Shape: `545 x 24 x 24`.
- Positive-weight samples: `545`.
- NaN samples: `1`.
- CUDA profile:
  - `radix_select_enabled=true`.
  - `native_kernel_capacity_selector=radix_select_unbounded_positive_samples`.
  - `kernel_sync_s=0.0191543`.
  - `total_s=0.019420300028286874`.
- CPU baseline time: `0.019150400068610907 s`.
- Result: passed.
- Max/RMS differences for master, weight, coverage, low-reject, high-reject:
  all `0.0`; all five maps were bitwise exact.

## Real 200-Light Regression

- Candidate run:
  `C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\real_200_default_gate626_20260625_131241`.
- Baseline run:
  `C:\glass_runs\phase2_s2_gate625_radix_select\real_200_default_gate625_20260625_125620`.
- Regression artifact:
  `C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\resident_regression_gate_gate626_vs_gate625.json`.
- Status: passed.
- Failed checks: none.
- Elapsed ratio: `0.9578194032630468` against max `1.15`.
- Candidate frame accounting: `193` active, `7` masked.
- Candidate total elapsed: `11.000130000058562 s`.
- Candidate resident calibration/integration stage: `10.131210600025952 s`.
- Candidate resident integration: `3.3211964999791235 s`.
- Hardened native kernel sync: `3.197501 s`.
- Native selector: `small_256`; the default 200-light group does not use
  radix-select because it has `193` active positive-weight frames.
- Determinism and contracts: resident-regression-gate passed with no failed
  checks.

## CUDA Availability

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Native rebuild required for this gate: no; this gate changed Python baseline,
  tests, and documentation only.

## Known Limitations

- The radix-select over-512 reducer remains opt-in behind
  `GLASS_CUDA_RADIX_SELECT_WINSORIZED=1`.
- The radix path still rereads the resident frame axis many times per percentile
  and is not yet a throughput-optimized default.
- This gate resolves the Gate625 mixed-valid/NaN rejection-boundary drift by
  changing the CPU baseline contract; it does not implement a faster segmented
  all-device reducer.

## Next Step

Return to substantive Phase 2 throughput work: benchmark and optimize the
over-512 device reducer against the segmented CPUStackEngine fallback, or shift
to the other measured 200-light bottleneck, resident registration/warp
orchestration.

## Clean-Room Compliance

Compliant. This gate is derived from GLASS-owned numerical formulas, GLASS CUDA
parity requirements, GLASS unit tests, GLASS-generated synthetic arrays, and
user-owned 200-light benchmark artifacts. It does not inspect, copy, summarize,
or rework external proprietary implementation source, and it does not modify
input image directories.
