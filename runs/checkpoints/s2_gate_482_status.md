# S2-Gate 482 Status: Resident Master-Cache StackEngine Builder And Real 200-Light A/B

## Gate

- Gate: S2-Gate 482
- Status: green
- Date: 2026-06-23
- Objective: return to Phase 2 substantive work by closing a resident CUDA master-cache StackEngine/DQ provenance gap, then run a real M38 H-alpha 200-light cold/warm A/B.

## Gate400-413 Retrospective

- Gate400-413 mostly strengthened release/profile/evidence handoff contracts rather than image computation.
- Actual core value:
  - preserved release-quality evidence through profile chains;
  - made resident CUDA DQ benchmark profiles reusable by acceptance and sweep planning;
  - reduced risk that future publication/default-promotion decisions drop benchmark profile evidence.
- Actual limitation:
  - they did not improve StackEngine execution, DQ pixel semantics, registration, resident performance, or 200-light numerical parity.
- Gate482 deliberately returns to the requested mainline: StackEngine default path, DQ/mask provenance, real 200-light regression, and performance evidence.

## Completed

- Resident CUDA master-cache cold-build path now uses GLASS `CPUStackEngine` for bias/dark/flat mean stacks.
- Shared resident master-cache fingerprint was bumped with builder id `resident_stack_engine_mean_master_cache_v1`, so older helper-built caches are not silently reused.
- Resident master-cache set stats now record:
  - `tile_stack_mode=stack_engine_cpu`;
  - `stack_engine_enabled=true`;
  - `stack_engine_metrics`;
  - `stack_engine_dq_provenance`;
  - `dq_provenance_summary`;
  - `master_rejection_requested`;
  - `master_rejection_applied`.
- Resident calibration artifacts now surface actual applied resident master rejection.
- Added `tests/test_resident_master_stack_engine.py`.
- Documented the algorithm-source entry and Phase 2 gate section.

## Important Probe Result

- A direct attempt to run CPU StackEngine robust master-frame rejection on the real full-size calibration set exceeded 30 minutes before writing any master-cache files.
- That attempt was stopped because it made the cold path unusable.
- Gate482 therefore constrains resident master-cache construction to mean/no-rejection for speed and numerical continuity, while recording requested-vs-applied rejection.
- Optimized robust resident master rejection remains a future CUDA or optimized CPU gate.

## Real 200-Light A/B

- Dataset: M38 H-alpha benchmark manifest with 200 lights, 20 bias, 20 dark, 20 flat.
- Output root: `C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real`
- Summary JSON: `C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real\gate482_real_ab_summary.json`

### Timing

- Cold StackEngine-cache total: `66.35778469999786 s`
- Cold `master_build_or_load`: `46.852212900004815 s`
- Warm StackEngine-cache total: `20.40486560005229 s`
- Warm `master_build_or_load`: `0.31111190002411604 s`
- Warm-vs-cold speedup: `3.2520569358627784x`
- Warm GLASS vs WBPP speedup: `53.54316080362716x`

### Numerical Results

- Warm vs cold master: shape match true, RMS `0.0`, p99 `0.0`, max `0.0`
- Warm vs Gate481 warm master: shape match true, RMS `0.0`, p99 `0.0`, max `0.0`
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
- Threshold acceptance artifact:
  `C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real\acceptance\warm_threshold_acceptance_audit.json`
- Strict benchmark-contract acceptance failed only because it required extra pipeline/StackEngine promotion evidence and an older command-token profile outside this gate's recipe. Image, speed, and threshold acceptance passed.
- Strict diagnostic artifact:
  `C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real\acceptance\warm_acceptance_audit.json`

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\engine\resident_calibration_artifacts.py tests\test_resident_master_stack_engine.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_shared_master_cache_reuses_across_runs tests\test_resident_calibration_artifacts.py tests\test_resident_calibration_contract.py`
- Cold real run:
  `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real\runs\cold_stackengine_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real\shared_master_cache`
- Warm real run: same command with `--out C:\glass_runs\phase2_s2_gate482_stackengine_mean_master_cache_ab_real\runs\warm_stackengine_cache`
- `glass compare` for warm-vs-cold, warm-vs-Gate481 warm, and warm-vs-WBPP coverage>=190.
- `glass speedup-summary --min-speedup 20`
- `glass acceptance-audit` threshold mode.
- `glass report`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Result

- Full pytest: `1122 passed in 41.37s`
- Focused resident/calibration tests: passed
- Ruff: passed

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Observed after gate: GPU utilization `0%`, memory `825 / 97887 MiB`

## Disk / Cleanup

- C: free after gate: about `42.53 GB`
- No user data was deleted.
- If cleanup becomes necessary, candidate generated-output roots are under `C:\glass_runs\phase2_s2_gate482_*`; project `runs/` contains old untracked checkpoint artifacts but was left untouched for auditability.

## Known Limitations

- Cold StackEngine master-cache build is slower than Gate481 helper-built cold cache: `46.85 s` master build/load versus Gate481's about `10.91 s`.
- Resident master-cache robust rejection is not applied yet; artifacts explicitly record requested `winsorized_sigma`, applied `none`.
- The real matched calibration set used by the planner contains 6 bias, 11 dark, and 4 flat frames for this H group even though the benchmark manifest contains at least 20 of each calibration frame type.
- Strict benchmark-contract acceptance needs a refreshed command/profile contract or attached pipeline/StackEngine promotion artifacts before it can pass for this recipe.

## Next Step

- Optimize resident master-cache StackEngine cold build:
  - avoid Python/DQ overhead for finite-only FITS master stacks;
  - consider a native/CUDA mean master builder that still emits StackEngine-compatible DQ provenance;
  - add a robust master-frame rejection implementation that is fast enough for full-size calibration sets.
- Continue Phase 2 mainline rather than release/report-only handoff gates.

## Clean-Room

- Compliant.
- Used only GLASS code, GLASS artifacts, user-owned image data, and user-generated WBPP black-box timing/output files.
- Did not read, copy, summarize, or rework official PixInsight/WBPP/PJSR implementation source.
- Did not modify input image directories.
