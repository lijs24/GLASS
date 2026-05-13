# Gate 10 Status: Local Normalization

- Gate: 10
- Date: 2026-05-12
- Status: completed
- Commit: pending

## Completed

- Implemented CPU tile statistics for local normalization.
- Implemented CUDA pixel apply kernel `local_norm_apply_f32`.
- Added Python CUDA wrapper with CPU fallback.
- Added tile-streaming local normalization stage after warp.
- Added `glass run --until-stage local_normalization`.
- Added `--local-normalization auto|on|off` so LN can be explicitly enabled or disabled.
- Added `local_norm_results.json` with reference frame, crop box, policy, backend, tile counts, mean scale/offset, valid pixels, and warnings.
- Added Local Normalization summary to HTML reports.
- Expanded `docs/local_normalization_model.md`.

## Commands Run

```powershell
.\.venv\Scripts\python -m pybind11 --cmakedir
cmd /c "call Visual Studio VsDevCmd.bat ... && cmake -S . -B build\native-cuda ... && cmake --build build\native-cuda --config Release"
.\.venv\Scripts\python -m pytest -q tests/test_cpu_local_norm.py tests/test_gpu_local_norm_vs_cpu.py tests/test_pipeline_fixture.py
.\.venv\Scripts\glass synthetic --out runs\gate_10_synth\source --frames 4 --width 48 --height 48 --filter H --known-shift
.\.venv\Scripts\glass audit --root runs\gate_10_synth\source --out runs\gate_10_synth\audit --backend auto
.\.venv\Scripts\glass run --plan runs\gate_10_synth\audit\processing_plan.json --out runs\gate_10_synth\run --backend cuda --until-stage local_normalization --local-normalization on --tile-size 12
.\.venv\Scripts\glass report --run runs\gate_10_synth\run --manifest runs\gate_10_synth\audit\manifest.json --plan runs\gate_10_synth\audit\processing_plan.json --out runs\gate_10_synth\run\report.html
.\.venv\Scripts\python -m pytest -q
```

## Test Result

- Focused Gate 10 tests: 10 passed.
- Full suite: 37 passed.
- CLI artifact check: `local_norm True 4 cuda 16`.

## CUDA Availability

- CUDA native extension: available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Artifacts

- `runs/gate_10_synth/source/`
- `runs/gate_10_synth/audit/manifest.json`
- `runs/gate_10_synth/audit/processing_plan.json`
- `runs/gate_10_synth/run/local_norm_results.json`
- `runs/gate_10_synth/run/local_norm_cache/`
- `runs/gate_10_synth/run/report.html`

## Known Limitations

- Statistics are CPU-controlled in Gate 10; CUDA currently applies already-computed per-tile scale/offset.
- The local model is per tile and nearest-neighbor registered input from Gate 09; no overlapping windows or interpolation between tile coefficients yet.
- Background masking is coverage-based only; sigma/outlier policies are recorded but not fully implemented.
- No crop is applied; `crop_box` is explicitly `null`.

## Next Step

- Gate 11: weighted integration and rejection, consuming local-normalized cache when enabled and emitting master, weight, coverage, low-rejection, and high-rejection maps.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or modified.
- The implementation is based on project-owned code, synthetic data, FITS IO, and clean-room astronomical processing behavior.
- Input data directories were not modified.
