# S2-Gate 75 Status: Resident Calibration Release Auto Policy

## Gate

S2-Gate 75: Resident Calibration Release Auto Policy

## Completed

- Added `auto` to `--resident-calibration-release-mode` for `glass run` and `glass audit`.
- Kept the default release mode as `sync`.
- Added an explicit policy: `auto` enables `h2d_event` only when `calibration_wave_effective_frames == resident_calibration_streams`.
- Kept explicit `h2d_event` available for controlled experiments, including underfilled-lane tests.
- Added resident artifact fields:
  - `calibration_release_mode_effective`
  - `calibration_h2d_release_capable`
  - `calibration_h2d_release_recommended`
  - `calibration_h2d_release_policy`
  - `calibration_h2d_release_reason`
- Added resident CLI tests for both auto-enabled full-lane waves and auto-synchronized underfilled waves.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py src\glass\cli.py
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_batch_wave_releases_prefetch_slots tests\test_resident_cuda_run.py::test_cli_resident_cuda_auto_release_policy_prefers_full_lanes
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_75_probe_200\h2d_release_batch8_stream4_wave4_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 4 --resident-calibration-release-mode h2d_event --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_75_200\auto_release_batch8_stream4_wave4_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 4 --resident-calibration-release-mode auto --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_75_200\auto_release_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_75_200\compare_gate75_auto_vs_gate70b.html --glass-time-seconds 12.381055099889636 --reference-time-seconds 12.200752399861813 --glass-label Gate75_auto_release --reference-label Gate70_event_reuse_b --ignore-border-px 16
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_75_200\auto_release_batch8_stream4_wave4_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_73_200\wave_batch8_stream4_wave2_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_75_200\compare_gate75_auto_vs_gate73.html --glass-time-seconds 12.381055099889636 --reference-time-seconds 12.239080199971795 --glass-label Gate75_auto_release --reference-label Gate73_wave2 --ignore-border-px 16
```

## Test Results

- Native CUDA build: passed, no work to do after Python-only Gate75 edits.
- Python compile: passed.
- Ruff: passed.
- Focused tests: 2 passed.
- Full pytest: 278 passed in 11.91 s.

## 200-Light Benchmark Results

Dataset: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`

Reference runs:

- Gate70B event reuse: 12.200752399861813 s.
- Gate73 wave 2: 12.239080199971795 s.
- Gate74 H2D release wave 2: 12.351992799900472 s.

Gate75 probe, explicit H2D release, batch 8, stream 4, wave 4:

- Run path: `C:\glass_runs\phase2_s2_gate_75_probe_200\h2d_release_batch8_stream4_wave4_20260601`
- Total elapsed: 12.271343299653381 s.
- `light_read_upload_calibrate`: 6.218063899781555 s.
- `light_read_wait_wall`: 2.654892100021243 s.
- `light_h2d_calibrate_store`: 2.664348698221147 s.
- Native calibration total: 2.6492141 s.
- Pending calibration wait after H2D release: 0.022517799999999998 s.
- Batch count: 50.

Gate75 formal auto run, batch 8, stream 4, wave 4:

- Run path: `C:\glass_runs\phase2_s2_gate_75_200\auto_release_batch8_stream4_wave4_20260601`
- Total elapsed: 12.381055099889636 s.
- Requested release mode: `auto`.
- Effective release mode: `h2d_event`.
- H2D release recommended: true.
- H2D release reason: `auto_h2d_event_wave_effective_matches_stream_count`.
- `light_read_upload_calibrate`: 6.223997300025076 s.
- `light_read_wait_wall`: 2.686121301725507 s.
- `light_h2d_calibrate_store`: 2.642012401483953 s.
- Native calibration total: 2.6278389000000004 s.
- Pending calibration wait after H2D release: 0.0230147 s.
- Prefetch no-slot blocked count: 138.
- Batch count: 50.
- Frame accounting: 200 input lights, 193 integrated, 7 zero-weight.

Numerical comparisons:

- Gate75 auto vs Gate70B: RMS diff 0.0, max abs diff 0.0, compared pixels 61139520.
- Gate75 auto vs Gate73: RMS diff 0.0, max abs diff 0.0, compared pixels 61139520.
- Speed vs Gate70B: 0.9854372104337513x.
- Speed vs Gate73 wave 2: 0.9885328916823004x.

Interpretation:

- The auto policy correctly selected `h2d_event` for the full-lane wave 4 configuration and records the effective decision.
- Output identity is preserved.
- This policy is not a performance win versus the best Gate70B/Gate73 runs; it is a guardrail that prevents underfilled-lane auto mode from using the slower Gate74-style path.
- The real next performance step remains a deeper native calibration queue or a larger resident ingest scheduler that reduces Python/native round trips without underfilling lanes.

## CUDA Availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_75_probe_200\h2d_release_batch8_stream4_wave4_20260601`
- `C:\glass_runs\phase2_s2_gate_75_200\auto_release_batch8_stream4_wave4_20260601`
- `C:\glass_runs\phase2_s2_gate_75_200\compare_gate75_auto_vs_gate70b.html`
- `C:\glass_runs\phase2_s2_gate_75_200\compare_gate75_auto_vs_gate70b.json`
- `C:\glass_runs\phase2_s2_gate_75_200\compare_gate75_auto_vs_gate73.html`
- `C:\glass_runs\phase2_s2_gate_75_200\compare_gate75_auto_vs_gate73.json`

## Known Limitations

- `auto` is opt-in; the default remains `sync`.
- The auto rule is intentionally conservative and based on current GLASS benchmark evidence.
- The rule only decides between existing sync and H2D-event release paths; it does not remove native call count or implement a true multi-wave native queue.
- End-to-end wall time remains slightly behind the Gate70B/Gate73 reference runs in the formal Gate75 benchmark.

## Next Step

S2-Gate 76 should move from policy to scheduling:

- prototype a deeper native calibration ingest queue or Python-side two-wave pending queue;
- preserve host-buffer lifetime until H2D completion;
- reduce the number of Python/native calibration calls while keeping lanes filled;
- compare against Gate70B, Gate73 wave 2, and Gate75 auto with strict output identity checks.

## Clean-Room Compliance

- This gate only changes GLASS-owned resident scheduler policy, CLI options, tests, docs, and artifact accounting.
- No PixInsight or WBPP source code was read, copied, summarized, or reworked.
- The real image input dataset was treated as read-only.
- The benchmark compares GLASS-generated outputs against prior GLASS outputs for regression identity.
