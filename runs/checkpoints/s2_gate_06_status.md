# S2-Gate 06 Status: Star/PSF Quality And Weighting

Date: 2026-05-31

## Gate

S2-Gate 6: Star/PSF Quality And Weighting.

## Completed

- Added a DAOFIND-like clean-room star detector based on robust background/noise, thresholded local maxima, centroiding, and second-moment PSF estimates.
- Added per-star and per-frame metrics: median FWHM, FWHM IQR, median eccentricity, median star SNR, median star flux, background mean/MAD, noise MAD, saturation fraction, quality score, and weight components.
- Added tile-streaming quality measurement using PSF-sized tile halos while keeping scratch median/MAD storage out-of-core.
- Added `combined` integration weighting for tile mode, using quality score normalized by median positive weight.
- Updated registration to use robust MAD-derived noise from `frame_quality.json` when available.
- Updated HTML report quality summary with detector and weight source.
- Updated algorithm source tracking and integration model documentation.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_star_detect.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cpu_integration.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_run_quality_and_report`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_run_integration`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli synthetic --out runs\s2_gate_06_smoke\data --frames 5 --width 40 --height 40 --known-shift`
- `.venv\Scripts\python.exe -m glass.cli audit --root runs\s2_gate_06_smoke\data --out runs\s2_gate_06_smoke\run --backend cpu --tile-size 8 --local-normalization on --integration-weighting combined --integration-rejection winsorized_sigma`
- `.venv\Scripts\python.exe -m glass.cli report --run runs\s2_gate_06_smoke\run --out runs\s2_gate_06_smoke\run\report.html --manifest runs\s2_gate_06_smoke\run\manifest.json --plan runs\s2_gate_06_smoke\run\processing_plan.json`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\s2_gate_06_smoke\doctor.json --allow-cpu-only`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\cpu\star_detect.py src\glass\cpu\metrics.py src\glass\engine\quality.py src\glass\engine\integration.py tests\test_cpu_star_detect.py tests\test_cpu_integration.py tests\test_pipeline_fixture.py`

## Test Results

- Targeted star/quality tests: 5 passed.
- Targeted integration tests: 5 passed.
- Targeted pipeline quality and integration tests: passed.
- Full test suite: 215 passed in 12.63 s.
- CUDA smoke tests: 3 passed.
- Ruff check: passed.

## CUDA

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/s2_gate_06_smoke/data/`
- `runs/s2_gate_06_smoke/run/frame_quality.json`
- `runs/s2_gate_06_smoke/run/integration_results.json`
- `runs/s2_gate_06_smoke/run/report.html`
- `runs/s2_gate_06_smoke/doctor.json`

## Known Limitations

- The detector is DAOFIND-like and independently implemented, but it is not a full DAOPHOT/DAOFIND reproduction.
- Deblending, aperture correction, spatial PSF modeling, and resident CUDA PSF-quality metrics remain future work.
- `combined` weighting is currently tile-mode only; resident CUDA still accepts `none` and `simple_snr` only.
- The weighting formula is project-defined and will need real-data tuning against the 200-light benchmark.

## Next Step

S2-Gate 7: harden registration and warp with robust matching/model validation and interpolator registry while preserving current CUDA performance artifacts.

## Clean-Room

Compliant. This gate used public photometry concepts and standard image-moment formulas. No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
