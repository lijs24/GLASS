# S2-Gate 76 Status: Native Callback Release Calibration Queue

## Gate

S2-Gate 76: Native Callback Release Calibration Queue

## Completed

- Added native `ResidentCalibratedStack.calibrate_frames_host_async_multistream_callback_release_timed`.
- Added reusable per-lane H2D start events so native code can time each H2D wave independently while preserving lane start/stop timing for final calibration sync.
- Added Python wrapper `ResidentCalibratedStack.calibrate_frames_host_async_multistream_callback_release_timed`.
- Added `callback_queue` to `--resident-calibration-release-mode` for `glass run` and `glass audit`.
- Added resident scheduler support for callback queue mode:
  - Python collects up to `resident_calibration_batch_frames`.
  - Native schedules internal waves of `calibration_wave_effective_frames`.
  - Native synchronizes H2D events per wave, calls back to Python to release completed prefetch slots, then performs one final stream synchronization.
- Added resident artifact fields:
  - `calibration_callback_release_supported`
  - `calibration_callback_release_capable`
  - `calibration_callback_release_enabled`
  - `calibration_callback_release_recommended`
  - `calibration_callback_release_count`
  - `calibration_callback_release_s`
  - `calibration_callback_wave_count`
  - `calibration_fetch_batch_frames`
- Added CUDA resident-stack test coverage for callback ordering, output correctness, and timing fields.
- Added resident CLI test coverage showing one Python batch with two native callback waves.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m py_compile src\glass_cuda.py src\glass\engine\resident_cuda.py src\glass\cli.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_callback_release_queue_calibration_matches_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_releases_inside_native_batch
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_callback_release_queue_calibration_matches_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_callback_queue_releases_inside_native_batch tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_release_policy_prefers_full_lanes tests\test_resident_cuda_run.py::test_cli_resident_cuda_batch_wave_releases_prefetch_slots
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_76_200\callback_queue_batch8_stream4_wave4_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 4 --resident-calibration-release-mode callback_queue --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_76_200\callback_queue_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate70b.html --glass-time-seconds 12.3291659001261 --reference-time-seconds 12.200752399861813 --glass-label Gate76_callback_queue --reference-label Gate70_event_reuse_b --ignore-border-px 16
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_76_200\callback_queue_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate73.html --glass-time-seconds 12.3291659001261 --reference-time-seconds 12.239080199971795 --glass-label Gate76_callback_queue --reference-label Gate73_wave2 --ignore-border-px 16
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_76_200\callback_queue_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_75_200\auto_release_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate75.html --glass-time-seconds 12.3291659001261 --reference-time-seconds 12.381055099889636 --glass-label Gate76_callback_queue --reference-label Gate75_auto_release --ignore-border-px 16
```

## Test Results

- Native CUDA build: passed.
- Python compile: passed.
- Ruff: passed.
- Focused callback tests: 2 passed.
- Focused resident calibration policy tests: 4 passed.
- Full pytest: 280 passed in 11.92 s.

## 200-Light Benchmark Results

Dataset: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`

Reference runs:

- Gate70B event reuse: 12.200752399861813 s.
- Gate73 wave 2: 12.239080199971795 s.
- Gate75 auto release: 12.381055099889636 s.

Gate76 callback queue, batch 8, stream 4, wave 4:

- Run path: `C:\glass_runs\phase2_s2_gate_76_200\callback_queue_batch8_stream4_wave4_20260601`
- Total elapsed: 12.3291659001261 s.
- Requested release mode: `callback_queue`.
- Effective release mode: `callback_queue`.
- H2D release reason: `explicit_callback_queue_requested`.
- `light_read_upload_calibrate`: 6.288913500029594 s.
- `light_read_wait_wall`: 2.8056086022406816 s.
- `light_h2d_calibrate_store`: 2.580847699660808 s.
- Native calibration total: 2.5682893999999994 s.
- Native calibration sync: 0.012690200000000002 s.
- Callback release time: 0.0071257000000000004 s.
- Callback release count: 200.
- Native callback waves: 50.
- Python/native calibration batch count: 25.
- Fetch batch frames: 8.
- Prefetch no-slot blocked count: 161.
- Frame accounting: 200 input lights, 193 integrated, 7 zero-weight.

Numerical comparisons:

- Gate76 callback vs Gate70B: RMS diff 0.0, max abs diff 0.0, compared pixels 61139520.
- Gate76 callback vs Gate73: RMS diff 0.0, max abs diff 0.0, compared pixels 61139520.
- Gate76 callback vs Gate75: RMS diff 0.0, max abs diff 0.0, compared pixels 61139520.
- Speed vs Gate70B: 0.9895845752012329x.
- Speed vs Gate73 wave 2: 0.9926932851026538x.
- Speed vs Gate75 auto: 1.0042086545175781x.

Interpretation:

- The callback queue preserves output identity.
- The native calibration section improved versus Gate75: native total dropped from about 2.63 s to about 2.57 s and Python/native calibration calls dropped from 50 to 25.
- End-to-end wall time did not beat Gate70B/Gate73 because `light_read_wait_wall` increased in this run. The next bottleneck remains host I/O/prefetch behavior, not calibration kernel correctness.

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_76_200\callback_queue_batch8_stream4_wave4_20260601`
- `C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate70b.json`
- `C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate73.html`
- `C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate73.json`
- `C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate75.html`
- `C:\glass_runs\phase2_s2_gate_76_200\compare_gate76_callback_vs_gate75.json`

## Known Limitations

- `callback_queue` is explicit and not default.
- Native still calls back into Python after each H2D wave, so this is not a fully native/device-resident ingest queue.
- The callback queue reduces Python/native calibration calls but can increase prefetch no-slot blocking depending on I/O timing.
- Formal 200-light wall time remains slightly behind Gate70B/Gate73 despite local native calibration timing improvement.

## Next Step

S2-Gate 77 should target the host I/O/prefetch side:

- profile why callback queue increased `light_read_wait_wall`;
- test larger pinned ring depth and worker count with callback queue;
- consider separating ring-slot release from immediate `_fill()` submission if callback timing contends with native scheduling;
- keep strict output identity comparisons against Gate70B/Gate73.

## Clean-Room Compliance

- This gate only changes GLASS-owned native CUDA scheduling, Python wrapper/scheduler glue, tests, docs, and artifact accounting.
- No PixInsight or WBPP source code was read, copied, summarized, or reworked.
- The real image input dataset was treated as read-only.
- The benchmark compares GLASS-generated outputs against prior GLASS outputs for regression identity.
