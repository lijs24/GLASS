# S2-Gate 680 Status: Native Completion Ring Capacity Control

## Gate

S2-Gate 680.

## Completed Content

- Added `--resident-native-completion-queue-buffer-frames` to `glass run` and
  `glass audit`.
- Threaded the value into resident CUDA native-completion calibration.
- Preserved the default raw-ring capacity formula:
  `max(prefetch_frames, calibration_batch_frames, calibration_streams*2)`.
- Explicit requests enlarge the planned native-completion raw FITS pinned-host
  ring without shrinking the established safe base.
- Resident artifacts and `resident_light_pipeline_profile` now record:
  - queue buffer policy source;
  - base frames;
  - requested frames;
  - planned frames;
  - native effective/clamped frames;
  - estimated and effective pinned raw bytes.
- Ran focused synthetic/CLI validation and a real 200-light 32-vs-64 buffer A/B.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py -k "native_completion or runtime_preset"
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py -k "native_completion_queue_buffer_frames or native_completion_calibration_is_opt_in or native_completion_runtime_preset"
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue64_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-native-completion-queue-buffer-frames 64
.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue64_candidate --out C:\glass_runs\phase2_s2_gate680_completion_ring\gate680_queue64_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate680_completion_ring\gate680_queue64_phase2_mainline_audit.md --min-lights 200 --min-active-frames 193 --max-masked-frames 7 --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default --candidate-run C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue64_candidate --out C:\glass_runs\phase2_s2_gate680_completion_ring\gate680_queue64_vs_queue32_regression.json --markdown C:\glass_runs\phase2_s2_gate680_completion_ring\gate680_queue64_vs_queue32_regression.md --max-elapsed-ratio 1.05 --min-active-frame-count 193 --max-masked-frame-count 7 --fail-on-failure
.\.venv\Scripts\python.exe -m glass.cli resident-runtime-compare --run queue32=C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default --run queue64=C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue64_candidate --baseline-label queue32 --out C:\glass_runs\phase2_s2_gate680_completion_ring\gate680_completion_ring_runtime_compare.json --markdown C:\glass_runs\phase2_s2_gate680_completion_ring\gate680_completion_ring_runtime_compare.md
```

## Test Results

- Focused CLI/runtime tests:
  `11 passed, 81 deselected`.
- Focused resident CUDA tests:
  `2 passed, 130 deselected`.
- Phase 2 mainline audit:
  passed, failed checks `[]`, input lights `200`, active frames `193`.
- Resident regression gate:
  passed, failed checks `[]`, elapsed ratio `1.0367292144663716`.
- Runtime compare:
  best label `queue32`, recommendation `best_observed:queue32`.
- Full pytest:
  `1422 passed in 65.33 s`.

## Real 200-Light Timing Summary

- 32-buffer default:
  - total elapsed: `12.245715199969709 s`
  - `light_read_upload_calibrate`: `3.391568800085224 s`
  - `resident_integration`: `3.3890133999520913 s`
  - planned/effective raw ring frames: `32 / 32`
  - estimated/effective pinned raw bytes: `3945676800 / 3945676800`
- 64-buffer candidate:
  - total elapsed: `12.695490699843504 s`
  - `light_read_upload_calibrate`: `4.130420900066383 s`
  - `resident_integration`: `3.3756945999339223 s`
  - requested/planned/effective raw ring frames: `64 / 64 / 64`
  - estimated/effective pinned raw bytes: `7891353600 / 7891353600`

## CUDA Availability

CUDA was available on this workstation. The focused resident CUDA tests and real
200-light resident CUDA runs completed.

## Known Limitations

- This gate adds a real scheduling control surface, but the tested 64-buffer
  candidate is not a default-promotion candidate on this workstation.
- Larger raw rings increase pinned host memory pressure; they should be used
  only for explicit A/B profiling and must pass resident regression before any
  promotion.
- The control is explicit frame-count based, not yet an automatic RAM/PCIe/disk
  adaptive policy.

## Next Step

Move to a larger substantive target:

- deeper read/H2D overlap with adaptive queue/ring policy, or
- deterministic cooperative/segmented resident reducer work.

Do not continue sweeping fixed completion-ring sizes unless a new adaptive
policy or hardware class justifies it.

## Clean-Room Compliance

Compliant. This gate used only GLASS-owned scheduling/profile code, GLASS tests,
and user-owned real benchmark artifacts. It did not read, copy, summarize, or
rework proprietary PixInsight/WBPP/PJSR source, and it did not modify input
image directories.
