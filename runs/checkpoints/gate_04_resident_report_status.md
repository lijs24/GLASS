# Gate 04 Resident Report Status

## Gate

Resident CUDA report/audit visibility.

## Completed

- `glass report` now reads `resident_artifacts.json` when present.
- HTML reports now include a `Resident CUDA summary` section.
- The resident section reports backend, GPU name, frame count, calibration frame
  counts, resident base VRAM, estimated peak VRAM, calibration timing,
  integration timing, and write timing.
- Regenerated the M38 formal resident report and confirmed the resident summary
  contains 200 lights, 20 bias, 20 dark, 20 flat, 46.852 GiB resident base VRAM,
  and 47.312 GiB estimated peak VRAM.

## Commands

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py tests/test_resident_cuda_run.py
.venv\Scripts\python.exe -m glass.cli report --run C:\glass_runs\final_m38_h_200\glass_resident_formal_run --out C:\glass_runs\final_m38_h_200\glass_resident_formal_run\report.html
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Targeted report/resident tests: 4 passed in 0.35 s.
- Full test suite: 67 passed in 5.60 s.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.

## Artifacts

- `C:\glass_runs\final_m38_h_200\glass_resident_formal_run\report.html`

## Known Limitations

- This report visibility gate does not make the resident path a complete
  WBPP-equivalent pipeline.
- Final validation still requires a full same-flow WBPP vs GLASS comparison
  with both speedup and image-result agreement.

## Next Step

Implement XISF Float32 read/compare support so GLASS can compare directly
against WBPP black-box master outputs.

## Clean Room

Compliant. The report consumes GLASS artifacts and black-box run products only.
No official WBPP/PJSR source was read or copied.
