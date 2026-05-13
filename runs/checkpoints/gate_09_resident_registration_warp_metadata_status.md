# Gate 09 Resident Registration Warp Metadata Status

## Gate

Gate 09 audit metadata checkpoint.

## Completed Content

- Fixed resident registration top-level warnings to report the actual configured matrix warp interpolation.
- The warning now records `bilinear` or `lanczos3` instead of always saying `bilinear`.
- Extended the resident external-matrix test to assert the top-level warning mentions `lanczos3` when Lanczos3 is selected.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff: passed.
- Targeted resident tests: `2 passed in 0.37s`.
- Full test suite: `168 passed in 7.88s`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- This checkpoint updates audit metadata only. It does not change the registration algorithm.

## Next Step

- Keep resident report metadata aligned with actual execution choices as more warp/LN modes are added.

## Clean-room Compliance

- Compliant. This is project-owned metadata/reporting code.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
