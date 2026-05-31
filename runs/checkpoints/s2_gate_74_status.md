# S2-Gate 74 Status: Resident H2D Completion Release

## Gate

S2-Gate 74: Resident H2D Completion Release

## Completed

- Added native `ResidentCalibratedStack.calibrate_frames_host_async_multistream_h2d_release_timed`.
- Added native `ResidentCalibratedStack.finish_pending_calibration_timed`.
- Added reusable per-lane H2D completion events for resident multistream calibration lanes.
- Added Python wrapper methods in `glass_cuda.ResidentCalibratedStack`.
- Added `--resident-calibration-release-mode {sync,h2d_event}` to `glass run` and `glass audit`.
- Wired the resident pinned-ring scheduler so `h2d_event` mode releases pinned prefetch slots after native H2D completion and then waits for pending calibration completion.
- Restricted the first implementation to one frame per calibration lane for safe host-buffer lifetime.
- Added resident artifact fields for release mode, support, enablement, release count, H2D release timing, H2D event timing, and pending wait timing.
- Added CUDA resident-stack and resident CLI tests for the new release path.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m py_compile src\glass_cuda.py src\glass\engine\resident_cuda.py src\glass\cli.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_h2d_release_batch_calibration_matches_cpu tests\test_resident_cuda_run.py::test_cli_resident_cuda_batch_wave_releases_prefetch_slots
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_74_200\h2d_release_batch8_stream4_wave2_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode h2d_event --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_74_200\h2d_release_batch8_stream4_wave2_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_74_200\compare_gate74_vs_gate70b.html --glass-time-seconds 12.351992799900472 --reference-time-seconds 12.200752399861813 --glass-label Gate74_h2d_release --reference-label Gate70_event_reuse_b --ignore-border-px 16
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_74_200\h2d_release_batch8_stream4_wave2_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_74_200\compare_gate74_vs_gate73.html --glass-time-seconds 12.351992799900472 --reference-time-seconds 12.239080199971795 --glass-label Gate74_h2d_release --reference-label Gate73_wave2 --ignore-border-px 16
```

## Test Results

- Native CUDA build: passed.
- Python compile: passed.
- Ruff: passed.
- Focused tests: 2 passed.
- Full pytest: 277 passed in 11.61 s.

## 200-Light Benchmark Results

Dataset: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`

Reference runs:

- Gate70B event reuse: 12.200752399861813 s.
- Gate73 wave 2: 12.239080199971795 s.

Gate74 H2D-event release, batch 8, stream 4, wave 2:

- Run path: `C:\glass_runs\phase2_s2_gate_74_200\h2d_release_batch8_stream4_wave2_20260601`
- Total elapsed: 12.351992799900472 s.
- `master_build_or_load`: 0.5009085000492632 s.
- `resident_allocate_and_master_upload`: 0.0975507996045053 s.
- `light_read_upload_calibrate`: 6.2682782001793385 s.
- `light_read_wait_wall`: 2.7255227975547314 s.
- `light_h2d_calibrate_store`: 2.634994194842875 s.
- Native calibration batch total: 2.614631600000001 s.
- Native stream H2D/calibrate/store elapsed: 2.584142464160918 s.
- Native calibration batch sync: 0.05033009999999999 s.
- `resident_registration_warp`: 1.3972886013798416 s.
- `resident_integration`: 0.2967151999473572 s.
- `output_write`: 0.18299539992585778 s.
- `calibration_batch_mode`: `host_async_multistream_h2d_release_batch`.
- `calibration_release_mode_requested`: `h2d_event`.
- `calibration_h2d_release_enabled`: true.
- `calibration_h2d_release_count`: 200.
- `calibration_h2d_release_s`: 2.5447654999999996 s.
- `calibration_h2d_event_sync_s`: 2.5124962000000006 s.
- `calibration_h2d_event_elapsed_s`: 2.512348001003267 s.
- `calibration_pending_wait_sync_s`: 0.05033009999999999 s.
- Prefetch release count: 200.
- Prefetch no-slot blocked count: 92.
- Frame accounting: 200 input lights, 193 integrated, 7 zero-weight.

Numerical comparisons:

- Gate74 vs Gate70B: RMS diff 0.0, max abs diff 0.0, compared pixels 61139520.
- Gate74 vs Gate73: RMS diff 0.0, max abs diff 0.0, compared pixels 61139520.
- Speed vs Gate70B: 0.9877557894917265x.
- Speed vs Gate73 wave 2: 0.9908587543922802x.

Interpretation:

- The H2D-event release path is functionally correct and preserves output identity.
- This first opt-in release path did not improve wall time on the 200-light run; it added clearer lifetime/timing evidence but remains slightly slower than Gate70B and Gate73.
- The useful signal is that pending calibration wait after H2D release is only about 0.05 s total, so the next optimization should reduce repeated host/native wave orchestration or make a deeper native queue rather than merely splitting release points.

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_74_200\h2d_release_batch8_stream4_wave2_20260601`
- `C:\glass_runs\phase2_s2_gate_74_200\compare_gate74_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_74_200\compare_gate74_vs_gate70b.json`
- `C:\glass_runs\phase2_s2_gate_74_200\compare_gate74_vs_gate73.html`
- `C:\glass_runs\phase2_s2_gate_74_200\compare_gate74_vs_gate73.json`

## Known Limitations

- The H2D-event release path is opt-in and defaults to `sync`.
- The first implementation requires wave frame count to be less than or equal to the calibration stream count so each released host buffer has its own H2D completion event.
- The Python scheduler currently waits for pending calibration immediately after releasing slots; this lets the prefetch thread refill, but it is not yet a full native multi-wave queue.
- The 200-light result is numerically identical but not faster than Gate70B/Gate73.

## Next Step

S2-Gate 75 should use the Gate74 timing evidence to remove more host orchestration:

- consider a deeper native resident calibration queue with multiple pending H2D-complete waves;
- keep pinned host arrays alive until H2D events retire, then release slots from Python;
- benchmark whether fewer Python/native round trips beats the current wave scheduler;
- preserve the same output identity checks against Gate70B/Gate73.

## Clean-Room Compliance

- This gate only changes GLASS-owned native CUDA scheduling, Python scheduler glue, tests, and artifact accounting.
- No PixInsight or WBPP source code was read, copied, summarized, or reworked.
- The real image input dataset was treated as read-only.
- The benchmark compares GLASS-generated outputs against prior GLASS outputs for regression identity.
