# S2-Gate 71 Status: Opt-In Resident Calibration Batch Enqueue

## Gate

S2-Gate 71: Opt-In Resident Calibration Batch Enqueue

## Completed

- Added native `ResidentCalibratedStack.calibrate_frames_host_async_timed(...)`.
- Added Python wrapper `glass_cuda.ResidentCalibratedStack.calibrate_frames_host_async_timed(...)`.
- Added `--resident-calibration-batch-frames` to `glass run` and `glass audit`.
- Wired resident CUDA pinned-ring mode to optionally enqueue multiple raw-light H2D copies and calibration kernels before one stream synchronization.
- Preserved the default per-frame path with batch size 1.
- Disabled batch calibration for `translation_preview`, because that mode still needs the CPU light array during online registration.
- Added resident artifact fields for requested batch size, enablement, support flag, batch count, frame count, timing model, native total time, stream elapsed time, and sync time.
- Added CUDA resident-stack correctness coverage and resident CLI artifact coverage.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m py_compile src\glass_cuda.py src\glass\engine\resident_cuda.py src\glass\cli.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_simple_snr_weighting
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_8_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_16_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 16 --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_8_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_71_200\compare_gate71_batch8_vs_gate70b.html --glass-time-seconds 12.409931600093842 --reference-time-seconds 12.200752399861813 --glass-label Gate71_batch8 --reference-label Gate70_event_reuse_b --ignore-border-px 16
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_16_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_71_200\compare_gate71_batch16_vs_gate70b.html --glass-time-seconds 13.596701600123197 --reference-time-seconds 12.200752399861813 --glass-label Gate71_batch16 --reference-label Gate70_event_reuse_b --ignore-border-px 16
```

## Test Results

- Native CUDA build: passed, no rebuild needed.
- Ruff: passed.
- Focused tests: 24 passed.
- Full pytest: 274 passed in 11.48 s.

## 200-Light Benchmark Results

Dataset: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`

Reference run:

- Gate70B event reuse: `C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601`
- Total elapsed: 12.200752399861813 s
- `light_h2d_calibrate_store`: 2.8054879987612367 s

Gate71 batch 8:

- Run path: `C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_8_20260601`
- Total elapsed: 12.409931600093842 s
- `light_h2d_calibrate_store`: 2.746413898188621 s
- Native batch total: 2.7336203000000006 s
- Batch count: 25
- Batch frame count: 200
- Compare vs Gate70B: RMS diff 0.0, max abs diff 0.0

Gate71 batch 16:

- Run path: `C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_16_20260601`
- Total elapsed: 13.596701600123197 s
- `light_h2d_calibrate_store`: 1.2902370989322662 s
- Native batch total: 1.2856604999999999 s
- Batch count: 13
- Batch frame count: 200
- Compare vs Gate70B: RMS diff 0.0, max abs diff 0.0

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Native backend: available.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_8_20260601`
- `C:\glass_runs\phase2_s2_gate_71_200\batch_calibration_16_20260601`
- `C:\glass_runs\phase2_s2_gate_71_200\compare_gate71_batch8_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_71_200\compare_gate71_batch8_vs_gate70b.json`
- `C:\glass_runs\phase2_s2_gate_71_200\compare_gate71_batch16_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_71_200\compare_gate71_batch16_vs_gate70b.json`

## Known Limitations

- Batch calibration is opt-in and defaults to one frame per sync.
- The first native batch path uses one reusable raw device buffer and one calibration stream. It reduces Python and per-frame sync overhead, but H2D and calibration are still serialized inside the stream.
- Batch 16 reduces the native H2D plus calibration stream time substantially, but it increases consumer read wait time with the current prefetch-slot release model. It is not a default routing candidate yet.
- True overlap needs multiple raw device buffers, multiple streams or staged stream events, and earlier prefetch slot release after H2D completion.
- `light_h2d` is reported as 0.0 in batch mode because the aggregate timing is reported as `light_calibration_batch_stream_h2d_calibrate_store`.

## Next Step

S2-Gate 72 should turn the batch enqueue mechanism into a true multi-buffer resident calibration pipeline:

- allocate a small ring of raw device buffers;
- enqueue H2D and calibration across streams or event-linked stages;
- release host prefetch slots after each frame's H2D has completed instead of after the whole batch sync;
- keep result identity checks against Gate70B and rerun 200-light timing.

## Clean-Room Compliance

- This gate only changes GLASS-owned CUDA scheduling and Python orchestration.
- No PixInsight or WBPP source code was read, copied, summarized, or reworked.
- The real image input dataset was treated as read-only.
- The benchmark compares GLASS-generated outputs only against prior GLASS Gate70B output for regression identity.
