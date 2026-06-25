# S2-Gate 653 Status: Resident Runtime State Sync

## Gate

- Gate: S2-Gate 653.
- Status: passed.
- Date: 2026-06-25.
- Scope: fix resident strict postcondition state synchronization after the
  Gate652 component-ledger hardening, and use a small real 200-light wave-fill
  A/B as runtime evidence.

## Completed Content

- Fixed `resident_mainline_framework` runtime behavior in `src/glass/cli.py`.
- The helper now writes the current in-memory `RunState` to `run_state.json`
  before invoking `resident_mainline_framework`, but only when that state has
  completed stages or artifacts.
- This prevents strict resident runs from failing the recomputed
  `resident_stage_ledger_component_contract` because `run_state.json` was
  stale while the in-memory state already contained complete resident stages.
- Empty diagnostic helper states no longer overwrite an existing green
  `run_state.json`.
- Added a regression test that reproduces the stale-disk-state condition.
- Updated:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/validation.md`;
  - `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py tests\test_resident_mainline_framework.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_mainline_framework.py
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\default_25us --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\candidate_10us --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10 --resident-native-completion-wave-fill-us 10
.\.venv\Scripts\glass.exe resident-regression-gate --candidate-run C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\candidate_10us --baseline-run C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\default_25us --out C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_regression_candidate10_vs_default25.json --markdown C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_regression_candidate10_vs_default25.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\candidate_10us --out C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_candidate10_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_candidate10_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\default_25us --out C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_default25_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_default25_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor
```

## Test Results

- Ruff over touched Python files: passed.
- Focused resident-mainline tests: `11 passed in 0.57 s`.
- Full pytest: `1370 passed in 61.51 s`.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000`.
- Default run:
  `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\default_25us`.
- Candidate run:
  `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\candidate_10us`.
- Both runs completed strict resident CUDA postconditions.
- Both runs passed `phase2-mainline-audit --fail-on-not-green`.
- Input lights: `200`.
- Active frames: `193`.
- Masked frames: `7`.
- Candidate-vs-default regression gate: passed.
- Elapsed ratio: `0.9981548371313056`.
- Failed regression checks: none.

## Wave-Fill A/B Result

Default 25us:

- Total elapsed: `11.252502299728803 s`.
- Parent `resident_calibration_integration`: `9.577831499977037 s`.
- `light_read_upload_calibrate`: `3.3043448000680655 s`.
- `resident_integration`: `3.2402869999641553 s`.
- Native calibration total: `1.9788569 s`.
- Wave-fill wait: `0.19675710000000002 s`.
- Wave count: `101`.
- Timeout count: `10`.

Candidate 10us:

- Total elapsed: `11.231739600305445 s`.
- Parent `resident_calibration_integration`: `9.573600300005637 s`.
- `light_read_upload_calibrate`: `3.2716652000090107 s`.
- `resident_integration`: `3.278101100004278 s`.
- Native calibration total: `1.957667 s`.
- Wave-fill wait: `0.1923904 s`.
- Wave count: `103`.
- Timeout count: `14`.

Decision:

- Do not promote `10us` to the default.
- The total-time improvement is only about `0.18%`, while integration time
  moved slightly in the wrong direction. This is noise-scale on the 200-light
  benchmark.
- Default remains `throughput-v4-native-completion` with `25us` wave-fill.

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`,
  compute capability `12.0`, VRAM `97886 MiB`, driver `596.21`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\default_25us`
- `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\candidate_10us`
- `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_regression_candidate10_vs_default25.json`
- `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_regression_candidate10_vs_default25.md`
- `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_default25_mainline_audit.json`
- `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000\gate653_candidate10_mainline_audit.json`

## Known Limitations

- This gate fixes runtime postcondition correctness; it does not change pixel
  math, CUDA kernels, frame admission, DQ semantics, output maps, or default
  runtime preset values.
- The 10us wave-fill experiment is a two-run A/B only and is not strong enough
  to justify a default change.
- The largest remaining substantive optimization targets are still
  `light_read_upload_calibrate` and `resident_integration`.

## Next Step

Return to hot-path execution work:

- reduce read/upload/calibration wall time with deeper native completion or
  better overlap; or
- reduce resident winsorized integration time with a stronger device-side
  reducer.

## Clean-Room Compliance

- This gate uses GLASS-owned runtime state, audit, and benchmark artifacts.
- Validation uses user-owned input data and GLASS-generated outputs.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
