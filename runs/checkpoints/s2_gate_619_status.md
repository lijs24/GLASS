# S2-Gate 619 Status: Resident Hardened Master-Only Download Mode

## Gate

- Gate: S2-Gate 619
- Status: green
- Branch: `main`
- Date: 2026-06-25

## Completed Contents

- Added `download_mode=full|master_weight|master_only` to
  `ResidentCalibratedStack.integrate_hardened_winsorized_sigma`.
- Hardened winsorized CUDA integration now accepts omitted weight,
  coverage, low-rejection, and high-rejection output pointers.
- Native bindings skip device allocation and D2H copies for omitted maps and
  return Python `None` values for omitted arrays.
- Resident runtime now passes `download_mode=master_only` for compatible stack
  dispatches when `--resident-output-maps minimal` is requested, including
  explicit `--resident-winsorized-mode hardened_cpu_parity`.
- Default audit/science output remains `download_mode=full`; DQ, coverage,
  rejection maps, and regression-gate evidence are unchanged.
- Updated Phase 2 docs, integration model notes, and algorithm-source ledger.

## Commands Run

- Native rebuild:
  - `cmd /S /C "\"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat\" -arch=x64 && \".\.venv\Scripts\cmake.exe\" --build build --config Release --target _glass_cuda_native -j 8"`
- Focused CUDA/native tests:
  - `python -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"`
  - `python -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_minimal_output_master_only tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline tests\test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads`
- Ruff:
  - `python -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- Real 200-light default validation:
  - `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_default_audit --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
  - `glass resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\real_200_default_contract_gate --candidate-run C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_default_audit --out C:\glass_runs\phase2_s2_gate619_hardened_master_only\resident_regression_gate_vs_gate618_default.json --markdown C:\glass_runs\phase2_s2_gate619_hardened_master_only\resident_regression_gate_vs_gate618_default.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Real 200-light master-only probe:
  - Full-chain minimal probe failed as expected at `warp_quality_contract`:
    `C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_hardened_minimal_master_only\warp_quality_contract.json`.
  - Integration-only probe:
    `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_hardened_minimal_integration_only --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps minimal --resident-winsorized-mode hardened_cpu_parity --resident-registration off --local-normalization off --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- Full validation:
  - `python -m pytest -q`
  - `git diff --check`

## Test Results

- Native rebuild: passed.
- Focused CUDA hardened winsorized tests: `5 passed, 52 deselected`.
- Focused resident CLI tests: `3 passed`.
- Ruff: passed.
- Full pytest: `1304 passed in 52.93 s`.
- `git diff --check`: passed; only existing CRLF conversion warnings.

## Real 200-Light Evidence

- Default candidate:
  `C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_default_audit`
- Gate618 baseline:
  `C:\glass_runs\phase2_s2_gate618_result_contract_runtime_gate\real_200_default_contract_gate`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate619_hardened_master_only\resident_regression_gate_vs_gate618_default.json`
- Regression markdown:
  `C:\glass_runs\phase2_s2_gate619_hardened_master_only\resident_regression_gate_vs_gate618_default.md`
- Regression result: passed.
- Candidate/baseline elapsed ratio: `0.9976734039350794`.
- Candidate best elapsed: `10.842480299877934 s`.
- Determinism differences: artifacts `0`, frame accounting `0`,
  registration `0`, output differences `0`, output numerical drift `0`.
- Candidate frame admission: `193 / 200` active, `7` masked.
- Candidate timing highlights:
  - light read/upload/calibrate: `3.273685200023465 s`
  - resident registration/warp: `0.26079330046195537 s`
  - resident integration: `3.3746273000724614 s`
  - output write: `0.30138399999123067 s`

## Master-Only Probe Evidence

- Integration-only probe:
  `C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_hardened_minimal_integration_only`
- This probe intentionally disabled resident registration and local normalization,
  so it is not a full science-output A/B. It isolates the hardened integration
  output-transfer path.
- Default audit native hardened integration:
  - `download_mode=full`
  - downloaded arrays: `5`
  - downloaded bytes: `863116800`
  - native download: `0.1161562 s`
  - native kernel sync: `3.252292 s`
  - hardened total: `3.374569399980828 s`
- Minimal integration-only native hardened integration:
  - `download_mode=master_only`
  - downloaded arrays: `1`
  - downloaded bytes: `246604800`
  - native download: `0.0333768 s`
  - native kernel sync: `3.0944796 s`
  - hardened total: `3.1296569999540225 s`
- Full-chain minimal output remains blocked by `warp_quality_contract` because
  minimal output omits geometric coverage. This is intentional and preserves the
  Gate618 result-contract safety behavior.

## CUDA

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: about `97886 MiB`.
- Native backend: rebuilt successfully with CUDA Toolkit 13.2.

## Known Limits

- This gate reduces output map allocation/download only for minimal-output
  stack-dispatch hardened winsorized runs. It does not speed up the default
  audit/science path, which still needs full maps for DQ and regression
  evidence.
- The hardened winsorized kernel itself remains the dominant resident
  integration cost; master-only mode reduces transfer/workspace overhead, not
  percentile/rejection computation.
- Full-chain minimal output is still not a promoted science path because current
  warp-quality evidence depends on geometric coverage maps.
- Historical untracked probe artifacts in `runs/checkpoints/` were left
  untouched and were not staged.

## Clean-Room Compliance

- Input image directories were treated as read-only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- This gate uses GLASS-owned CUDA kernels, wrappers, runtime output-map policy,
  tests, and user-owned benchmark outputs.

## Next Step

- Return to the larger measured bottleneck: reduce the hardened winsorized
  kernel time itself or pipeline the resident read/upload/calibration path
  without changing default audit/science outputs.
