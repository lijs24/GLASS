# S2-Gate 477 Status: Resident I/O Preset Probe

- Gate: S2-Gate 477
- Status: green checkpoint
- Date: 2026-06-22

## Completed

- Added opt-in `--resident-runtime-preset throughput-v3-io`.
- Kept default resident runtime preset unchanged: `throughput-v1`.
- Ran two explicit real-data I/O/calibration probes and one real-data preset
  validation run on the M38 H-alpha 200-light dataset.
- Compared the v3 preset master against the Gate476 Lanczos3 baseline master.
- Confirmed the v3 scheduling preset does not change the integrated pixels on
  this run.

## v3 Preset

`throughput-v3-io` applies:

- `resident_prefetch_frames=32`
- `resident_prefetch_workers=12`
- `resident_prefetch_refill_mode=queued`
- `resident_h2d_mode=pinned_ring`
- `resident_calibration_batch_frames=16`
- `resident_calibration_streams=4`
- `resident_calibration_wave_frames=4`
- `resident_calibration_release_mode=callback_queue`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests docs
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests\test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v1 tests\test_cli_smoke.py::test_resident_runtime_preset_respects_explicit_overrides
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate477_io_probe\runs\prefetch24_workers10 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-prefetch-frames 24 --resident-prefetch-workers 10
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate477_io_probe\runs\prefetch32_workers12_wave4 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-prefetch-frames 32 --resident-prefetch-workers 12 --resident-calibration-batch-frames 16 --resident-calibration-wave-frames 4 --resident-calibration-streams 4
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate477_io_probe\runs\throughput_v3_io_preset --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate477_io_probe\runs\throughput_v3_io_preset\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate475_ab_matrix_real\runs\throughput_v1_lanczos3_parity\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate477_io_probe\compare\throughput_v3_io_preset_vs_gate476_v1.html --glass-label "GLASS throughput_v3_io_preset" --reference-label "GLASS gate476 throughput_v1" --glass-coverage-map C:\glass_runs\phase2_s2_gate477_io_probe\runs\throughput_v3_io_preset\integration\resident_coverage_map_H.fits --min-coverage 190
```

## Focused Test Results

- `ruff check src tests docs`: passed.
- Focused pytest: `3 passed in 0.28s`.

Full pytest was run after checkpoint edits and is recorded in the final Gate477
summary:

- `python -m pytest -q`: `1118 passed in 42.44s`

## Real Probe Results

Gate476 baseline:

- preset: `throughput-v1`
- total elapsed: `30.953057600010652 s`
- light read/upload/calibrate: `14.113322600023821 s`
- prefetch frames/workers: `12 / 7`
- calibration actual stream count: `2`
- pinned host bytes: `1479628800`

Explicit probe `prefetch24_workers10`:

- total elapsed: `30.18374159996165 s`
- delta vs Gate476: `-0.7693160000490025 s`
- light read/upload/calibrate: `13.259199200023431 s`
- prefetch frames/workers: `24 / 10`
- pinned host bytes: `2959257600`

Explicit probe `prefetch32_workers12_wave4`:

- total elapsed: `30.14285220002057 s`
- delta vs Gate476: `-0.8102053999900818 s`
- light read/upload/calibrate: `13.133229200029746 s`
- prefetch frames/workers: `32 / 12`
- calibration actual stream count: `4`
- pinned host bytes: `3945676800`

Preset validation `throughput-v3-io`:

- total elapsed: `30.96547570003895 s`
- delta vs Gate476: `+0.012418100028298795 s`
- light read/upload/calibrate: `13.745235500042327 s`
- prefetch frames/workers: `32 / 12`
- calibration actual stream count: `4`
- pinned host bytes: `3945676800`

## Numerical Check

`throughput-v3-io` master versus Gate476 baseline:

- shape match: `true`
- coverage fraction: `0.960532609259836`
- RMS difference: `0.0`
- relative RMS difference: `0.0`
- p99 absolute difference: `0.0`
- max absolute difference: `0.0`

## Decision

- Add `throughput-v3-io` as experimental opt-in.
- Do not promote it to default.
- The explicit probe showed a possible I/O scheduling gain, but the preset
  repeat was neutral against Gate476. This is useful evidence, not enough for
  default promotion.

## Artifacts

- `runs/checkpoints/s2_gate_477_io_probe_summary.json`
- `runs/checkpoints/s2_gate_477_status.md`
- Real outputs under `C:\glass_runs\phase2_s2_gate477_io_probe`

## Known Limitations

- This gate is a small real-data probe, not a repeated statistical benchmark.
- The next optimization should target native FITS read cost, prefetch/orchestration
  overhead, or reusable staged caches rather than simply increasing prefetch
  depth further.

## Clean-Room Compliance

- This gate changes only GLASS runtime scheduling presets and consumes
  GLASS-generated artifacts.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Original image directories were not modified.
