# S2-Gate 07 Status: Registration And Warp Hardening

Date: 2026-05-31

## Gate

S2-Gate 7: Registration And Warp Hardening.

## Completed

- Added homography to the clean-room CPU registration model ladder using direct linear transform fitting after affine/translation hypotheses provide inlier sets.
- Added per-frame registration validation payloads with matrix shape, finite-value, projective-row, determinant, inlier, RMS, and solution-source checks.
- Kept phase-correlation fallback explicitly labeled as a preview fallback that does not require star inliers.
- Added tile-mode warp interpolator registry with `nearest`, `bilinear`, `bicubic`, and `lanczos3`.
- Added CLI `--warp-interpolation` for tile-mode `run` and `audit`.
- Preserved the existing integer-translation nearest fast path for nearest-equivalent integer shifts.
- Updated registration and algorithm-source documentation.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_warp.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_run_registration tests\test_pipeline_fixture.py::test_pipeline_fixture_run_warp`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m ruff check src\glass\cpu\registration.py src\glass\engine\registration.py src\glass\engine\warp.py src\glass\cli.py tests\test_cpu_registration.py tests\test_cpu_warp.py tests\test_pipeline_fixture.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_warp_vs_cpu.py`
- `.venv\Scripts\python.exe -m glass.cli synthetic --out runs\s2_gate_07_smoke\data --frames 5 --width 48 --height 48 --known-shift`
- `.venv\Scripts\python.exe -m glass.cli audit --root runs\s2_gate_07_smoke\data --out runs\s2_gate_07_smoke\run --backend cpu --tile-size 8 --registration-method star --warp-interpolation lanczos3 --local-normalization on --integration-weighting combined --integration-rejection winsorized_sigma`
- `.venv\Scripts\python.exe -m glass.cli report --run runs\s2_gate_07_smoke\run --out runs\s2_gate_07_smoke\run\report.html --manifest runs\s2_gate_07_smoke\run\manifest.json --plan runs\s2_gate_07_smoke\run\processing_plan.json`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\s2_gate_07_smoke\doctor.json --allow-cpu-only`

## Test Results

- Registration targeted tests: 13 passed.
- Warp targeted tests: 5 passed.
- Pipeline registration/warp targeted tests: 2 passed.
- Full test suite: 219 passed in 12.21 s.
- CUDA import/device/smoke/GPU warp tests: 10 passed.
- Ruff check: passed.

## CUDA

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/s2_gate_07_smoke/data/`
- `runs/s2_gate_07_smoke/run/registration_results.json`
- `runs/s2_gate_07_smoke/run/warp_results.json`
- `runs/s2_gate_07_smoke/run/report.html`
- `runs/s2_gate_07_smoke/doctor.json`

## Known Limitations

- Homography is a first-pass global model; local distortion correction is still future work.
- Bicubic and Lanczos3 tile-mode paths are CPU correctness paths and not optimized for large production runs.
- Lanczos3 reduces edge coverage; the smoke run produced expected NumPy empty-slice warnings in later rejection statistics along fully uncovered edge pixels.
- Resident CUDA warp already has bilinear/Lanczos support, but this gate did not convert the tile-mode registry into a unified CUDA registry.

## Next Step

S2-Gate 8: implement continuous Local Normalization coefficient fields and diagnostics, with explicit crop-box reporting if any crop is introduced.

## Clean-Room

Compliant. This gate used standard geometric transform, DLT homography, and public interpolation formulas. No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
