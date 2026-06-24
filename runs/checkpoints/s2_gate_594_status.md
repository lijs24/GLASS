# S2 Gate 594 Status: Resident Master-Cache Rejection Policy

## Gate

- Gate: S2-Gate 594
- Title: Resident Master-Cache Rejection Policy
- Date: 2026-06-24
- Status: passed

## Completed

- Resident master-cache construction now honors `CalibrationPolicy.master_rejection`.
- Default active master rejection, including `winsorized_sigma`, routes to `CPUStackEngine` instead of the resident CUDA mean-only fast path.
- Explicit no-rejection policies still use the resident CUDA mean builder when available.
- Resident master-cache metrics and top-level stats now report actual `master_rejection_applied` and dispatch reasons.
- Resident master-cache builder id was bumped to `resident_stack_engine_resident_cuda_policy_master_cache_v2` so older no-rejection caches are not silently reused.
- Added/updated resident master-cache tests for active rejection, no-rejection CUDA mean dispatch, and raw-u16 mean dispatch.
- Updated Phase 2 plan and algorithm-source log.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_master_stack_engine.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py tests\test_resident_calibration_artifacts.py tests\test_resident_cuda_run.py -k "resident_master_cache or calibration_artifacts or master_cache"`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py -k "calibration_artifacts or resident_native_calibration"`
- Synthetic validation script writing `C:\glass_runs\phase2_s2_gate594_resident_master_rejection\gate594_validation_summary.json`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused resident master tests: `3 passed`
- Focused resident/calibration/pipeline tests: `9 passed, 102 deselected` and `2 passed, 44 deselected`
- Full pytest: `1264 passed in 66.82s`
- Ruff: `All checks passed`

## Synthetic Validation

- Artifact directory: `C:\glass_runs\phase2_s2_gate594_resident_master_rejection`
- Validation summary: `C:\glass_runs\phase2_s2_gate594_resident_master_rejection\gate594_validation_summary.json`
- Dataset: `20` bias, `20` dark, `20` flat frames, each `96x96`, one extreme outlier per calibration group.
- No-rejection policy:
  - elapsed: `0.38482600008137524 s`
  - bias mean: `60.0`
  - dark mean after bias subtraction: `140.0`
  - `master_rejection_applied=none`
- Winsorized policy:
  - elapsed: `1.1001293000299484 s`
  - bias mean: `10.0`
  - dark mean after bias subtraction: `90.0`
  - `master_rejection_applied=winsorized_sigma`
- Checks passed: `none_applied_none`, `winsorized_applied_winsorized`, `winsorized_bias_rejects_outlier`, `none_bias_includes_outlier`, `cache_builder_is_v2`, `all_finite`

## CUDA

- CUDA available: yes
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Native backend: true

## Known Limitations

- The corrected default resident master-cache path can make cold-cache real-data runs slower because robust master rejection currently falls back to `CPUStackEngine`.
- This gate did not run the full real 200-light A/B. The synthetic validation proves result semantics and bounded performance behavior for the changed path; the next gate should run the real 200-light A/B with the v2 cache builder and quantify cold-cache cost.
- CUDA robust master-frame reduction is still future work.

## Next Step

- Run the real 200-light A/B with the corrected v2 resident master cache.
- If cold-cache master rejection dominates runtime, implement a CUDA resident robust master reduction or an optimized tiled CPU reduction as the next substantive performance gate.

## Clean-Room Compliance

- This gate uses GLASS-owned StackEngine code and GLASS-generated synthetic FITS data.
- No proprietary or external implementation source was read, copied, summarized, or reworked.
- Input image directories remain read-only.
