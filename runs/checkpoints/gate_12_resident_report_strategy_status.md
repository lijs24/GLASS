# Gate 12 Status: Resident Report Strategy Fields

## Gate

Gate 12: End-to-end CUDA report/audit increment.

## Completed

- Expanded the HTML resident CUDA summary table to include key processing strategy fields:
  - resident registration mode
  - resident warp interpolation
  - resident local-normalization mode
  - resident integration weighting
  - resident rejection mode
  - resident weighting and LN timings
- Added report test coverage confirming resident registration/LN/weighting/rejection strings appear in `report.html`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\html_report.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke
.\.venv\Scripts\python.exe -m pytest -q tests\test_cli_smoke.py tests\test_blackbox_package.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Targeted report/resident audit tests: `2 passed`.
- CLI/blackbox report subset: `7 passed`.
- Full pytest: `173 passed in 8.22s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- The HTML report summarizes resident strategy fields but does not yet render detailed per-frame resident weighting/LN coefficient tables.

## Next Step

- Add richer per-frame resident diagnostics to report artifacts only where it remains readable, or link detailed JSON diagnostics from the report.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
