# S2-Gate 658 Status: Real Inline Cosmetic CUDA Source-DQ Mainline Scope

## Gate

S2-Gate 658.

## Completed Content

- Added `inline_cosmetic_cuda_positive` as a resident mainline framework scope.
- The scope requires positive source-DQ invalid/applied samples, resident inline
  cosmetic CUDA source evidence, and resident in-memory mask streaming.
- `resident_mainline_framework` now aggregates source-DQ source/count maps from
  execution groups when the top-level summary does not carry those maps.
- `resident_registration_runtime_contract` now distinguishes active integration
  DQ counts from all-frame registration-row DQ audit counts. Registration audit
  can close against either active or all-frame totals, while row totals,
  pre-registration visible samples, post-registration deferred samples, and
  required-not-visible samples still have to match.
- Added focused tests for inline cosmetic CUDA scope pass/fail and all-frame
  source-DQ registration accounting.
- Ran a real 200-light resident CUDA `cosmetic_cuda` source-DQ positive run.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_mainline_framework.py src\glass\engine\resident_registration_runtime_contract.py src\glass\cli.py tests\test_resident_mainline_framework.py tests\test_resident_registration_runtime_contract.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py::test_resident_mainline_framework_inline_cosmetic_cuda_scope_passes tests/test_resident_mainline_framework.py::test_resident_mainline_framework_inline_cosmetic_cuda_scope_rejects_sidecar_only tests/test_resident_registration_runtime_contract.py::test_resident_registration_runtime_contract_allows_registration_all_frame_source_dq

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-inline-source-dq cosmetic_cuda --resident-inline-source-dq-max-invalid-fraction 0.02 --resident-mainline-framework-gate strict --resident-mainline-framework-scope inline_cosmetic_cuda_positive --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-mainline-min-source-dq-invalid-samples 1 --resident-mainline-min-source-dq-applied-samples 1 --out C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\inline_cosmetic_cuda_positive_strict_green
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\inline_cosmetic_cuda_positive_strict_green --out C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\gate658_inline_cosmetic_cuda_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\gate658_inline_cosmetic_cuda_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\inline_cosmetic_cuda_positive_strict_green\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate656_registration_source_dq_input_audit\runs_20260625_212001\default_strict\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\gate658_inline_cosmetic_cuda_vs_gate656_default.json --glass-label "Gate658 inline cosmetic CUDA" --reference-label "Gate656 default" --glass-coverage-map C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\inline_cosmetic_cuda_positive_strict_green\integration\resident_coverage_map_H.fits --min-coverage 190

.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_mainline_framework.py src\glass\engine\resident_registration_runtime_contract.py src\glass\cli.py tests\test_resident_mainline_framework.py tests\test_resident_registration_runtime_contract.py
git diff --check
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_mainline_framework.py::test_resident_mainline_framework_inline_cosmetic_cuda_scope_passes tests/test_resident_mainline_framework.py::test_resident_mainline_framework_inline_cosmetic_cuda_scope_rejects_sidecar_only tests/test_resident_registration_runtime_contract.py::test_resident_registration_runtime_contract_allows_registration_all_frame_source_dq
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff over touched files: passed.
- Focused resident mainline/runtime-contract tests: `3 passed`.
- Full pytest: `1383 passed in 61.17s`.
- `git diff --check`: passed.
- Real 200-light inline cosmetic CUDA strict run: passed.
- `phase2-mainline-audit --fail-on-not-green`: passed.
- GLASS-vs-GLASS compare completed.

## CUDA Availability

- CUDA was available for this gate.
- GPU used in this phase remains NVIDIA RTX PRO 6000 Blackwell Workstation
  Edition with about 96 GiB VRAM.

## Real 200-Light Evidence

- Evidence root:
  `C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737`.
- Green run:
  `C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\inline_cosmetic_cuda_positive_strict_green`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\gate658_inline_cosmetic_cuda_mainline_audit.json`.
- Compare:
  `C:\glass_runs\phase2_s2_gate658_inline_cosmetic_cuda_real\runs_20260625_214737\gate658_inline_cosmetic_cuda_vs_gate656_default.json`.
- Frame accounting: `200` lights, `193` active frames, `7` masked frames.
- GLASS elapsed time: `18.911628100206144 s`.
- Black-box reference elapsed time: `1092.541 s`.
- Speedup: about `57.78x`.

## Source-DQ Evidence

- `resident_mainline_framework.json`: passed with
  `framework_scope=inline_cosmetic_cuda_positive`.
- `resident_registration_runtime_contract.json`: passed and recorded
  `registration_matches_all_frame_source_dq=true`.
- Active integration source-DQ counts:
  - `input_invalid_samples_before_rejection=9532598`
  - `applied_invalid_samples=9532598`
- All-frame registration/audit source-DQ counts:
  - `all_frame_input_invalid_samples_before_frame_mask=10258384`
  - `all_frame_applied_invalid_samples=10258384`
- Source counts:
  - `resident_post_registration_pre_warp_cosmetic_cuda=192`
  - `resident_post_registration_pre_warp_cosmetic_cuda_flush=8`
- Deferred application:
  - `resident_inline_source_dq_deferred_frame_count=200`
  - `resident_inline_source_dq_deferred_applied_frame_count=200`
  - `resident_inline_source_dq_deferred_pending_frame_count=0`

## Runtime and Comparison

- Component timing:
  - `resident_light_read_upload_calibrate=7.699204199947417 s`
  - `resident_registration_warp=0.2707780001219362 s`
  - `resident_local_normalization=0.35652599995955825 s`
  - `resident_integration=3.2230436999816447 s`
  - `resident_output_write=0.2761841000756249 s`
- Compare to Gate656 default with coverage >= `190`:
  - shape match: true
  - compared pixels: `60106168`
  - coverage fraction: `0.9749391414927853`
  - absolute difference p50/p90/p99:
    `0.45581817626953125` / `2.0315895080566406` /
    `10.900529212951653`
  - RMS difference: `4.465267226951517`
  - relative RMS difference: `0.014049558858932804`

## Failure Fixed During Gate

- The first real run failed `resident_registration_runtime_contract` because
  registration source-DQ rows used all-frame totals while
  `resident_source_dq_execution.summary` reported active integration totals.
- The second real run passed the registration runtime contract but failed the
  new mainline scope because inline source counts were present in execution
  groups, not in the aggregate summary.
- Both failures were fixed with focused contract changes and tests before the
  final green run.

## Known Limitations

- `cosmetic_cuda` remains opt-in. With a `0.02` guard it invalidates millions of
  samples, and the master drifts versus the default route as expected.
- This gate proves execution, accounting, and strict contracts. It does not
  prove that the current detector is scientifically safe for default use.
- A star-aware or structure-aware cosmetic CUDA policy is still required before
  inline source-DQ should be considered for default science output.

## Next Step

Build a conservative star-aware/structure-aware resident cosmetic CUDA policy,
then rerun the same 200-light A/B to reduce master drift while keeping positive
source-DQ execution and strict accounting.

## Clean-Room Compliance

This gate is derived from GLASS-owned resident CUDA source-DQ execution,
runtime contracts, tests, and user-owned benchmark outputs. It did not inspect,
copy, summarize, or rework external or proprietary implementation source, and
it did not modify original input image directories.
