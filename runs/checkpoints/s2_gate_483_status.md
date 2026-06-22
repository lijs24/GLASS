# S2-Gate 483 Status: StackEngine Mean Fast Path And Cold-Cache Regression

## Gate

- Gate: S2-Gate 483
- Status: green
- Date: 2026-06-23
- Objective: reduce the Gate482 resident master-cache cold-build regression while keeping master construction inside `CPUStackEngine` and preserving StackEngine/DQ result contracts.

## Completed

- Added a `CPUStackEngine` fast path for mean/weighted-mean stacks when rejection is disabled.
- The fast path streams one source tile at a time into weighted-sum, weight-sum, coverage, and optional variance accumulators.
- It avoids per-tile 3D `np.stack` materialization and records:
  - `metrics.execution_path=streaming_mean_no_rejection`;
  - `dq_provenance.execution_path=streaming_mean_no_rejection`;
  - the normal embedded StackEngine result contract.
- Added tests proving:
  - mean/no-rejection no longer calls `np.stack`;
  - DQ and non-finite samples are still accounted correctly;
  - weighted mean, coverage, weight maps, variance, DQ provenance, and result contract remain valid.
- Updated `docs/algorithm_sources.md` and `docs/phase2_algorithm_hardening.md`.

## Real 200-Light A/B

- Output root: `C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real`
- Summary JSON: `C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real\gate483_real_ab_summary.json`
- Dataset: M38 H-alpha benchmark manifest with 200 lights, 20 bias, 20 dark, 20 flat.
- Matched calibration group used by planner for H: 6 bias, 11 dark, 4 flat.

### Timing

- Cold fast-mean total: `52.42856379994191 s`
- Cold fast-mean `master_build_or_load`: `32.28885949996766 s`
- Warm fast-mean total: `20.60115920001408 s`
- Warm fast-mean `master_build_or_load`: `0.30893689999356866 s`
- Gate482 cold total: `66.35778469999786 s`
- Gate482 cold `master_build_or_load`: `46.852212900004815 s`
- Cold total speedup vs Gate482: `1.2656800013291873x`
- Cold master-build speedup vs Gate482: `1.4510333788671521x`
- Warm GLASS vs WBPP speedup: `53.032986609765786x`

### Numerical Results

- Warm vs cold master: shape match true, RMS `0.0`, p99 `0.0`, max `0.0`
- Warm vs Gate482 warm master: shape match true, RMS `0.0`, p99 `0.0`, max `0.0`
- Warm vs WBPP with coverage >= 190:
  - RMS `0.0017794216505176163`
  - p99 abs diff `0.00042621337808668863`
  - p99.9 abs diff `0.003845416396856427`
  - coverage fraction `0.960532609259836`
  - compared pixels `59217988`

### Acceptance

- Threshold acceptance passed:
  - lights >= 200
  - bias >= 20
  - dark >= 20
  - flat >= 20
  - active frames >= 190
  - speedup >= 20x
  - coverage fraction >= 0.95
  - RMS <= 0.01
  - p99 abs diff <= 0.01
- Acceptance artifact:
  `C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real\acceptance\warm_threshold_acceptance_audit.json`
- Report:
  `C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real\reports\warm_report.html`

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\stack_engine.py tests\test_stack_engine.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine.py tests\test_stack_engine_result_contract.py tests\test_resident_master_stack_engine.py`
- Cold real run:
  `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real\runs\cold_fast_mean_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real\shared_master_cache`
- Warm real run: same command with `--out C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real\runs\warm_fast_mean_cache`
- `glass compare` for warm-vs-cold, warm-vs-Gate482 warm, and warm-vs-WBPP coverage>=190.
- `glass speedup-summary --min-speedup 20`
- `glass acceptance-audit` threshold mode.
- `glass report`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Result

- Focused StackEngine tests: `21 passed`
- Full pytest: `1124 passed in 41.07s`
- Ruff: passed

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Observed after gate: GPU utilization `0%`, memory `825 / 97887 MiB`

## Disk / Cleanup

- C: free after gate: about `39.92 GB`
- No user data was deleted.
- Candidate generated-output cleanup roots, if space is needed:
  - `C:\glass_runs\phase2_s2_gate482_stackengine_master_cache_ab_real` aborted robust-rejection probe;
  - `C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real`;
  - `C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real`.

## Known Limitations

- Gate483 improves cold StackEngine master build/load from `46.85 s` to `32.29 s`, but Gate481's helper-built cold cache was still faster at about `10.91 s`.
- The fast path only covers mean/weighted-mean with rejection disabled.
- Robust resident master rejection remains deferred because the full-size CPU attempt in Gate482 was too slow.
- Median, sum, and rejected stacks still use the generic StackEngine tile path.

## Next Step

- Build a native/CUDA or finite-only fast master-mean path that preserves StackEngine-compatible DQ provenance but approaches or beats the Gate481 helper cold-cache time.
- After that, revisit robust master-frame rejection with an optimized implementation instead of the generic CPU StackEngine path.

## Clean-Room

- Compliant.
- Used only GLASS code, GLASS artifacts, user-owned image data, and user-generated WBPP black-box timing/output files.
- Did not read, copy, summarize, or rework official PixInsight/WBPP/PJSR implementation source.
- Did not modify input image directories.
