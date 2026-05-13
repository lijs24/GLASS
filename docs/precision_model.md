# Precision Model

GLASS is a clean-room project, so official WBPP/PJSR source code is not used to
determine implementation details. Precision behavior is established from
black-box output metadata, public file formats, and GLASS's own numerical
audits.

## Black-Box WBPP Evidence

For the M38 H 200-frame benchmark, inspected WBPP-generated XISF output headers
declared:

- `masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`:
  `sampleFormat="Float32"`.
- `masterBias_BIN-1_9600x6422.xisf`: `sampleFormat="Float32"`.
- `LIGHT_H_0001_c.xisf`: `sampleFormat="Float32"`.

This proves the observed WBPP output images for this run are 32-bit floating
point samples. It does not prove every internal WBPP temporary variable or every
PixInsight process uses only 32-bit arithmetic.

## GLASS Current Defaults

- Calibration CPU baseline: float32 input/output arithmetic.
- CUDA calibration: float32 kernel arithmetic.
- CPU mean integration: float64 accumulation over float32 frames, final float32
  output.
- Resident CUDA mean integration: float32 resident stack and float32
  accumulation, final float32 output.

The current CUDA resident path is therefore optimized for throughput and matches
the observed WBPP output sample format, but it is not bit-equivalent to a
float64 accumulator.

## M38 Precision Audit

Command:

```powershell
.venv\Scripts\python.exe benchmarks\audit_precision.py --plan C:\glass_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\final_m38_h_200\precision_audit_512.json --light-limit 16 --calib-limit 20 --crop-size 512 --wbpp-xisf C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --wbpp-xisf C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterBias_BIN-1_9600x6422.xisf --wbpp-xisf C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\calibrated\Light_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono\LIGHT_H_0001_c.xisf
```

Result artifact:

`C:\glass_runs\final_m38_h_200\precision_audit_512.json`

On the central `512 x 512` crop with 16 lights and 20 calibration frames each:

- CPU32 calibrated frames vs CPU64 reference:
  - max absolute error over frames: about `0.00159`.
  - mean max absolute error over frames: about `0.00153`.
- CUDA32 calibrated frames vs CPU32:
  - max absolute error over frames: `0.0` for this crop and kernel.
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

These errors are far below normal sky background, read noise, and photon noise
for this dataset. Float32 CUDA arithmetic is therefore not expected to be a
material source of scientific error for the tested calibration plus mean
integration path.

## Policy

- Keep float32 CUDA as the default high-throughput image sample format.
- Keep CPU float64 reference paths and crop audits for verification.
- For stages with long accumulations, rejection statistics, or local model
  fitting, evaluate float64 or compensated accumulation where precision audits
  show measurable drift.
- Report sample format and accumulation policy in benchmark and validation
  artifacts.
