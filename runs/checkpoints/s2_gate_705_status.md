# S2 Gate 705 Status: Multi-Wait Native Completion Lane Fill

## Gate

- Gate: S2-Gate 705
- Date: 2026-06-26
- Status: green
- Branch: `main`
- Goal area: resident CUDA light read/upload/calibrate pipeline scheduling.

## Completed Content

- Promoted the default `throughput-v4-native-completion` scheduling preset from:
  - `resident_native_completion_wave_fill_mode=single_wait`
  - `resident_native_completion_wave_fill_us=250`
- To:
  - `resident_native_completion_wave_fill_mode=multi_wait`
  - `resident_native_completion_wave_fill_us=1000`
- This keeps the existing native completion queue, H2D upload, CUDA
  calibration kernels, calibration formulas, frame admission, DQ, registration,
  local normalization, and integration math unchanged.
- Explicit rollback/A-B controls remain available:
  - `--resident-native-completion-wave-fill-mode single_wait`
  - `--resident-native-completion-wave-fill-us 250`
- Updated focused tests and documentation:
  - `src/glass/cli.py`
  - `tests/test_cli_smoke.py`
  - `tests/test_resident_cuda_run.py`
  - `docs/phase2_algorithm_hardening.md`
  - `docs/integration_model.md`
  - `docs/known_limitations.md`
  - `docs/algorithm_sources.md`

## Space Cleanup

Before the real 200-light validation, C: had only about `3.27 GB` free. To keep
the benchmark on C: without touching input image directories or current
baseline artifacts, the following old generated GLASS run directories were
removed:

- `C:\glass_runs\phase2_s2_gate555_prefetch_depth_matrix`
- `C:\glass_runs\phase2_s2_gate556_scheduler_candidates`
- `C:\glass_runs\phase2_s2_gate631_calibration_lane_matrix`

After cleanup, C: had about `37.17 GB` free. No raw input image directories were
modified.

## Commands Run

```powershell
.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\single_wait_1000us_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-native-completion-wave-fill-us 1000
```

```powershell
.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\multi_wait_1000us_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-native-completion-wave-fill-us 1000 --resident-native-completion-wave-fill-mode multi_wait
```

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py -k "runtime_preset"
```

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "native_completion_wave_fill or native_u16_completion_calibration_is_opt_in or native_completion_queue_buffer"
```

```powershell
.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
```

```powershell
.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000 --out C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\gate705_default_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\gate705_default_mainline_audit.md --fail-on-not-green
```

```powershell
.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\active_index_candidate --candidate-run C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000 --out C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\gate705_default_vs_gate704_regression.json --markdown C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\gate705_default_vs_gate704_regression.md --max-elapsed-ratio 1.05 --fail-on-failure
```

```powershell
.venv\Scripts\python.exe -m ruff check src/glass/cli.py tests/test_cli_smoke.py tests/test_resident_cuda_run.py
```

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff over touched Python files: passed.
- Focused CLI runtime-preset tests: `12 passed, 82 deselected in 1.02 s`.
- Focused resident native-completion tests: `3 passed, 138 deselected in 2.36 s`.
- Full pytest: `1451 passed in 72.90 s`.
- Phase 2 mainline audit: passed.
- Resident regression gate versus Gate704: passed.
- Regression determinism summary:
  - `artifact_difference_count=0`
  - `frame_accounting_difference_count=0`
  - `frame_signature_difference_count=0`
  - `output_difference_count=0`
  - `output_numerical_drift_count=0`
  - `registration_difference_count=0`

## CUDA Availability

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- VRAM: `97886 MiB`
- Driver version: `596.21`
- Native backend loaded: yes.

## Real 200-Light Result

- Baseline:
  `C:\glass_runs\phase2_s2_gate704_active_index_integration\runs_20260626_110113\active_index_candidate`
- Single-wait 1000us probe:
  `C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\single_wait_1000us_candidate`
- Explicit multi-wait 1000us probe:
  `C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\multi_wait_1000us_candidate`
- Promoted default:
  `C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000`

| Metric | Gate704 default | Single-wait 1000us | Multi-wait 1000us | Promoted default |
| --- | ---: | ---: | ---: | ---: |
| Total elapsed | `11.090906699886546 s` | `11.129275600076653 s` | `10.542253200197592 s` | `10.727156800101511 s` |
| Resident calibration + integration | `9.755395399988629 s` | `9.69165479997173 s` | `9.194300799979828 s` | `9.385764499893412 s` |
| Light read/upload/calibrate | `3.101156600052491 s` | `3.134771700017154 s` | `2.879372700001113 s` | `2.982370199984871 s` |
| Resident integration | `2.6184026999399066 s` | `2.6177477000746876 s` | `2.6162375999847427 s` | `2.627562499954365 s` |
| Native completion lane fill | `0.3472222222222222` | `0.5376344086021505` | `0.9803921568627451` | `0.9090909090909091` |
| Native completion wave count | `144` | `93` | `51` | `55` |
| Multi-frame wave fraction | `0.2638888888888889` | `0.9139784946236559` | `0.9803921568627451` | `0.9272727272727272` |

The promoted default produced `200` input lights, `193` active frames, and `7`
masked frames, matching the Gate704 frame accounting.

## Known Limitations

- This gate is a scheduling default, not a new calibration algorithm.
- It improves lane fill on the current RTX PRO 6000 / external-storage setup,
  but different storage/GPU combinations may still prefer explicit wait-mode
  overrides.
- The largest resident component remains light read/upload/calibrate at about
  `2.98 s`; the next work should target native H2D/calibrate-store cost and
  Python/orchestration overhead rather than only increasing lane count.

## Next Step

- Use Gate705 as the new resident calibration/read baseline.
- Next substantive gate should either:
  - reduce native H2D/calibrate-store time, or
  - move more calibration scheduling/orchestration into native code while
    preserving resident DQ/mask contracts and 200-light output stability.

## Clean-Room Compliance

- This gate uses GLASS-owned native completion queue behavior, GLASS runtime
  preset plumbing, GLASS tests, and user-owned benchmark artifacts.
- No external proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
