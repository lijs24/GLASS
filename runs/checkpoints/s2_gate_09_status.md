# S2-Gate 09 Status: Rejection And Variance Integration

Date: 2026-05-31

## Gate

S2-Gate 9: Rejection And Variance Integration.

## Completed

- Promoted the variance map to a formal tile-mode integration artifact.
- Added `output_variance_map` to the integration policy model.
- Updated StackEngine weighted-mean variance to use weighted population variance over valid, unrejected samples.
- Added variance summary metrics to StackEngine results.
- Added variance-map FITS writing for both StackEngine CPU integration and the rejection-free CUDA streaming accumulator path.
- Added `variance_aware` frame weighting using inverse variance from `noise_sigma` or `background_rms`, with median normalization like other non-unit weights.
- Exposed additional tile-mode rejection modes through the CLI: `minmax`, `percentile`, `mad`, and `median_sigma`.
- Updated integration and algorithm-source documentation.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine.py tests\test_cpu_integration.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\integration.py src\glass\engine\stack_engine.py src\glass\models.py src\glass\cli.py tests\test_stack_engine.py tests\test_cpu_integration.py tests\test_pipeline_fixture.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py::test_pipeline_fixture_audit tests\test_pipeline_fixture.py::test_pipeline_fixture_run_integration`
- `.venv\Scripts\glass.exe synthetic --out runs\s2_gate_09_smoke_data --frames 5 --width 40 --height 40 --known-shift`
- `.venv\Scripts\glass.exe audit --root runs\s2_gate_09_smoke_data --out runs\s2_gate_09_smoke --backend cpu --tile-size 8 --local-normalization on --integration-weighting variance_aware --integration-rejection mad`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m pytest -q tests\test_cuda_import.py tests\test_cuda_device_info.py tests\test_cuda_smoke.py tests\test_gpu_integration_vs_cpu.py`

## Test Results

- StackEngine and CPU integration focused tests: 13 passed.
- Pipeline audit and integration focused tests: 2 passed.
- Full test suite: 224 passed in 13.69 s.
- CUDA import/device/smoke/GPU integration tests: 4 passed.
- Ruff check: passed.
- CLI smoke with `variance_aware` weighting and `mad` rejection: completed successfully.

## CUDA

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Artifacts

- `runs/s2_gate_09_smoke_data/`
- `runs/s2_gate_09_smoke/integration_results.json`
- `runs/s2_gate_09_smoke/integration/master_*.fits`
- `runs/s2_gate_09_smoke/integration/weight_map_*.fits`
- `runs/s2_gate_09_smoke/integration/coverage_map_*.fits`
- `runs/s2_gate_09_smoke/integration/variance_map_*.fits`
- `runs/s2_gate_09_smoke/integration/low_rejection_*.fits`
- `runs/s2_gate_09_smoke/integration/high_rejection_*.fits`
- `runs/s2_gate_09_smoke/integration/dq_map_*.fits`

## Known Limitations

- `variance_aware` currently uses frame-level quality proxies (`noise_sigma` or `background_rms`), not a camera-calibrated per-pixel noise model.
- The tile-mode variance map is a population-variance diagnostic over valid, unrejected samples; uncertainty propagation through calibration, warp, LN, and rejection remains future work.
- Additional rejection modes are exposed for tile-mode StackEngine integration. Resident CUDA remains intentionally limited to `none`, `sigma_clip`, and `winsorized_sigma` until equivalent kernels and diagnostics are implemented.
- The 200-light real-data benchmark was not rerun for this gate; this gate primarily formalized maps and CPU/tile StackEngine contracts without changing the resident CUDA benchmark path.

## Next Step

S2-Gate 10: stabilize XISF metadata/cache-safe image input, expand report coverage for all major stages, and rerun the 200-light benchmark against the Phase 1 baseline.

## Clean-Room

Compliant. This gate used public statistical definitions for inverse-variance weighting, weighted population variance, and robust rejection modes. No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
