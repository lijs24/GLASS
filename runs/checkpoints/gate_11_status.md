# Gate 11 Status: Weighted Integration and Rejection

- Gate: 11
- Date: 2026-05-12
- Status: completed
- Commit: pending

## Completed

- Added tile-streaming integration stage.
- Added `gpwbpp run --until-stage integration`.
- Added `--integration-weighting auto|none|simple_snr`.
- Added `--integration-rejection auto|none|sigma_clip|winsorized_sigma`.
- Implemented CPU weighted integration baseline with coverage support.
- Implemented sigma clipping and winsorized sigma rejection maps.
- Implemented native CUDA `integrate_accumulate_mean_tile_f32` accumulator.
- Integration consumes local-normalized cache when present, otherwise registered cache.
- Integration outputs master, weight map, coverage map, low rejection map, and high rejection map per filter.
- HTML report now includes integration summary.
- Expanded `docs/integration_model.md`.

## Commands Run

```powershell
cmd /c "call Visual Studio VsDevCmd.bat ... && cmake -S . -B build\native-cuda ... && cmake --build build\native-cuda --config Release"
.\.venv\Scripts\python -m pytest -q tests/test_cpu_integration.py tests/test_gpu_integration_vs_cpu.py tests/test_pipeline_fixture.py
.\.venv\Scripts\gpwbpp synthetic --out runs\gate_11_synth\source --frames 5 --width 48 --height 48 --filter H --known-shift
.\.venv\Scripts\gpwbpp audit --root runs\gate_11_synth\source --out runs\gate_11_synth\audit --backend auto
.\.venv\Scripts\gpwbpp run --plan runs\gate_11_synth\audit\processing_plan.json --out runs\gate_11_synth\run --backend cuda --until-stage integration --local-normalization on --integration-weighting simple_snr --integration-rejection winsorized_sigma --tile-size 12
.\.venv\Scripts\gpwbpp report --run runs\gate_11_synth\run --manifest runs\gate_11_synth\audit\manifest.json --plan runs\gate_11_synth\audit\processing_plan.json --out runs\gate_11_synth\run\report.html
.\.venv\Scripts\gpwbpp run --plan runs\gate_11_synth\audit\processing_plan.json --out runs\gate_11_synth\run_cuda_mean --backend cuda --until-stage integration --local-normalization off --integration-weighting none --integration-rejection none --tile-size 12
.\.venv\Scripts\python -m pytest -q
```

## Test Result

- Focused Gate 11 tests: 13 passed.
- Full suite: 40 passed.
- CLI winsorized artifact check: `integration simple_snr winsorized_sigma 1 5 cpu`.
- CLI CUDA accumulator check: `integration_cuda_mean none none cuda 16`.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Artifacts

- `runs/gate_11_synth/source/`
- `runs/gate_11_synth/audit/manifest.json`
- `runs/gate_11_synth/audit/processing_plan.json`
- `runs/gate_11_synth/run/integration_results.json`
- `runs/gate_11_synth/run/integration/master_H.fits`
- `runs/gate_11_synth/run/integration/weight_map_H.fits`
- `runs/gate_11_synth/run/integration/coverage_map_H.fits`
- `runs/gate_11_synth/run/integration/low_rejection_H.fits`
- `runs/gate_11_synth/run/integration/high_rejection_H.fits`
- `runs/gate_11_synth/run/report.html`
- `runs/gate_11_synth/run_cuda_mean/integration_results.json`

## Known Limitations

- Rejection modes are CPU baseline in Gate 11.
- CUDA path currently covers weighted mean accumulation without rejection.
- `combined` weighting is not implemented yet; Gate 11 implements `none` and `simple_snr`.
- Integration groups by FITS filter and assumes already aligned/cropped dimensions.
- Rejection thresholds are per-tile stack statistics and do not yet use advanced masks.

## Next Step

- Gate 12: end-to-end CUDA WBPP-like audit pipeline with resume-aware run artifacts and final master output through one command.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or modified.
- The implementation is based on project-owned code, synthetic data, FITS IO, and clean-room astronomical processing behavior.
- Input data directories were not modified.
