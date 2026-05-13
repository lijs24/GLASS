# Gate 13 Validation Docs Status

## Gate

Gate 13 validation documentation checkpoint.

## Completed Content

- Updated `docs/validation.md` with the current strongest M38 real-data black-box comparison.
- Recorded the WBPP black-box reference path, GPWBPP resident CUDA output path, runtime, speedup, full-frame compare metrics, coverage-masked compare metrics, diagnostics reports, and known interpretation limits.

## Commands Run

```powershell
git diff --check docs\validation.md
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Diff whitespace check: passed, with only Git LF-to-CRLF warning.
- Full test suite: `168 passed in 7.88s`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- This is documentation of the current validation evidence, not a new algorithmic capability.
- The validation still records Local Normalization as disabled for the strongest WBPP parity benchmark.

## Next Step

- Keep `docs/validation.md` synchronized as Local Normalization, boundary policy, and rejection parity improve.

## Clean-room Compliance

- Compliant. The documented comparison uses GPWBPP-owned outputs and user-generated PixInsight/WBPP black-box artifacts only.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
