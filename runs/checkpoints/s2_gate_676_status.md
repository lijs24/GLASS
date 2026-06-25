# S2-Gate 676 Status: Native Completion Micro-Poll Wave Fill

## Gate

- Gate: S2-Gate 676
- Date: 2026-06-26
- Status: passed

## Completed Work

- Changed native resident CUDA completion-queue wave-fill waits in the `1..500 us` range from `condition_variable.wait_for` to a short unlock/yield/relock micro-poll loop.
- Preserved the default `throughput-v4-native-completion` policy of `single_wait_25us`; the gate changes the sub-millisecond wait implementation, not the runtime preset.
- Kept zero-wait behavior as `disabled` and larger waits as `condition_variable_wait_for`.
- Added runtime/profile disclosure for `native_completion_consumer_wave_fill_wait_strategy`.
- Updated resident CUDA artifact propagation and resident light-pipeline profile summaries.
- Added tests for default no-wait disabled strategy and native-completion micro-poll strategy.
- Updated Phase 2 hardening, validation, known limitations, and algorithm-source documentation.

## Commands Run

```powershell
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build build --config Release --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_calibrates_u16be_paths_completion_queue_on_gpu_like_cpu tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_u16_completion_calibration_is_opt_in tests/test_resident_cuda_run.py::test_cli_resident_cuda_native_completion_runtime_preset_is_cli_opt_in tests/test_resident_light_pipeline_profile.py
.\.venv\Scripts\python.exe -m glass.cli run --plan 'C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json' --out 'C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll' --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir 'C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final'
.\.venv\Scripts\python.exe -m pytest -q
```

Additional acceptance commands produced:

- `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\gate676_phase2_mainline_audit.json`
- `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\gate676_vs_gate675_regression.json`

## Test Results

- Native CUDA rebuild: passed.
- Focused tests: `7 passed in 1.89s`.
- Full pytest: `1419 passed in 64.60s`.
- Phase 2 mainline audit: passed, failed checks `[]`.
- Gate675 regression gate: passed, failed checks `[]`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.
- Driver/runtime context observed in current build artifacts: NVIDIA driver 596.21, CUDA 13.2 build environment.

## Real 200-Light Validation

- Run: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll`
- Plan: `C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json`
- Input lights: 200.
- Active frames: 193.
- Masked frames: 7.
- Mainline route: resident CUDA, resident memory mode, local normalization on, similarity CUDA triangle registration, Lanczos3 warp, winsorized sigma integration.
- Mainline audit total elapsed: `11.825730400159955 s`.
- Component timings:
  - light read/upload/calibrate: `3.0986569999950007 s`
  - resident registration/warp: `0.25982120051048696 s`
  - resident local normalization: `0.36506579990964383 s`
  - resident integration: `3.371088800020516 s`
  - output write: `0.2352990999352187 s`

## Gate675 Regression Summary

- Baseline: `C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\default_unit_weight_map_from_coverage`
- Candidate: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll`
- Determinism differences: 0 output differences, 0 artifact differences, 0 frame-accounting differences, 0 registration differences.
- Elapsed ratio: `0.9725103078340935`.
- Light read/upload/calibrate ratio: `0.9069537480813726`.
- H2D/calibrate/store ratio: `0.8869540089254363`.
- Resident integration ratio: `1.0289805924952096` (integration variance/regression remains within threshold).

## Native Completion Profile

Gate675 default:

- Policy: `single_wait_25us`
- Strategy: not recorded before this gate
- Wave-fill wait: `0.19453819999999994 s`
- Wait count: 99
- Timeout count: 12
- Wave count: 99
- Multi-frame wave count: 87
- Lane-fill ratio: `0.5050505050505051`

Gate676 default:

- Policy: `single_wait_25us`
- Strategy: `micro_poll_yield`
- Wave-fill wait: `0.005880000000000006 s`
- Wait count: 184
- Timeout count: 181
- Wave count: 185
- Max wave frames: 2
- Multi-frame wave count: 15
- Lane-fill ratio: `0.2702702702702703`

Interpretation: Windows sub-millisecond `condition_variable.wait_for(25us)` was oversleeping materially on the real default path. Micro-polling makes the requested short wait much closer to its intended budget and reduces the light-stage wall time while preserving outputs.

## Artifacts

- Run directory: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll`
- Mainline audit: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\gate676_phase2_mainline_audit.json`
- Regression gate: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\gate676_vs_gate675_regression.json`
- Master: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll\integration\resident_master_H.fits`
- Weight map: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll\integration\resident_weight_map_H.fits`
- Coverage map: `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll\integration\resident_coverage_map_H.fits`
- Low/high rejection maps and DQ map: present in the same integration directory.

## Known Limitations

- This gate optimizes native completion-queue scheduling only; it does not change calibration, registration, warp, local normalization, rejection math, DQ semantics, output maps, or frame admission.
- The measured wave-fill wait decreases strongly, but integration remains the largest resident component in this run.
- The real 200-light timing includes normal disk/OS variance; the optimization is accepted because it passed deterministic output regression and improved total elapsed to `0.9725103078340935x` of Gate675.
- The current real benchmark has no positive source-DQ sidecar/inline invalid samples, so nonzero source-DQ stress remains a separate mainline target.

## Next Step

- Continue Phase 2 mainline optimization at the largest remaining resident component: the hardened winsorized integration reducer and/or broader H2D/calibration overlap. Avoid new report-only gates unless they directly unblock those runtime or correctness targets.

## Clean-Room Compliance

- Compliant.
- No external/proprietary implementation source was inspected, summarized, copied, or reworked.
- Validation used GLASS-owned code/tests/artifacts and user-owned 200-light benchmark data only.
- Input image directories were treated as read-only.
