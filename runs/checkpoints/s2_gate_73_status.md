# S2-Gate 73 Status: Resident Calibration Wave Scheduler

## Gate

S2-Gate 73: Resident Calibration Wave Scheduler

## Completed

- Added `--resident-calibration-wave-frames` to `glass run` and `glass audit`.
- Added an opt-in wave scheduler that splits a larger resident calibration batch into smaller native waves.
- Pinned prefetch slots are released after each wave synchronization when wave mode is enabled.
- Preserved default behavior with wave size `0`.
- Added prefetch accounting to `_LightPrefetcher`: no-slot blocked count, release count, and maximum in-flight pinned slots.
- Added resident artifact fields for requested wave size, effective wave size, wave enablement, release mode, prefetch no-slot blocked count, release count, and max in-flight slots.
- Added resident CLI coverage for wave scheduling.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\cli.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_simple_snr_weighting tests\test_resident_cuda_run.py::test_cli_resident_cuda_batch_wave_releases_prefetch_slots
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave4_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 4 --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_73_200\compare_gate73_wave2_vs_gate70b.html --glass-time-seconds 12.239080199971795 --reference-time-seconds 12.200752399861813 --glass-label Gate73_batch8_stream4_wave2 --reference-label Gate70_event_reuse_b --ignore-border-px 16
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_73_200\compare_gate73_wave4_vs_gate70b.html --glass-time-seconds 12.36963939992711 --reference-time-seconds 12.200752399861813 --glass-label Gate73_batch8_stream4_wave4 --reference-label Gate70_event_reuse_b --ignore-border-px 16
```

## Test Results

- Native CUDA build: passed, no rebuild needed.
- Ruff: passed.
- Focused tests: 2 passed.
- Full pytest: 276 passed in 11.58 s.

## 200-Light Benchmark Results

Dataset: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`

Reference runs:

- Gate70B event reuse: 12.200752399861813 s
- Gate72 batch 8 stream 4: 12.381431499961764 s

Gate73 batch 8, stream 4, wave 4:

- Run path: `C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave4_20260601`
- Total elapsed: 12.36963939992711 s
- `light_read_upload_calibrate`: 6.190882700029761 s
- `light_read_wait_wall`: 2.6235861997120082 s
- `light_h2d_calibrate_store`: 2.6871737991459668 s
- Native batch total: 2.6590263000000007 s
- Native wave count: 50
- Prefetch no-slot blocked count: 138
- Prefetch release count: 200
- Max in-flight pinned slots: 16
- Compare vs Gate70B: RMS diff 0.0, max abs diff 0.0

Gate73 batch 8, stream 4, wave 2:

- Run path: `C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601`
- Total elapsed: 12.239080199971795 s
- `light_read_upload_calibrate`: 6.195350099820644 s
- `light_read_wait_wall`: 2.5700754011049867 s
- `light_h2d_calibrate_store`: 2.7511250958777964 s
- Native batch total: 2.7145695000000005 s
- Native wave count: 100
- Prefetch no-slot blocked count: 92
- Prefetch release count: 200
- Max in-flight pinned slots: 16
- Compare vs Gate70B: RMS diff 0.0, max abs diff 0.0
- Speed vs Gate70B: 0.9968684084519627x
- Speed vs Gate72 batch 8 stream 4: 1.0116308052534804x

Best Gate73 run by total time: batch 8, stream 4, wave 2.

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Native backend: available.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave4_20260601`
- `C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601`
- `C:\glass_runs\phase2_s2_gate_73_200\compare_gate73_wave2_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_73_200\compare_gate73_wave2_vs_gate70b.json`
- `C:\glass_runs\phase2_s2_gate_73_200\compare_gate73_wave4_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_73_200\compare_gate73_wave4_vs_gate70b.json`

## Known Limitations

- Wave scheduling is opt-in and defaults to disabled.
- Wave 2 reduces host read wait and improves total time versus Gate72, but it increases native calibration wave count and slightly raises native H2D plus calibration time versus a larger wave.
- End-to-end wall time is still marginally behind Gate70B in this run, although the gap is now small.
- True early host-slot release still needs a native H2D completion event/queue so the slot can be released before the calibration kernel wave completes.

## Next Step

S2-Gate 74 should move beyond wave-level release:

- expose per-frame or per-lane H2D completion events from native code;
- release Python pinned prefetch slots after H2D completion rather than after wave synchronization;
- keep host arrays alive safely until H2D completion;
- benchmark against Gate73 wave 2 and Gate70B.

## Clean-Room Compliance

- This gate only changes GLASS-owned scheduler and artifact accounting.
- No PixInsight or WBPP source code was read, copied, summarized, or reworked.
- The real image input dataset was treated as read-only.
- The benchmark compares GLASS-generated outputs against prior GLASS Gate70B output for regression identity.
