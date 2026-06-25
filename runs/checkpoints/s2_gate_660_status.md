# S2-Gate 660 Status: Active-Registered Cosmetic CUDA Source-DQ Admission

## Gate

S2-Gate 660.

## Completed Content

- Added `--resident-inline-source-dq-admission` to `glass run` and
  `glass audit`.
- Added two admission modes:
  - `all`: legacy behavior.
  - `active_registered`: apply deferred inline cosmetic CUDA source-DQ only to
    frames still admitted by registration/current positive-weight state.
- Filtered deferred cosmetic CUDA source-DQ candidates before native batch
  application, so masked frames do not run the native threshold apply path.
- Added auditable `skipped_admission_policy` source-DQ rows for masked frames.
- Recorded admission policy, target scope, candidate count, target count, and
  skipped-admission count in resident timing/strategy/artifacts.
- Added focused resident CUDA tests for the normal deferred path and a
  manual-excluded frame skipped by active-registered admission.
- Ran a real 200-light strict validation using the Gate659 conservative profile
  plus active-registered admission.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq.py src\glass\engine\resident_source_dq_strategy.py tests\test_resident_cuda_run.py

.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_defers_inline_cosmetic_cuda_source_dq_until_after_registration tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_active_registered_inline_cosmetic_cuda_skips_excluded_frame
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_run_resident_inline_source_dq_policy_conservative_sets_guard tests/test_cli_smoke.py::test_run_resident_inline_source_dq_explicit_fraction_overrides_policy tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_skips_inline_cosmetic_cuda_high_fraction_guard tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_defers_inline_cosmetic_cuda_source_dq_until_after_registration tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_active_registered_inline_cosmetic_cuda_skips_excluded_frame
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_source_dq.py tests/test_resident_source_dq_strategy.py tests/test_resident_source_dq_contract.py tests/test_resident_mainline_framework.py::test_resident_mainline_framework_inline_cosmetic_cuda_scope_passes

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_cuda --resident-inline-source-dq-policy conservative --resident-inline-source-dq-admission active_registered --resident-mainline-framework-gate strict --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --out C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict --out C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\gate660_active_registered_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\gate660_active_registered_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_conservative_policy_strict\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\gate660_active_registered_vs_gate659_conservative.json --glass-label "Gate660 active registered cosmetic CUDA" --reference-label "Gate659 conservative cosmetic CUDA" --glass-coverage-map C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict\integration\resident_coverage_map_H.fits --min-coverage 190

.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff over touched Python/test files: passed.
- Focused deferred/admission CUDA tests: `2 passed`.
- Focused CLI/source-DQ/resident framework tests: `28 passed`.
- Full pytest: `1386 passed in 61.95s`.
- Real 200-light strict resident CUDA run: passed.
- `phase2-mainline-audit --fail-on-not-green`: passed.
- Gate660-vs-Gate659 GLASS compare: passed and bit-identical.

## CUDA Availability

- CUDA was available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM reported to GLASS: `97886 MiB`.

## Real 200-Light Evidence

- Evidence root:
  `C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412`.
- Green run:
  `C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\gate660_active_registered_mainline_audit.json`.
- Compare:
  `C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\gate660_active_registered_vs_gate659_conservative.json`.
- Frame accounting: `200` lights, `193` active frames, `7` masked frames.
- GLASS `total_elapsed_s`: `18.553858600207604 s`.
- Resident calibration/integration stage: `16.83023530000355 s`.
- Black-box reference elapsed time: `1092.541 s`.
- Speedup: about `58.88x`.
- Admission evidence:
  - `resident_inline_source_dq_admission=active_registered`
  - deferred candidates: `200`
  - deferred targets: `193`
  - skipped by admission: `7`
- Source-DQ evidence:
  - `input_invalid_samples_before_rejection=147179`
  - `all_frame_input_invalid_samples_before_frame_mask=147179`
  - `applied_invalid_samples=147179`
  - status counts: `applied=10`, `skipped_high_invalid_fraction=183`,
    `skipped_admission_policy=7`

## Comparison To Gate659 Conservative

- Shape match: true.
- Compared pixels at coverage >= `190`: `60105945`.
- Coverage fraction: `0.9749355243693554`.
- Absolute difference p50/p90/p99/p99.9: all `0.0`.
- Max absolute difference: `0.0`.
- RMS difference: `0.0`.

## Known Limitations

- This gate hardens deferred source-DQ admission and removes masked-frame native
  apply work. It is not a true star-aware cosmetic detector.
- Inline cosmetic CUDA source-DQ remains opt-in and is not promoted to the
  default science route.
- The cosmetic threshold formula is unchanged.

## Next Step

Implement star/structure-aware inline cosmetic CUDA source-DQ protection or a
proper catalog-aware detector, then rerun the same 200-light conservative
profile and compare against both Gate660 and the default science route.

## Clean-Room Compliance

This gate is derived from GLASS-owned resident CUDA source-DQ execution,
resident frame-mask semantics, GLASS tests, and user-owned benchmark outputs. It
did not inspect, copy, summarize, or rework external or proprietary
implementation source, and it did not modify original input image directories.
