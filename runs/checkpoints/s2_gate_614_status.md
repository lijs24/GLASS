# S2-Gate 614 Status: Resident Regression Gate

## Gate

S2-Gate 614 adds a hard resident CUDA regression command for the real 200-light
A/B path. The gate was created after rejecting a native winsorized integration
micro-optimization that either slowed the run or changed output pixels.

## Completed Content

- Added `glass resident-regression-gate`.
- Added `src/glass/report/resident_regression_gate.py`.
- Added unit and CLI tests in `tests/test_resident_regression_gate.py`.
- The gate checks resident determinism, runtime ratio, pipeline contract,
  StackEngine contract, resident DQ pixel closure, and optional resident
  frame-mask thresholds.
- Ran a fresh real 200-light resident CUDA candidate and compared it against
  the Gate613 green baseline.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_regression_gate.py
.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --help
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_regression_gate.py tests\test_resident_regression_gate.py src\glass\cli.py
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate614_regression_gate\real_200_default_regression --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate613_ln_batch_stats\real_200_default_regression --candidate-run C:\glass_runs\phase2_s2_gate614_regression_gate\real_200_default_regression --out C:\glass_runs\phase2_s2_gate614_regression_gate\resident_regression_gate_vs_gate613.json --markdown C:\glass_runs\phase2_s2_gate614_regression_gate\resident_regression_gate_vs_gate613.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_regression_gate.py tests\test_resident_determinism.py tests\test_resident_runtime_compare.py
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_regression_gate.py tests\test_resident_regression_gate.py src\glass\cli.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- `tests/test_resident_regression_gate.py`: `3 passed`.
- Focused resident regression/determinism/runtime tests: `10 passed`.
- Ruff: `All checks passed`.
- Full pytest: `1293 passed in 54.14s`.

## Real 200-Light Result

- Baseline:
  `C:\glass_runs\phase2_s2_gate613_ln_batch_stats\real_200_default_regression`
- Candidate:
  `C:\glass_runs\phase2_s2_gate614_regression_gate\real_200_default_regression`
- Gate JSON:
  `C:\glass_runs\phase2_s2_gate614_regression_gate\resident_regression_gate_vs_gate613.json`
- Gate Markdown:
  `C:\glass_runs\phase2_s2_gate614_regression_gate\resident_regression_gate_vs_gate613.md`
- Candidate runtime: `10.9278315998381 s`.
- Gate613 baseline runtime: `11.212513899896294 s`.
- Candidate/baseline elapsed ratio: `0.9746103057173622`.
- Determinism differences: artifact `0`, frame signatures `0`,
  registration `0`, frame accounting `0`, output pixels `0`.
- Frame masks: `193 / 200` active, `7` masked.
- Gate status: `passed`.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Known Limitations

- The new command compares existing baseline/candidate run directories. It does
  not run the candidate by itself.
- Runtime thresholds are based on `run_timing.json` wall-clock fields and can
  vary with storage cache state. A run close to the threshold should be repeated
  before accepting or rejecting an optimization.
- Gate614 is a regression guard, not a new performance optimization.

## Next Step

Use `glass resident-regression-gate` as the real 200-light A/B guard before the
next substantive Phase 2 default-path work: StackEngine default-path
consolidation, DQ/mask pipeline completion, resident registration/warp
orchestration, and CUDA resident performance optimization.

## Clean-Room Compliance

This gate uses only GLASS-owned code, GLASS-generated artifacts, user-owned
input data, and locally generated benchmark outputs. It does not read, copy,
summarize, or rework proprietary implementation source.
