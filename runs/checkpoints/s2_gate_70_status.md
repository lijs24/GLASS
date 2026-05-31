# S2-Gate 70 Status: Reused Resident Calibration Events

## Gate

S2-Gate 70 - Reused Resident Calibration Events.

## Completed

- Replaced per-frame CUDA event allocation in resident `pinned_async` and `pinned_ring` calibration timing paths with reusable stack-lifetime CUDA events.
- Preserved the existing pageable, pinned async, and pinned-ring H2D/calibration behavior and event-based timing semantics.
- Added `event_mode` to native resident calibration timing dictionaries:
  - `none` for pageable upload;
  - `reused_stack_events` for pinned async and host/pinned-ring async paths.
- Added resident artifact fields under `resident_io_pipeline`:
  - `calibration_event_mode`;
  - `calibration_event_modes`;
  - `calibration_event_reuse`.
- Added unit/CLI assertions for event reuse in resident stack tests and pinned-ring resident CLI smoke.
- Updated Phase 2 plan with S2-Gate 70.

## Commands Run

```powershell
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_69_200\native_batch_matrix_warp_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_70_200\compare_gate70b_vs_gate69.html --glass-time-seconds 12.200752399861813 --reference-time-seconds 12.512505700346082 --glass-label Gate70_event_reuse_b --reference-label Gate69_native_batch --ignore-border-px 16
```

## Test Results

- Native CUDA build: succeeded.
- Ruff: `All checks passed!`.
- Focused resident/CUDA tests: `23 passed in 2.22s`.
- Full pytest: `273 passed in 11.47s`.
- 200-light real M38 H-alpha resident CUDA runs: both succeeded through integration.

## 200-Light Result

### Gate70 A

- Run output: `C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_20260601`
- Total elapsed: `12.339389800094068 s`.
- `light_read_upload_calibrate`: `6.231226600240916 s`.
- `light_h2d_calibrate_store`: `2.81951039750129 s`.
- `light_h2d`: `2.615868265628815 s`.
- `light_calibrate_store`: `0.14595167988538743 s`.
- `resident_registration_warp`: `1.408388598356396 s`.
- Event mode: `reused_stack_events`.

### Gate70 B

- Run output: `C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601`
- Total elapsed: `12.200752399861813 s`.
- `light_read_upload_calibrate`: `6.230851400177926 s`.
- `light_h2d_calibrate_store`: `2.8054879987612367 s`.
- `light_h2d`: `2.605731456279755 s`.
- `light_calibrate_store`: `0.14396553617715835 s`.
- `resident_registration_warp`: `1.4119865987449884 s`.
- Event mode: `reused_stack_events`.

## Comparison

- Compared Gate70 B master against Gate69 master:
  - Report: `C:\glass_runs\phase2_s2_gate_70_200\compare_gate70b_vs_gate69.html`
  - Shape match: true.
  - Ignored border: 16 px.
  - RMS difference: `0`.
  - Max absolute difference: `0`.
  - Speedup vs Gate69 single run: `1.02555197338x`.

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA Toolkit used for local native build: 13.2.

## Known Limitations

- Reusing events removes a per-frame native overhead but does not change the fundamental H2D bandwidth limit.
- `light_read_upload_calibrate` remains around `6.23 s` for this 200-light run; the next meaningful speed step must reduce H2D volume, pipeline H2D and calibration more deeply, or move more of the raw-frame path into a multi-frame native scheduler.
- Results are subject to cache and USB/external-disk variability, so Gate70 is treated as a small optimization plus stronger observability, not a major throughput gate.

## Next Step

S2-Gate 71 should implement a deeper raw-light scheduler, preferably with a native multi-frame calibration pipeline that can hold multiple raw device buffers and overlap H2D for frame N+1 with calibration for frame N, or with a compact raw `uint16` resident preload path when the dataset fits VRAM.

## Clean-Room

Compliant. This gate only changes GLASS native CUDA event management and GLASS resident artifacts. It does not read, copy, summarize, or rework PixInsight/WBPP implementation source.
