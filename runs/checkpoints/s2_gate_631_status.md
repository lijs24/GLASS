# S2-Gate 631 Status: Native Completion Lane-Fill Profile

## Gate

S2-Gate 631 returns to the resident read/H2D/calibration hot path. It tests
whether the native completion-queue calibration path should use more lanes by
default, and adds the missing lane-fill telemetry needed to guide the next
substantive optimization.

## Completed

- Ran a real 200-light native-completion lane matrix with the same plan, same
  resident master cache, same audit-map policy, and same CUDA backend:
  - default 4 lanes;
  - 8 lanes;
  - 12 lanes;
  - 16 lanes.
- Ran an additional default-vs-8-lane repeat pair.
- Ran a post-change default real 200-light rerun to prove the new profile
  contract appears in real artifacts.
- Ran resident-regression-gate checks for:
  - default4 versus lanes8;
  - default4_r2 versus lanes8_r2;
  - default4 versus the post-change profile-contract rerun.
- Kept the default runtime preset unchanged. 8 lanes were numerically safe but
  not a stable native-calibration or total-time win; 12/16 lanes increased
  native calibration time in the first matrix.
- Added `resident_light_pipeline_profile.native_completion` with:
  - submit/completion counts;
  - worker and queue-buffer counts;
  - slot-reuse waits;
  - consumer wave counts;
  - max wave frames;
  - multi-frame wave fraction;
  - wave-fill waits;
  - `consumer_lane_fill_ratio`.
- Added focused unit coverage for the new profile contract and recommendation.
- Updated Phase 2 plan, known limitations, and algorithm-source ledger.

## Code Changes

- `src/glass/engine/resident_light_pipeline_profile.py`
- `tests/test_resident_light_pipeline_profile.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/known_limitations.md`
- `docs/algorithm_sources.md`

## Real 200-Light Evidence

- Matrix root:
  `C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533`
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\gate631_lane_matrix_summary.json`
- Summary Markdown:
  `C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\gate631_lane_matrix_summary.md`

Measured rows:

| variant | streams | total s | native H2D+cal s | kernel s | lane fill | active/masked |
|---|---:|---:|---:|---:|---:|---:|
| default4 | 4 | 11.165 | 1.977 | 3.197 | 0.862 | 193/7 |
| lanes8 | 8 | 10.790 | 1.968 | 3.220 | 0.610 | 193/7 |
| lanes12 | 12 | 10.887 | 2.032 | 3.209 | 0.450 | 193/7 |
| lanes16 | 16 | 10.835 | 2.011 | 3.180 | 0.735 | 193/7 |
| default4_r2 | 4 | 10.662 | 1.974 | 3.197 | 0.847 | 193/7 |
| lanes8_r2 | 8 | 10.862 | 1.980 | 3.221 | 0.893 | 193/7 |
| default4_profile_contract | 4 | 10.745 | 1.968 | 3.202 | 0.781 | 193/7 |

Repeat summary:

- 8-lane versus default native H2D mean ratio: `0.999212`.
- 8-lane versus default total elapsed mean ratio: `0.992004`.
- Default lane-fill mean: `0.854763`.
- 8-lane mean lane-fill: `0.751307`.

Regression gates:

- `regression_default4_vs_lanes8.json`: passed, elapsed ratio
  `0.9663834722897465`.
- `regression_default4_r2_vs_lanes8_r2.json`: passed, elapsed ratio
  `1.0188336004688132`.
- `regression_default4_vs_profile_contract.json`: passed, elapsed ratio
  `0.9623754746375969`.

## Decision

- Default change: rejected.
- Reason: adding lanes is not a stable win on the current 200-light data. The
  8-lane route preserves output, but its native H2D/calibration timing is
  effectively equal to default across repeats. 12/16 lanes make the native
  calibration segment slower in the first matrix.
- Next optimization target: improve native completion wave-fill/overlap before
  adding more lanes, or return to the bounded hardened winsorized reducer
  kernel itself.

## Commands Run

```powershell
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\<variant> --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\<lanesN> --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-calibration-streams <N> --resident-calibration-wave-frames <N>

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\default4 --candidate-run C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\lanes8 --out C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\regression_default4_vs_lanes8.json --markdown C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\regression_default4_vs_lanes8.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\default4_r2 --candidate-run C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\lanes8_r2 --out C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\regression_default4_r2_vs_lanes8_r2.json --markdown C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\regression_default4_r2_vs_lanes8_r2.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\default4 --candidate-run C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\default4_profile_contract --out C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\regression_default4_vs_profile_contract.json --markdown C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix\runs_20260625_140533\regression_default4_vs_profile_contract.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_light_pipeline_profile.py tests\test_cli_smoke.py::test_resident_runtime_preset_throughput_v4_native_completion_applies_default_values tests\test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v4_native_completion tests\test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_runtime_preset_is_cli_opt_in
.\.venv\Scripts\ruff.exe check src tests docs --select E,F --ignore E501
git diff --check
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests: `7 passed`.
- Ruff: `All checks passed!`
- Diff check: passed.
- Full pytest: `1325 passed in 57.72s`.

## CUDA Availability

- CUDA available to GLASS: yes.
- Native backend: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Driver: `596.21`.
- VRAM reported by `nvidia-smi`: `97887 MiB`.

## Known Limits

- This gate does not speed up the default path; it prevents a misleading
  lane-count promotion and exposes the missing metrics needed for the next
  optimization.
- Profile-only artifacts generated before this code change do not contain the
  new `native_completion` block, but their raw `resident_io_pipeline` payload
  still contains enough counters to recompute lane fill.
- The resident integration kernel remains the larger measured hot path after
  calibration.

## Next Step

Start S2-Gate 632 on a substantive hot-path improvement. Preferred directions:

- native completion wave-fill/overlap improvement that increases lane-fill
  without raising lane count blindly; or
- CUDA hardened winsorized reducer work that reduces the current native
  kernel-sync segment.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned runtime profile code, GLASS tests,
GLASS-generated artifacts, and user-owned 200-light benchmark data. It does not
inspect external implementation source, use proprietary behavior, modify input
directories, or copy external algorithms.
