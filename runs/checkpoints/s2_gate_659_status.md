# S2-Gate 659 Status: Conservative Cosmetic CUDA Source-DQ Policy Profile

## Gate

S2-Gate 659.

## Completed Content

- Added `--resident-inline-source-dq-policy` to `glass run` and `glass audit`.
- Added three policy profiles:
  - `default`: `0.0001`, preserving the previous safest high-fraction guard.
  - `conservative`: `0.0003`, selected from the real 200-light guard sweep.
  - `diagnostic`: `0.02`, matching the high-coverage Gate658 impact study.
- Kept `--resident-inline-source-dq-max-invalid-fraction` as an explicit
  override over the selected policy.
- Recorded policy and effective guard in `run_timing.json`,
  `resident_source_dq_strategy.json`, and `resident_artifacts.json`.
- Added focused CLI tests for policy resolution and explicit override behavior.
- Ran real 200-light conservative policy validation and compared it to the
  Gate656 default master.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass\engine\resident_source_dq_strategy.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py::test_run_resident_inline_source_dq_policy_conservative_sets_guard tests/test_cli_smoke.py::test_run_resident_inline_source_dq_explicit_fraction_overrides_policy tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_skips_inline_cosmetic_cuda_high_fraction_guard

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_cuda --resident-inline-source-dq-max-invalid-fraction 0.001 --resident-mainline-framework-gate strict --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --out C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_guard001_strict
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_cuda --resident-inline-source-dq-max-invalid-fraction 0.0005 --resident-mainline-framework-gate strict --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --out C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_guard0005_strict
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_cuda --resident-inline-source-dq-max-invalid-fraction 0.0003 --resident-mainline-framework-gate strict --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --out C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_guard0003_strict

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_cuda --resident-inline-source-dq-policy conservative --resident-mainline-framework-gate strict --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --out C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_conservative_policy_strict
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_conservative_policy_strict --out C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\gate659_conservative_policy_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\gate659_conservative_policy_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_conservative_policy_strict\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\default_strict\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\gate659_conservative_policy_vs_gate656_default.json --glass-label "Gate659 conservative cosmetic CUDA" --reference-label "Gate656 default" --glass-coverage-map C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_conservative_policy_strict\integration\resident_coverage_map_H.fits --min-coverage 190
```

## Test Results

- Ruff over touched Python/test files: passed.
- Focused policy/default guard tests: `3 passed`.
- Real 200-light conservative policy strict run: passed.
- `phase2-mainline-audit --fail-on-not-green`: passed.
- GLASS-vs-GLASS compare completed.

## CUDA Availability

- CUDA was available for this gate.
- GPU used in this phase remains NVIDIA RTX PRO 6000 Blackwell Workstation
  Edition with about 96 GiB VRAM.

## Real 200-Light Guard Sweep

All candidates used strict `inline_cosmetic_cuda_positive` scope.

| Guard | Applied frames | All-frame invalid samples | RMS vs Gate656 default | p99 absolute diff |
| --- | ---: | ---: | ---: | ---: |
| `0.001` | `140` | `5118176` | `2.761208205607273` | `8.372343616485594` |
| `0.0005` | `47` | `1142686` | `0.8960583565176917` | `2.4001502990722656` |
| `0.0003` | `10` | `147179` | `0.5331775153760971` | `1.2427406311035156` |

## Green Conservative Profile Evidence

- Evidence root:
  `C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000`.
- Green run:
  `C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_conservative_policy_strict`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\gate659_conservative_policy_mainline_audit.json`.
- Compare:
  `C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\gate659_conservative_policy_vs_gate656_default.json`.
- Frame accounting: `200` lights, `193` active frames, `7` masked frames.
- GLASS elapsed time: `18.47093429986853 s`.
- Black-box reference elapsed time: `1092.541 s`.
- Speedup: about `59.15x`.
- Policy evidence:
  - `resident_inline_source_dq_policy=conservative`
  - `resident_inline_source_dq_policy_effective.source=policy_default`
  - `resident_inline_source_dq_max_invalid_fraction=0.0003`
  - strategy and resident artifact both record policy `conservative`.
- Source-DQ evidence:
  - `input_invalid_samples_before_rejection=147180`
  - `all_frame_input_invalid_samples_before_frame_mask=147180`
  - `applied_frame_count=10`
  - `all_frame_applied_frame_count=10`
  - status counts: `applied=10`, `skipped_high_invalid_fraction=190`

## Comparison To Gate656 Default

- Shape match: true.
- Compared pixels: `60105945`.
- Coverage fraction: `0.9749355243693554`.
- Absolute difference p50/p90/p99:
  `0.0345001220703125` / `0.17724990844726562` /
  `1.2427406311035156`.
- RMS difference: `0.5331775153760971`.
- Relative RMS difference: `0.0016775947037267229`.

## Known Limitations

- The conservative profile is still a high-fraction guard, not a star-aware
  detector.
- It reduces Gate658 policy drift but does not eliminate it.
- Default source-DQ remains off; this profile is opt-in pending star-aware or
  structure-aware source-DQ validation.

## Next Step

Implement a star-proximity or catalog-aware protection policy for resident
cosmetic CUDA source-DQ, then rerun the same 200-light profile sweep and require
positive source-DQ with lower master drift than the conservative guard alone.

## Clean-Room Compliance

This gate is derived from GLASS-owned policy resolution, resident CUDA
artifacts, source-DQ strategy artifacts, tests, and user-owned benchmark
outputs. It did not inspect, copy, summarize, or rework external or proprietary
implementation source, and it did not modify original input image directories.
