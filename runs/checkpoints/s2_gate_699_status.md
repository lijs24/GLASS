# S2 Gate 699 Status

Date: 2026-06-26
Branch: `main`
Status: green

## Gate

S2-Gate 699: Resident StackEngine active-coverage contract.

## Completed

- Added resident StackEngine surface checks for active frame count versus
  positive StackRequest weights.
- Added a coverage guard requiring post-rejection coverage max to stay within
  active positive-weight frame count.
- Added coverage and weight support checks against
  `dq_provenance_summary.post_rejection_pixels`.
- Preserved the precomputed-statistics contract path so resident runs can avoid
  rereading full maps for these checks.
- Added a negative unit test that fails the contract when active count,
  coverage max, coverage support, and weight support drift.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_stack_surface.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests/test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline tests/test_stack_engine_contract.py::test_stack_engine_contract_classifies_resident_stack_surface_contract`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --out C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\gate699_active_coverage_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\gate699_active_coverage_mainline_audit.md`
- `.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate698_default_prestart\runs_20260627_090000\default_prestart_candidate --candidate-run C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate --out C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\gate699_active_coverage_vs_gate698_ab.json --markdown C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\gate699_active_coverage_vs_gate698_ab.md`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused resident surface tests: `4 passed`.
- Focused resident/default tests: `3 passed`.
- Full pytest: `1444 passed in 70.16 s`.

## Real 200-Light Result

- Candidate run:
  `C:\glass_runs\phase2_s2_gate699_resident_surface_active_coverage\runs_20260627_100000\active_coverage_contract_candidate`
- Input lights: `200`
- Active/masked frames: `193 / 7`
- Mainline audit: passed.
- A/B versus Gate698: passed.
- Elapsed ratio versus Gate698: `0.9818270795336204`.
- Worst component ratio: `0.9861023082024485`.
- Component-ratio failures: `0`.
- All six tracked integration FITS hashes matched Gate698.

## Contract Evidence

- `active_frame_count_matches_positive_weights`: passed with `193` active
  frames and `193` positive weights.
- `coverage_max_within_active_frame_count`: passed with coverage max `193.0`.
- `coverage_positive_pixels_match_post_rejection_pixels`: passed with
  `61651200` pixels.
- `weight_positive_pixels_match_post_rejection_pixels`: passed with `61651200`
  pixels.
- `valid_samples_after_rejection`: `11761072908`.
- `rejected_samples`: `47540364`.

## Timing

- `resident_light_read_upload_calibrate`: `3.033154399949126 s`
- `resident_registration_warp`: `0.26309880055487156 s`
- `resident_local_normalization`: `0.3593616000143811 s`
- `resident_integration`: `3.279866800061427 s`
- `resident_output_write`: `0.27349980000872165 s`
- `total_elapsed_s`: `11.957288500037976 s`

## CUDA

- CUDA was available for the real validation run.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- This gate did not require a native CUDA rebuild because it changes the
  Python resident contract layer and tests only.

## Known Limitations

- This is a correctness and auditability gate, not a speed optimization.
- It does not change calibration, registration, warp, local normalization,
  rejection thresholds, integration math, or CUDA kernels.
- The new checks depend on resident provenance being present for full runtime
  enforcement; legacy direct builder calls without those fields keep the
  existing compatibility behavior where applicable.

## Next Step

S2-Gate 700 should return to a substantive runtime or algorithm target:
resident registration/warp batching, reduced host/device orchestration, or a
larger resident reducer architecture change with real 200-light A/B evidence.

## Clean-Room

Compliant. The work uses GLASS-owned DQ/mask contracts, resident artifacts,
tests, and user-owned 200-light benchmark outputs. It does not inspect, copy,
summarize, or rework external proprietary implementation source, and it does
not modify input image directories.
