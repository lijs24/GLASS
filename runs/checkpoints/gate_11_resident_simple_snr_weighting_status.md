# Gate 11 Status: Resident CUDA Simple SNR Weighting

## Gate

Gate 11: Weighted integration and rejection resident CUDA increment.

## Completed

- Enabled `--integration-weighting simple_snr` for resident CUDA runs.
- Added resident frame-global mean/std weighting from device-side statistics.
- Preserved failed or explicitly excluded frames as weight 0.
- Recorded resident weighting diagnostics in `resident_artifacts.json`.
- Wrote selected frame weights to `integration_results.json` with `weighting: simple_snr`.
- Updated capability flags and integration/CUDA backend documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass\capabilities.py tests\test_resident_cuda_run.py tests\test_capabilities.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_simple_snr_weighting tests\test_capabilities.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cuda_resident_stack.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Targeted simple_snr/capability tests: `2 passed`.
- Resident/CLI subset: `33 passed`.
- Full pytest: `172 passed in 8.22s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- Resident `simple_snr` currently uses global mean/std after calibration/registration; it is not yet the final WBPP-like combined PSF/background/eccentricity/star-count weighting model.
- Weighting diagnostics are per-frame global summaries, not per-tile maps.
- Real M38 comparison runs so far used weighting disabled to match the observed WBPP FastIntegration settings.

## Next Step

- Extend resident weighting toward combined quality metrics once frame-quality and registration diagnostics are fully resident.
- Keep comparing weighted/rejected outputs against CPU baselines on synthetic data before enabling in the large WBPP parity run.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
- Implementation uses project-owned CUDA/Python code and synthetic tests.
