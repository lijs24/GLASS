# S2-Gate 633 Status: Lazy Fallback Scale In Hardened Reducer

## Gate

S2-Gate 633 targets the resident CUDA hardened winsorized integration hot path.
The bounded 256/512-frame reducer no longer computes fallback mean/std for
every pixel before q25/median/q75 selection. It now computes fallback std only
when the median/IQR scale is zero or non-finite.

## Completed

- Updated the bounded resident hardened winsorized CUDA reducer to use
  `lazy_iqr_degenerate_frame_axis_rescan`.
- Preserved CPUStackEngine parity by recomputing fallback samples in original
  frame-axis order for degenerate IQR pixels.
- Added native profile fields:
  - `fallback_scale_strategy=lazy_iqr_degenerate_frame_axis_rescan`
  - `fallback_scale_default_path=median_iqr_scale_without_fallback_std`
- Added a CUDA/CPU parity test that forces the IQR-degenerate fallback branch.
- Updated Phase 2 algorithm hardening notes, known limitations, and algorithm
  source ledger.

## Code Changes

- `cpp/cuda/integration_kernels.cu`
- `cpp/src/native_bindings.cpp`
- `tests/test_cuda_resident_stack.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `docs/known_limitations.md`

## Real 200-Light Evidence

- Candidate root:
  `C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040`
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\gate633_lazy_fallback_summary.json`
- Summary Markdown:
  `C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\gate633_lazy_fallback_summary.md`
- Regression gate 1:
  `regression_gate632_promoted_vs_gate633_lazy.json`
  - baseline: Gate632 `default_promoted_single_wait`
  - candidate: Gate633 `candidate_lazy_fallback`
  - status: passed
  - elapsed ratio: `1.026617075839138`
- Regression gate 2:
  `regression_gate632_single_wait_r2_vs_gate633_lazy_r2.json`
  - baseline: Gate632 `single_wait_r2`
  - candidate: Gate633 `candidate_lazy_fallback_r2`
  - status: passed
  - elapsed ratio: `1.0044802533947044`

Measured rows:

| variant | total s | resident integration s | hardened total s | kernel sync s | fallback strategy |
|---|---:|---:|---:|---:|---|
| gate632_promoted | 10.820 | 3.320 | 3.320 | 3.198 | eager_fallback_std_before_quartiles |
| gate633_lazy | 11.108 | 3.317 | 3.317 | 3.183 | lazy_iqr_degenerate_frame_axis_rescan |
| gate632_single_wait_r2 | 10.687 | 3.316 | 3.316 | 3.193 | eager_fallback_std_before_quartiles |
| gate633_lazy_r2 | 10.735 | 3.308 | 3.308 | 3.178 | lazy_iqr_degenerate_frame_axis_rescan |

Ratios:

- Pair 1 total elapsed: `1.026617`
- Pair 1 kernel sync: `0.995285`
- Pair 2 total elapsed: `1.004480`
- Pair 2 kernel sync: `0.995307`

## Commands Run

```powershell
cmd.exe /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8"

.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py -k "hardened_winsorized"

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\default_promoted_single_wait --candidate-run C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback --out C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\regression_gate632_promoted_vs_gate633_lazy.json --markdown C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\regression_gate632_promoted_vs_gate633_lazy.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\single_wait_r2 --candidate-run C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2 --out C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\regression_gate632_single_wait_r2_vs_gate633_lazy_r2.json --markdown C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\regression_gate632_single_wait_r2_vs_gate633_lazy_r2.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\ruff.exe check src tests docs --select E,F --ignore E501
git diff --check
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native build: passed.
- Focused CUDA hardened winsorized tests: `17 passed, 52 deselected in 3.69s`.
- Focused resident CUDA hardened tests: `7 passed, 120 deselected in 3.94s`.
- Ruff: passed.
- `git diff --check`: passed with only Windows LF/CRLF warnings.
- Full pytest: `1327 passed in 60.47s`.

## CUDA Availability

- CUDA available: yes.
- Native CUDA extension: rebuilt successfully.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Driver: `596.21`.
- Reported VRAM: `97887 MiB`.

## Known Limits

- Kernel-sync improved slightly in both real 200-light pairs, but total elapsed
  time did not materially improve because the gain is smaller than surrounding
  I/O, calibration, registration, and output-write variance.
- The reducer remains a one-thread-per-pixel local-array implementation bounded
  to 512 positive samples unless the opt-in radix-select prototype is enabled.
- This gate does not change registration/warp orchestration, local
  normalization, output maps, or default frame admission.

## Next Step

Proceed to a larger substantive S2 gate: redesign the resident hardened
reducer around cooperative/segmented device-side order statistics, or attack
resident registration/warp orchestration and deeper native read/H2D/calibration
overlap. Do not spend the next gate on report-only/default-promotion plumbing
unless it directly blocks these paths.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned CUDA reducer code, GLASS CPUStackEngine
semantics, GLASS tests, and user-owned 200-light benchmark artifacts. It does
not inspect, copy, summarize, or rework external/proprietary implementation
source, and it does not modify input image directories.
