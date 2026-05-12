# Gate 04 Precision Status

## Gate

Precision audit for the resident CUDA calibration plus mean integration path.

## Completed

- Did not read official WBPP/PJSR source code.
- Inspected WBPP black-box XISF output headers and found `sampleFormat="Float32"`
  for the M38 master light, master bias, and a calibrated light output.
- Added reusable precision validation helpers under `gpwbpp.validation.precision`.
- Added `benchmarks/audit_precision.py` for crop-based CPU64/CPU32/CUDA32 audits.
- Added unit tests for precision helper functions.
- Added `docs/precision_model.md`.

## Commands

```powershell
.venv\Scripts\python.exe benchmarks\audit_precision.py --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\precision_audit_512.json --light-limit 16 --calib-limit 20 --crop-size 512 --wbpp-xisf C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --wbpp-xisf C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterBias_BIN-1_9600x6422.xisf --wbpp-xisf C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\calibrated\Light_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono\LIGHT_H_0001_c.xisf
```

## Results

- Crop: central `512 x 512`.
- Lights: 16.
- Calibration frames: 20 bias, 20 dark, 20 flat.
- WBPP black-box XISF output sample format: `Float32`.
- CPU32 integrated master vs CPU64 reference:
  - max absolute error: about `0.00153`.
  - RMSE: about `9.06e-6`.
  - relative RMSE: about `1.13e-7`.
- CUDA32 resident integrated master vs CPU64 reference:
  - max absolute error: about `0.00156`.
  - RMSE: about `1.03e-5`.
  - relative RMSE: about `1.29e-7`.
- CUDA32 resident integrated master vs CPU32 integrated master:
  - max absolute error: about `0.000244`.
  - RMSE: about `5.74e-6`.
  - relative RMSE: about `7.19e-8`.

## Test Result

- Targeted precision/resident tests: 4 passed in 0.10 s.
- Full test suite: 65 passed in 5.49 s.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.

## Known Limitations

- CPU64 is a reference arithmetic path for auditing; it is not claimed to be
  WBPP's internal implementation.
- The precision audit is crop-based, not whole-frame exhaustive.
- Future registration, local normalization, rejection, and model-fitting stages
  need their own precision audits.

## Next Step

Keep CUDA float32 as the high-throughput default for image samples, while adding
stage-specific audits and compensated or float64 accumulation only where measured
drift warrants it.

## Clean Room

Compliant. PixInsight/WBPP was used only as a black-box output generator. No
official WBPP/PJSR source was read or copied.
