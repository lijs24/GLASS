# S2-Gate 674 Status: Resident Lifecycle Mainline Guard And Reducer A/B

## Gate

- Gate: S2-Gate 674
- Status: green
- Date: 2026-06-26

## Completed

- Promoted `resident_memory_lifecycle.json` from optional runtime evidence to a required Phase 2 mainline artifact.
- `phase2-mainline-audit` now fails unless resident CUDA runs prove:
  - transient raw staging;
  - calibrated light stack resident through integration;
  - no registered disk cache materialization;
  - valid calibrated-stack and peak memory estimates.
- `resident-regression-gate` now requires the same lifecycle contract by default.
- Added `--allow-missing-resident-memory-lifecycle` as a legacy/debug escape hatch.
- Hardened the lifecycle builder for small source-DQ/synthetic runs:
  - output FITS headers can supply shape without reading pixels;
  - `frame_accounting.json` can supply light-frame counts;
  - a conservative peak estimate is computed when no explicit runtime estimate is present.
- Ran a real 200-light active-index reducer A/B candidate and rejected it because it was slower than the paired default route.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src\\glass\\engine\\resident_memory_lifecycle.py src\\glass\\report\\phase2_mainline_audit.py src\\glass\\report\\resident_regression_gate.py src\\glass\\cli.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\engine\\resident_memory_lifecycle.py src\\glass\\report\\phase2_mainline_audit.py src\\glass\\report\\resident_regression_gate.py src\\glass\\cli.py tests\\test_phase2_mainline_audit.py tests\\test_resident_regression_gate.py tests\\test_resident_mainline_framework.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_phase2_mainline_audit.py tests\\test_resident_regression_gate.py tests\\test_resident_memory_lifecycle.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_memory_lifecycle.py tests\\test_resident_mainline_framework.py tests\\test_resident_cuda_run.py::test_cli_resident_cuda_triangle_source_dq_feeds_registration_runtime_contract tests\\test_resident_cuda_run.py::test_cli_resident_cuda_run_generates_source_dq_cache_route`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `glass run` on the real 200-light plan, default resident route:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\default_lifecycle_guard_final`
- `glass phase2-mainline-audit --fail-on-not-green` on the final default run.
- `glass resident-regression-gate --fail-on-failure` comparing the final default run against Gate673.
- `glass run` on the real 200-light plan with `GLASS_CUDA_UNIT_WEIGHT_ACTIVE_INDEX=1`:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\candidate_active_index_reducer`
- `glass resident-regression-gate --fail-on-failure` comparing the active-index candidate against its paired default run.
- `glass resident-runtime-compare` for the paired default and active-index candidate.

## Test Results

- Focused mainline/regression/lifecycle tests: `16 passed`.
- Expanded lifecycle/mainline/source-DQ focused tests: `19 passed`.
- Full pytest: `1418 passed in 64.75 s`.
- Ruff: passed.
- Py compile: passed.

## Real 200-Light Evidence

- Final default run:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\default_lifecycle_guard_final`
- Final profile summary:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\gate674_final_profile_summary.json`
- Final mainline audit:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\gate674_final_phase2_mainline_audit.json`
- Final regression versus Gate673:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\gate674_final_vs_gate673_regression.json`
- Active-index candidate regression:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\gate674_active_index_vs_default_regression.json`
- Runtime compare:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\gate674_runtime_compare.json`

Final default metrics:

- Input lights: `200`
- Active/masked frames: `193/7`
- Total elapsed: `12.066693499917164 s`
- Light read/upload/calibrate: `3.2876758000347763 s`
- Resident registration/warp: `0.26390850043389946 s`
- Resident local normalization: `0.35589420003816485 s`
- Resident integration: `3.323810000088997 s`
- Output write: `0.26571329997386783 s`
- Estimated calibrated resident stack: `45.93372344970703 GiB`
- Estimated peak: `49.608429938554764 GiB`
- Raw all frames resident: `false`
- Calibrated stack resident: `true`
- Registered cache materialized on disk: `false`

Active-index reducer A/B:

- Candidate path:
  `C:\\glass_runs\\phase2_s2_gate674_lifecycle_mainline\\runs_20260626_080000\\candidate_active_index_reducer`
- Regression status: passed, failed checks `[]`
- Candidate/default total ratio: `1.0181637343039516`
- Candidate/default integration ratio: `1.0355348444807078`
- Decision: not promoted.

## CUDA

- CUDA was available.
- GPU observed in prior Gate673/Gate674 validation: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability `12.0`, VRAM `97886 MiB`, driver `596.21`.

## Known Limitations

- `resident_memory_lifecycle.json` is still an estimated lifecycle contract, not a live CUDA allocator trace.
- Active-index reducer selection is numerically safe on this data but slower for the current `193/200` active-frame case.
- The next performance work should target resident integration reducer internals or light upload/calibration overlap, not simple queue-depth increases.

## Clean-Room

- This gate used GLASS-owned code, GLASS tests, and user-owned benchmark artifacts.
- No proprietary WBPP/PJSR source code was read, copied, summarized, or reworked.

## Next Step

- Return to substantive Phase 2 execution work: either implement a faster resident hardened reducer strategy or improve overlap in the I/O/H2D/calibration pipeline while preserving the lifecycle guard.
