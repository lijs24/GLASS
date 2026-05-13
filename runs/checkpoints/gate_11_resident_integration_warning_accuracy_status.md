# Gate 11 Status: Resident Integration Warning Accuracy

## Gate

Gate 11: Weighted integration and rejection reporting increment.

## Completed

- Fixed resident integration warnings so Winsorized Sigma wording is emitted only when `rejection=winsorized_sigma`.
- Added sigma-clip-specific warning text only for `rejection=sigma_clip`.
- Added regression coverage so a no-rejection simple_snr resident run does not report Winsorized Sigma diagnostics.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_simple_snr_weighting tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Targeted tests: `2 passed`.
- Full pytest: `172 passed in 7.94s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- This checkpoint only corrects reporting accuracy; it does not change the rejection math.

## Next Step

- Continue tightening resident CUDA integration parity and report metadata for real WBPP comparison runs.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
