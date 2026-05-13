# Gate 13 Status: Validation Speedup Summary Documentation

## Gate

Gate 13: PixInsight/WBPP black-box comparison documentation increment.

## Completed

- Updated `docs/validation.md` with the machine-readable M38 speedup summary artifacts:
  - `runs\benchmarks\m38_wbpp_speedup_summary.json`
  - `runs\benchmarks\m38_wbpp_speedup_summary.md`
- Added the exact command to regenerate the summary from existing GPWBPP/WBPP black-box artifacts.
- Documented planned frame count, active weighted frame count, and zero-weight frame count for the WBPP accepted-mask comparison.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Result

- Full pytest: `175 passed in 8.11s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- This checkpoint records documentation only; it does not re-run GPWBPP or WBPP.
- The referenced summary is generated from existing artifacts under `C:\gpwbpp_runs\final_m38_h_200`.

## Next Step

- Keep validation documentation synchronized when a newer real-data resident audit or benchmark run supersedes the current M38 reference.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
