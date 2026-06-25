# S2 Gate 687 Status: Resident Hardened No-Rejection Accumulation Branch

## Gate

- Gate: S2-Gate 687
- Status: passed
- Date: 2026-06-27
- Scope: resident CUDA hardened winsorized integration reducer

## Completed

- Split the resident hardened winsorized CUDA final accumulation path after
  `allow_rejection` is known.
- Added a no-rejection accumulation branch that skips per-sample low/high
  threshold checks when the existing rejection guard has already disabled
  rejection.
- Preserved the previous frame-axis accumulation order and weighting semantics
  for unit-positive mask-scan, active-index/reuse, and weighted fallback paths.
- Added native profile fields:
  - `rejection_guard_no_reject_accumulation_branch_enabled`
  - `rejection_guard_no_reject_accumulation_model`
- Updated CUDA parity coverage, integration docs, validation notes, and the
  algorithm independence log.

## Commands Run

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && ".venv\Scripts\cmake.exe" --build build --target _glass_cuda_native --config Release'`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "hardened_winsorized_sigma"`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_minimal_output_master_only`
- `.venv\Scripts\python.exe -m ruff check tests/test_cuda_resident_stack.py`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch --out C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_mainline_audit.json --fail-on-not-green`
- `.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow --candidate-run C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch --out C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_regression_gate.md --fail-on-failure`
- Direct SHA256 and array compare script for the six integration FITS outputs.

## Test Results

- Native CUDA build: passed.
- Focused CUDA hardened winsorized tests: `20 passed, 57 deselected in 3.11 s`.
- Focused resident CLI hardened tests: `2 passed in 0.90 s`.
- Ruff: passed.
- Full pytest: `1426 passed in 66.99 s`.
- Phase 2 mainline audit: passed with failed checks `[]`.
- Resident regression gate versus Gate686: passed with elapsed ratio
  `0.9889038261696533`.

## Real 200-Light Validation

- Candidate run:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow`
- Frame masks: `200` planned, `193` active, `7` masked.
- Total elapsed:
  - Gate686: `12.344183000386693 s`
  - Gate687: `12.207209800020792 s`
- Resident integration:
  - Gate686: `3.2561724999686703 s`
  - Gate687: `3.234628599951975 s`
- Native hardened total:
  - Gate686: `3.256090199924074 s`
  - Gate687: `3.2345450000138953 s`
- Native kernel sync:
  - Gate686: `3.1232872 s`
  - Gate687: `3.1146121 s`
- Candidate profile:
  - `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`
  - `unit_positive_weight_frame_count=193`
  - `unit_positive_weight_mask_bytes=200`
  - `rejection_guard_no_reject_accumulation_branch_enabled=true`

## Output Agreement

- Direct FITS SHA256 compare: passed for all six outputs.
- Direct array compare: passed for all six outputs.
- Compared outputs:
  - `resident_master_H.fits`
  - `resident_weight_map_H.fits`
  - `resident_coverage_map_H.fits`
  - `resident_low_rejection_map_H.fits`
  - `resident_high_rejection_map_H.fits`
  - `resident_dq_map_H.fits`
- All array diffs had `max_abs=0.0`, `rms=0.0`, and `nonzero_diff_pixels=0`.

## Artifacts

- Runtime compare:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_runtime_compare.json`
- Runtime compare markdown:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_runtime_compare.md`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_regression_gate.json`
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_mainline_audit.json`
- Hash compare:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_output_hash_compare.json`
- Array compare:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\gate687_output_array_compare.json`

## CUDA

- CUDA available: yes.
- Native extension target `_glass_cuda_native` built successfully.
- Build environment: Visual Studio 2022 Build Tools plus CUDA Toolkit 13.2.
- Build warnings: existing CUDA/MSVC header encoding and include warnings only.

## Known Limitations

- This is a modest final-accumulation branch cleanup, not the final scalable
  cooperative or segmented reducer.
- The dominant resident integration cost remains median/IQR order-statistic
  work and repeated frame-axis scans.
- Single-run total elapsed timing still includes external storage/cache and
  scheduler variance.

## Next Step

- Continue the Phase 2 mainline with a larger resident CUDA integration
  improvement, preferably a deterministic cooperative/segmented reducer, or
  return to native H2D/calibrate overlap if the reducer redesign is too large
  for one gate.

## Clean-Room Compliance

- Compliant.
- This gate uses GLASS-owned CUDA kernels, GLASS tests, and user-owned benchmark
  artifacts only.
- No external proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
