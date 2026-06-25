# S2-Gate 689 Status: Resident Matrix-Warp Identity Bypass

## Gate

- Gate: S2-Gate 689
- Theme: resident registration/warp mainline optimization
- Status: passed

## Completed

- Added `_matrix_is_identity` for exact 3x3 identity transform detection.
- Updated `_apply_resident_registration_matrix_batch` to return
  `identity_bypass` for identity matrices and to remove those frames from
  native batch warp inputs.
- Added timing/evidence fields:
  - `input_frame_count`
  - `identity_bypass_frame_count`
  - `identity_bypass_model=skip_resampling_preserve_resident_frame`
- Updated triangle registration warp call sites so `identity_bypass` frames are
  not added to `warped_frame_indices`. The existing full-coverage accumulator
  therefore accounts for positive-weight bypassed frames as unwarped frames.
- Added resident artifact fields:
  - `triangle_warp_identity_bypass_frame_count`
  - `triangle_warp_identity_bypass_model`
- Added focused tests proving mixed identity/non-identity batches filter only
  the non-identity matrices into native warp and all-identity batches avoid
  native warp calls entirely.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "registration_matrix_batch"`
- `.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_cuda.py tests/test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "registration_matrix_batch or triangle_warp_batch or fused_matrix or resident_result_contract or sample_closure"`
- `.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py -k "fused_matrix_warped_mean or batch_lanczos3 or warp_coverage"`
- `.venv\Scripts\python.exe -m pytest -q tests/test_phase2_mainline_audit.py`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default --out C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_mainline_audit.json --fail-on-not-green`
- `.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch --candidate-run C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default --out C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_regression_gate.md --fail-on-failure`
- Direct Python FITS SHA256/array comparison for the six integration outputs.
- `.venv\Scripts\glass.exe resident-result-contract --run C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default --out C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_resident_result_contract.json --markdown C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_resident_result_contract.md --pixel-verify --fail-on-failed`
- `.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default --out C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_pipeline_contract.md --pixel-verify`
- `.venv\Scripts\python.exe -m pytest -q`
- `nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader`

## Test Results

- Focused resident matrix-batch tests:
  `6 passed, 132 deselected`.
- Broader resident CUDA registration/contract tests:
  `14 passed, 124 deselected`.
- Focused CUDA resident stack warp/fused tests:
  `4 passed, 73 deselected`.
- Phase 2 mainline audit tests:
  `8 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1431 passed in 66.66 s`.

## Real 200-Light Validation

- Candidate run:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch`
- Phase 2 mainline audit: passed with failed checks `[]`.
- Resident regression gate: passed with failed checks `[]`.
- Regression elapsed ratio versus Gate687: `1.02595343286861`.
- Input lights: `200`.
- Active/masked frames: `193 / 7`.
- Direct FITS SHA256 compare: passed for all six integration outputs.
- Direct array compare: passed for all six integration outputs.
- Resident result contract with pixel verification: passed.
- Pipeline contract with pixel verification: passed.

## Timing

- Gate687 total elapsed: `12.207209800020792 s`.
- Gate689 total elapsed: `12.524028800078668 s`.
- Gate689 resident component timing:
  - light read/upload/calibrate: `3.5127374000148848 s`
  - registration/warp: `0.278870000038296 s`
  - local normalization: `0.36278890003450215 s`
  - integration: `3.2666022999910638 s`
  - output write: `0.26949790003709495 s`
- Gate689 recorded:
  - `triangle_warp_batch_frame_count=192`
  - `triangle_warp_identity_bypass_frame_count=0`
  - `triangle_warp_batch_fallback_frame_count=0`
  - `triangle_warp_batch_timing_model=native_chunked_batch_warp_scatter_one_sync`

## Artifacts

- Timing summary:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_timing_summary.json`
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_mainline_audit.json`
- Regression gate:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_regression_gate.json`
- Regression gate markdown:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_regression_gate.md`
- Output compare:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_output_compare.json`
- Resident result contract:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_resident_result_contract.json`
- Pipeline contract:
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\gate689_pipeline_contract.json`

## CUDA

- CUDA available to GLASS: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Driver: 596.21.
- VRAM reported by `nvidia-smi`: 97887 MiB.

## Known Limitations

- The current M38 200-light data did not contain identity moving warps, so this
  gate validates output parity and future zero-motion behavior rather than a
  speedup on this data set.
- This gate does not change star detection, transform fitting, interpolation
  math for non-identity matrices, local normalization, rejection, DQ flags, or
  integration math.
- The Gate689 elapsed ratio is slower than Gate687 by about `2.6%`, while
  direct output comparison is bitwise identical. This is recorded as normal
  single-run storage/GPU scheduling variance, not a numerical regression.

## Next Step

- Continue the resident registration/warp mainline with a larger optimization
  that affects the current 200-light data set, such as reducing batch warp
  orchestration/synchronization, or return to a deterministic cooperative
  hardened reducer for the remaining integration cost.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned resident matrix and warp wrappers,
  GLASS tests, and user-owned benchmark artifacts only.
- No external or proprietary implementation source was inspected or used.
- Original image directories were not modified.
