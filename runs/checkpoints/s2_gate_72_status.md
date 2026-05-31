# S2-Gate 72 Status: Multi-Stream Resident Calibration Batch

## Gate

S2-Gate 72: Multi-Stream Resident Calibration Batch

## Completed

- Added native `ResidentCalibratedStack.calibrate_frames_host_async_multistream_timed(...)`.
- Added reusable native calibration lanes: one raw-light device buffer, CUDA stream, start event, and stop event per lane.
- Added Python wrapper and read-only properties for calibration lane count and lane buffer bytes.
- Added `--resident-calibration-streams` to `glass run` and `glass audit`.
- Wired resident CUDA pinned-ring batch mode to use the multistream native path when both batch size and stream count are above one.
- Preserved default single-frame and single-stream behavior.
- Added resident artifact fields for requested stream count, actual stream count, lane buffer bytes, multistream support, multistream enablement, mode, and timing model.
- Added CUDA resident-stack correctness coverage and resident CLI artifact coverage.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m py_compile src\glass_cuda.py src\glass\engine\resident_cuda.py src\glass\cli.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_simple_snr_weighting
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream4_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream2_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 2 --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_72_200\compare_gate72_b8s4_vs_gate70b.html --glass-time-seconds 12.381431499961764 --reference-time-seconds 12.200752399861813 --glass-label Gate72_batch8_stream4 --reference-label Gate70_event_reuse_b --ignore-border-px 16
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream2_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_72_200\compare_gate72_b8s2_vs_gate70b.html --glass-time-seconds 12.894521200098097 --reference-time-seconds 12.200752399861813 --glass-label Gate72_batch8_stream2 --reference-label Gate70_event_reuse_b --ignore-border-px 16
```

## Test Results

- Native CUDA build: passed.
- Ruff: passed.
- Focused tests: 25 passed.
- Full pytest: 275 passed in 11.43 s.

## 200-Light Benchmark Results

Dataset: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`

Reference run:

- Gate70B event reuse: `C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601`
- Total elapsed: 12.200752399861813 s
- `light_h2d_calibrate_store`: 2.8054879987612367 s

Gate72 batch 8, streams 4:

- Run path: `C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream4_20260601`
- Total elapsed: 12.381431499961764 s
- `light_h2d_calibrate_store`: 2.65192440059036 s
- Native batch total: 2.6356558000000003 s
- Stream H2D plus calibration elapsed: 2.616549015045166 s
- Sync time: 2.6143442 s
- Batch count: 25
- Batch frame count: 200
- Actual stream count: 4
- Lane buffer bytes: 986419200
- Compare vs Gate70B: RMS diff 0.0, max abs diff 0.0

Gate72 batch 8, streams 2:

- Run path: `C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream2_20260601`
- Total elapsed: 12.894521200098097 s
- `light_h2d_calibrate_store`: 2.7300530010834336 s
- Native batch total: 2.7147154999999996 s
- Actual stream count: 2
- Lane buffer bytes: 493209600
- Compare vs Gate70B: RMS diff 0.0, max abs diff 0.0

Best Gate72 run by total time: batch 8, streams 4.

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Native backend: available.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream4_20260601`
- `C:\glass_runs\phase2_s2_gate_72_200\multistream_batch8_stream2_20260601`
- `C:\glass_runs\phase2_s2_gate_72_200\compare_gate72_b8s4_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_72_200\compare_gate72_b8s4_vs_gate70b.json`
- `C:\glass_runs\phase2_s2_gate_72_200\compare_gate72_b8s2_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_72_200\compare_gate72_b8s2_vs_gate70b.json`

## Known Limitations

- Multistream calibration is opt-in and defaults to one stream.
- The native H2D plus calibration segment improves versus Gate70B and Gate71 batch 8, but end-to-end total time still does not beat Gate70B in the best measured run.
- The main remaining drag is host read/prefetch wait. The Python prefetch slot is still released only after the native batch returns, so larger batches can starve the prefetch ring.
- Stream 4 was better than stream 2 for the measured 200-light dataset, but it is not a default routing candidate yet.
- Host arrays must remain alive until the native batch synchronizes. Earlier host-slot release will require a more explicit H2D completion handshake or a persistent native ingest queue.

## Next Step

S2-Gate 73 should reduce host read wait rather than only native calibration time:

- split resident calibration batches into smaller waves while keeping multistream lanes;
- or expose per-frame H2D completion events so Python can release pinned prefetch slots before calibration finishes;
- record prefetch starvation counters and batch wave occupancy;
- rerun 200-light benchmark against Gate70B and Gate72 batch 8 stream 4.

## Clean-Room Compliance

- This gate only changes GLASS-owned CUDA resource allocation and scheduling.
- No PixInsight or WBPP source code was read, copied, summarized, or reworked.
- The real image input dataset was treated as read-only.
- The benchmark compares GLASS-generated outputs against prior GLASS Gate70B output for regression identity.
