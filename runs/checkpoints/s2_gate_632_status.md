# S2-Gate 632 Status: Single-Wait Native Completion Default

## Gate

S2-Gate 632 implements the next resident native-completion calibration
scheduler improvement after Gate631. It keeps the 4-lane high-VRAM default but
changes completion wave-fill from repeated waits to a single bounded wait per
consumer wave.

## Completed

- Added `--resident-native-completion-wave-fill-mode` with:
  - `single_wait`: at most one bounded wait per completion wave;
  - `multi_wait`: previous repeated wait-for-fill behavior.
- Added `GLASS_RESIDENT_NATIVE_COMPLETION_WAVE_FILL_MODE` for explicit
  experiments when CLI mode remains at the default.
- Implemented the native C++ `single_wait` branch in
  `calibrate_frames_fits_u16be_bzero_paths_completion_queue_timed`.
- Recorded actual/requested/source wave-fill mode in:
  - native timing payloads;
  - `resident_io_pipeline`;
  - `resident_light_pipeline_profile.native_completion`;
  - profile `knobs`;
  - `run_timing.json`.
- Promoted `single_wait` as the default mode for the
  `throughput-v4-native-completion` resident runtime preset.
- Preserved explicit `--resident-native-completion-wave-fill-mode multi_wait`
  as the compatibility and A/B fallback.
- Updated focused CLI/native/resident/profile tests.
- Updated Phase 2 plan, known limitations, and algorithm-source ledger.

## Code Changes

- `cpp/src/native_bindings.cpp`
- `src/glass/cli.py`
- `src/glass/engine/resident_cuda.py`
- `src/glass/engine/resident_light_pipeline_profile.py`
- `tests/test_cli_smoke.py`
- `tests/test_cuda_resident_stack.py`
- `tests/test_resident_cuda_run.py`
- `tests/test_resident_light_pipeline_profile.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/known_limitations.md`
- `docs/algorithm_sources.md`

## Real 200-Light Evidence

- Run root:
  `C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431`
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\gate632_single_wait_summary.json`
- Summary Markdown:
  `C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\gate632_single_wait_summary.md`

Measured rows:

| variant | mode | total s | native H2D+cal s | wait count | wait s | waves | lane fill | active/masked |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| default_multi_wait | multi_wait | 11.097 | 1.963 | 135 | 0.184 | 56 | 0.893 | 193/7 |
| single_wait | single_wait | 10.730 | 1.912 | 94 | 0.175 | 97 | 0.515 | 193/7 |
| default_multi_wait_r2 | multi_wait | 10.825 | 1.966 | 139 | 0.201 | 54 | 0.926 | 193/7 |
| single_wait_r2 | single_wait | 10.687 | 1.977 | 94 | 0.192 | 97 | 0.515 | 193/7 |
| default_promoted_single_wait | single_wait | 10.820 | 1.967 | 93 | 0.144 | 97 | 0.515 | 193/7 |

Mean explicit-pair ratios:

- `single_wait` versus `multi_wait` total elapsed ratio: `0.976989`.
- `single_wait` versus `multi_wait` native H2D+calibration ratio: `0.990062`.
- `single_wait` versus `multi_wait` wait-count ratio: `0.686131`.

Regression gates:

- `regression_default_multi_vs_single_wait.json`: passed, elapsed ratio
  `0.9669097248119599`.
- `regression_default_multi_r2_vs_single_wait_r2.json`: passed, elapsed ratio
  `0.9873223661024512`.
- `regression_default_multi_vs_promoted_single_wait.json`: passed, elapsed
  ratio `0.9750197625770799`.

The post-promotion run was executed without an explicit mode override. Its
`run_timing.json` and `resident_io_pipeline` both recorded `single_wait`.

## Decision

- Default change: promoted.
- New default: `throughput-v4-native-completion` uses
  `resident_native_completion_wave_fill_mode=single_wait`.
- Fallback: pass `--resident-native-completion-wave-fill-mode multi_wait`.
- Reason: `single_wait` preserved output parity in all regression gates,
  reduced repeated condition-variable waits, and improved total elapsed time
  across two paired real 200-light repeats.

## Commands Run

```powershell
cmd.exe /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"" >nul && .\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native -j 8"

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\<variant> --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final

.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\<single_wait_variant> --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-native-completion-wave-fill-mode single_wait

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\default_multi_wait --candidate-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\single_wait --out C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\regression_default_multi_vs_single_wait.json --markdown C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\regression_default_multi_vs_single_wait.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\default_multi_wait_r2 --candidate-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\single_wait_r2 --out C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\regression_default_multi_r2_vs_single_wait_r2.json --markdown C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\regression_default_multi_r2_vs_single_wait_r2.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\default_multi_wait --candidate-run C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\default_promoted_single_wait --out C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\regression_default_multi_vs_promoted_single_wait.json --markdown C:\glass_runs\phase2_s2_gate632_single_wait\runs_20260625_142431\regression_default_multi_vs_promoted_single_wait.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure

.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_resident_runtime_preset_throughput_v4_native_completion_applies_default_values tests\test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v4_native_completion tests\test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_completion_wave_fill_mode tests\test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests\test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_runtime_preset_is_cli_opt_in tests\test_resident_light_pipeline_profile.py
.\.venv\Scripts\ruff.exe check src tests docs --select E,F --ignore E501
git diff --check
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Native build: passed.
- Focused tests before promotion: `10 passed`.
- Focused tests after promotion: `10 passed`.
- Ruff: `All checks passed!`
- Diff check: passed.
- Full pytest: `1326 passed in 59.88s`.

## CUDA Availability

- CUDA available to GLASS: yes.
- Native backend: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Driver: `596.21`.
- VRAM reported by `nvidia-smi`: `97887 MiB`.

## Known Limits

- This gate reduces completion-queue wait overhead; it does not solve the
  larger resident hardened winsorized kernel cost.
- `single_wait` produces lower lane fill by design; the real benchmark shows
  fewer waits and lower total elapsed time despite lower lane fill.
- Hardware or disk configurations that benefit from repeated wave filling can
  still request `multi_wait` explicitly.

## Next Step

Start S2-Gate 633 on a larger hot path: either resident hardened winsorized
kernel structure or a deeper native read/H2D overlap redesign that reduces the
remaining `native_h2d_calibrate_store` wall time without changing output pixels.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned native scheduling code, GLASS tests,
GLASS-generated artifacts, and user-owned 200-light benchmark data. It does not
inspect external implementation source, use proprietary behavior, modify input
directories, or copy external algorithms.
