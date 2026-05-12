# Gate 13 Stage Compare Status

Gate: 13 (PixInsight/WBPP black-box comparison, partial stage-alignment checkpoint)

Completed:

- Added explicit candidate scale/offset/clip support to `gpwbpp compare`.
- Added a WBPP stage comparison benchmark for GPWBPP resident masters and WBPP
  black-box XISF master/calibrated outputs.
- Re-ran M38 H light 0001 stage comparison against WBPP outputs.
- Documented the current M38 200-light WBPP black-box timing, observed
  FastIntegration settings, stage agreement, and remaining parity gaps.

Commands run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_compare_report.py tests\test_xisf_io.py
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --help
.\.venv\Scripts\python.exe benchmarks\compare_wbpp_stages.py --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --gpwbpp-run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run --wbpp-run C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox --out C:\gpwbpp_runs\final_m38_h_200\stage_compare_light_0001_v2.json --light-index 1
.\.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\gpwbpp_runs\final_m38_h_200\resident_vs_wbpp_pedestal_scaled_compare.html --gpwbpp-time-seconds 58.9810051000095 --reference-time-seconds 1092.541 --gpwbpp-label GPWBPP-resident-pedestal-scaled --reference-label PixInsight-WBPP-fastIntegration --gpwbpp-scale 0.000015259021896696421 --gpwbpp-offset 0.015259021896696421 --clip-low 0 --clip-high 1
.\.venv\Scripts\python.exe -m pytest -q
```

Test results:

- Targeted tests: 5 passed.
- Full suite: 71 passed in 5.58 s.

CUDA availability:

- CUDA resident mode is available on this workstation.
- Formal M38 resident run used NVIDIA RTX PRO 6000 Blackwell Workstation Edition
  through the native `gpwbpp_cuda` backend.

Artifacts:

```text
C:\gpwbpp_runs\final_m38_h_200\stage_compare_light_0001_v2.json
C:\gpwbpp_runs\final_m38_h_200\resident_vs_wbpp_pedestal_scaled_compare.json
C:\gpwbpp_runs\final_m38_h_200\resident_vs_wbpp_pedestal_scaled_compare.html
```

Observed comparison:

- Master bias/dark/flat agree closely after expected scale differences.
- Calibrated light 0001 agrees in the robust central fit region; WBPP calibrated
  output carries a 1000 ADU pedestal convention in metadata.
- Final resident mean integration remains not equivalent to WBPP
  FastIntegration, because WBPP aligned 193/200 frames, used Lanczos3
  interpolation, ran cosmetic correction, and applied Winsorized Sigma
  Clipping.

Known limitations:

- This is not a full Gate 13 completion.
- The current GPWBPP resident path proves speed for high-VRAM calibration plus
  mean integration, but not final master parity.
- WBPP stage settings were taken only from user-generated logs and outputs.

Next step:

- Implement resident/streaming FastIntegration parity: calibrated-output
  normalization policy, cosmetic high-pixel correction, alignment failure
  accounting, registration/warp, and winsorized rejection, then rerun the same
  M38 200-light comparison.

Clean-room status:

- Compliant. No official WBPP/PJSR source was read or copied. Only
  user-generated WBPP logs, output paths, XISF metadata, and image statistics
  were used.
