# S2-Gate 620 Status: Resident Hardened Quartile Quickselect Scheduler

## Gate

- Gate: S2-Gate 620
- Status: green
- Branch: `main`
- Date: 2026-06-25

## Completed Contents

- Replaced repeated full-range native q25/median/q75 quickselect scheduling in
  the resident hardened winsorized CUDA reducer with an ascending unique-rank
  quartile selector.
- Preserved the same exact linear-interpolated q25, median, and q75 definitions.
- Preserved the Gate611 frame-axis reread order for winsorized mean/std and
  final weighted accumulation, so the CPU-parity arithmetic order after
  percentile selection remains unchanged.
- Native profiles now record
  `percentile_strategy=ascending_unique_quartile_quickselect_order_statistics`.
- Added CUDA parity coverage for small frame counts `2, 3, 5, 7, 8`, where
  percentile ranks duplicate or land on exact integer positions.
- Updated Phase 2 docs, integration model notes, and algorithm-source ledger.

## Commands Run

- Native rebuild:
  - `cmd /S /C "\"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat\" -arch=x64 && \".\.venv\Scripts\cmake.exe\" --build build --config Release --target _glass_cuda_native -j 8"`
- Focused CUDA/native tests:
  - `python -m pytest -q tests\test_cuda_resident_stack.py -k "hardened_winsorized_sigma"`
  - `python -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_minimal_output_master_only`
- Ruff:
  - `python -m ruff check tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- Real 200-light default validation:
  - `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate620_quartile_scheduler\real_200_default_audit --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
  - `glass resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_default_audit --candidate-run C:\glass_runs\phase2_s2_gate620_quartile_scheduler\real_200_default_audit --out C:\glass_runs\phase2_s2_gate620_quartile_scheduler\resident_regression_gate_vs_gate619_default.json --markdown C:\glass_runs\phase2_s2_gate620_quartile_scheduler\resident_regression_gate_vs_gate619_default.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- Full validation:
  - `python -m pytest -q`
  - `git diff --check`

## Test Results

- Native rebuild: passed.
- Focused CUDA hardened winsorized tests: `6 passed, 52 deselected`.
- Focused resident CLI hardened tests: `2 passed`.
- Ruff: passed.
- Full pytest: `1305 passed in 53.19 s`.
- `git diff --check`: passed; only existing CRLF conversion warnings.

## Real 200-Light Evidence

- Candidate run:
  `C:\glass_runs\phase2_s2_gate620_quartile_scheduler\real_200_default_audit`
- Gate619 baseline:
  `C:\glass_runs\phase2_s2_gate619_hardened_master_only\real_200_default_audit`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate620_quartile_scheduler\resident_regression_gate_vs_gate619_default.json`
- Regression markdown:
  `C:\glass_runs\phase2_s2_gate620_quartile_scheduler\resident_regression_gate_vs_gate619_default.md`
- Regression result: passed.
- Candidate/baseline elapsed ratio: `0.9766605524966213`.
- Candidate timing deltas:
  - light read/upload/calibrate: `3.273685200023465 s` to
    `3.253148499992676 s`
  - resident registration/warp: `0.26079330046195537 s` to
    `0.26315299957059324 s`
  - resident integration: `3.3746273000724614 s` to
    `3.29226309992373 s`
  - output write: `0.30138399999123067 s` to `0.24100090004503727 s`
- Native hardened integration timing:
  - Gate619 native profile:
    - `percentile_strategy=quickselect_order_statistics`
    - `kernel_sync_s=3.252292`
    - `download_s=0.1161562`
    - `downloaded_arrays=5`
    - `downloaded_bytes=863116800`
    - `total_s=3.374569399980828`
  - Gate620 native profile:
    - `percentile_strategy=ascending_unique_quartile_quickselect_order_statistics`
    - `kernel_sync_s=3.1733044`
    - `download_s=0.1146506`
    - `downloaded_arrays=5`
    - `downloaded_bytes=863116800`
    - `total_s=3.292202000040561`
- Determinism differences: artifacts `0`, frame accounting `0`,
  registration `0`, output differences `0`, output numerical drift `0`.
- Candidate frame admission: `193 / 200` active, `7` masked.

## CUDA

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: about `97886 MiB`.
- Native backend: rebuilt successfully with CUDA Toolkit 13.2.

## Known Limits

- This gate reduces repeated quartile quickselect scheduling work but keeps the
  per-pixel local-array reducer. The hardened kernel is still the dominant
  resident integration cost.
- Native resident hardened winsorized integration remains bounded to 512 frames.
  Larger groups still require the correctness-first segmented CPUStackEngine
  fallback until a scalable all-device reducer exists.
- The default audit/science output map path is unchanged and still downloads all
  maps required for DQ and regression evidence.
- Historical untracked probe artifacts in `runs/checkpoints/` were left
  untouched and were not staged.

## Clean-Room Compliance

- Input image directories were treated as read-only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- This gate uses GLASS-owned CUDA kernels, CPU-baseline parity tests, runtime
  artifacts, and user-owned 200-light benchmark outputs.

## Next Step

- Continue attacking the resident hardened integration bottleneck. The next
  high-value direction is either a deeper reducer redesign for the 512-frame
  local-array path or a resident read/upload/calibration pipeline improvement
  that reduces the remaining `~3.25 s` light read/upload/calibrate stage without
  changing output pixels.
