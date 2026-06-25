# S2-Gate 665 Status: Deterministic Resident Star-Protected Source-DQ Catalog

## Gate

S2-Gate 665

## Completed

- Wired the existing resident `--resident-star-catalog-deterministic` control into the opt-in `cosmetic_star_cuda` source-DQ star catalog path.
- Added deterministic catalog provenance to:
  - per-frame source-DQ threshold info;
  - source-DQ rows and component summaries;
  - `resident_io_pipeline`;
  - `resident_source_dq_strategy.json`.
- Preserved default behavior: resident inline source-DQ still defaults to `off`, and deterministic source-DQ catalogs are active only when `cosmetic_star_cuda` and `--resident-star-catalog-deterministic` are selected.
- Ran focused tests, real 200-light deterministic repeat validation, regression/determinism gate, ruff, and full pytest.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py::test_inline_star_protected_cosmetic_thresholds_from_resident_stack_records_catalog tests\test_resident_source_dq_strategy.py::test_resident_source_dq_strategy_records_cuda_star_protected_inline_detector tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_accepts_inline_star_protected_cosmetic_cuda_source_dq`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_star_cuda --resident-inline-source-dq-policy conservative --resident-inline-source-dq-admission active_registered --resident-star-catalog-deterministic --resident-mainline-framework-gate strict --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 0 --resident-mainline-min-source-dq-applied-samples 0 --out C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_a`
- Same command for:
  `C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_b`
- `.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_a --candidate-run C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_b --out C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\gate665_repeat_regression.json --markdown C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\gate665_repeat_regression.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10`
- `.venv\Scripts\python.exe -m ruff check .`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_active_registered_inline_cosmetic_cuda_skips_excluded_frame -vv`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_accepts_inline_star_protected_cosmetic_cuda_source_dq tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_active_registered_inline_cosmetic_cuda_skips_excluded_frame`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused source-DQ/strategy/resident CUDA tests: `3 passed`.
- Ruff: `All checks passed`.
- First full pytest attempt: `1 failed, 1401 passed`; the failing frame-mask test passed when rerun directly and in adjacent order.
- Final full pytest rerun: `1402 passed in 62.53s`.

## Real 200-Light Results

- Run A:
  `C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_a`
- Run B:
  `C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500\det_star_cuda_b`
- Run A elapsed: `19.866321900160983 s`.
- Run B elapsed: `19.738215200253762 s`.
- Black-box reference elapsed used for speedup: `1092.541 s`.
- Run A speedup versus black-box reference: `54.99562495490026x`.
- Run B speedup versus black-box reference: `55.35257156005457x`.
- Run A component timing:
  - `resident_light_read_upload_calibrate=8.983780600014143 s`
  - `resident_registration_warp=0.259741400484927 s`
  - `resident_local_normalization=0.4077763999812305 s`
  - `resident_integration=3.3404862000606954 s`
  - `resident_output_write=0.3155267999973148 s`
- Run B component timing:
  - `resident_light_read_upload_calibrate=8.872635599924251 s`
  - `resident_registration_warp=0.2576664995867759 s`
  - `resident_local_normalization=0.363944899989292 s`
  - `resident_integration=3.3117685000179335 s`
  - `resident_output_write=0.2832134000491351 s`

## Source-DQ Repeat Determinism

- Run A source-DQ invalid samples: `147013`.
- Run B source-DQ invalid samples: `147013`.
- Run A/B hot pixels: `98216`.
- Run A/B cold pixels: `48797`.
- Run A/B status counts:
  - `applied=10`
  - `skipped_high_invalid_fraction=183`
  - `skipped_admission_policy=7`
- Run A/B native methods:
  - `ResidentCalibratedStack.apply_star_protected_isolated_cosmetic_threshold_mask_frames`
  - `ResidentCalibratedStack.count_star_protected_isolated_cosmetic_threshold_mask_frames`
- Run A/B artifacts record:
  - `resident_inline_source_dq_star_catalog_deterministic=true`
  - `resident_cuda_star_grid_top_nms_candidates_deterministic`

## Regression Gate

- `resident-regression-gate`: passed.
- Failed checks: `[]`.
- Candidate/baseline elapsed ratio: `0.9935515642728923`.
- Determinism summary:
  - `output_difference_count=0`
  - `output_numerical_drift_count=0`
  - `registration_difference_count=0`
  - `frame_accounting_difference_count=0`
  - `artifact_difference_count=0`

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: available to GLASS.

## Known Limits

- `cosmetic_star_cuda` remains opt-in and is not promoted to the default science route.
- Deterministic catalog mode fixes repeat determinism for this opt-in route, but default promotion still requires science-policy comparison against the default route and continued StackEngine/DQ contract coverage.
- A transient full-suite frame-mask test failure was observed once and did not reproduce in direct, adjacent-order, or final full-suite reruns.

## Next Step

- Return to default-route Phase 2 substance:
  - make StackEngine/DQ contracts cover remaining default surfaces;
  - improve read/upload/calibration overlap;
  - optimize hardened winsorized integration.

## Clean-Room Compliance

- This gate uses GLASS-owned resident CUDA catalog controls, GLASS source-DQ artifacts, GLASS tests, and user-owned benchmark outputs.
- It does not inspect, copy, summarize, or rework external/proprietary implementation source.
- Input image directories were treated as read-only.
