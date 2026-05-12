# Gate 13 Status: WBPP Accepted-Frame Mask

Gate: 13 partial black-box comparison.

Completed content:
- Inspected the user-generated WBPP output XISF ProcessingHistory for the M38
  final master.
- Found the seven FastIntegration targets with `totalPairMatches=0` and zero
  transform matrices:
  - `LIGHT_H_0100`
  - `LIGHT_H_0153`
  - `LIGHT_H_0154`
  - `LIGHT_H_0155`
  - `LIGHT_H_0156`
  - `LIGHT_H_0157`
  - `LIGHT_H_0158`
- Added `gpwbpp run --exclude-frame-id ...` for resident CUDA runs. The option
  can be repeated and matches frame id, file name, or file stem.
- Ran a new resident CUDA comparison excluding the same seven frames.

Commands run:
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_resident_cuda_run.py tests\\test_cuda_resident_stack.py tests\\test_cpu_integration.py`
- `.\\.venv\\Scripts\\python.exe -m gpwbpp.cli run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_wsc_reject_flatfloor005_wbpp_mask_run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_preview --reference-frame-id F000196 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\\.venv\\Scripts\\python.exe -m gpwbpp.cli compare --gpwbpp C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_wsc_reject_flatfloor005_wbpp_mask_run\\integration\\resident_master_H.fits --reference C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\\gpwbpp_runs\\final_m38_h_200\\wsc_reject_flatfloor005_wbpp_mask_scaled_resident_vs_wbpp_compare.html --gpwbpp-time-seconds 76.81677979999222 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident CUDA WSC-reject WBPP accepted-frame mask" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 0.000015259021896696421 --clip-low 0 --clip-high 1`
- `.\\.venv\\Scripts\\python.exe -m gpwbpp.cli report --run C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_wsc_reject_flatfloor005_wbpp_mask_run --out C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_wsc_reject_flatfloor005_wbpp_mask_run\\report.html`

Test results:
- Targeted tests: 14 passed in 0.24 s.

Real-data run results:
- Dataset: M38 H, 200 lights plus 20 bias, 20 dark, 20 flats.
- Excluded frames: 7.
- Registration statuses: 192 ok, 1 reference, 7 excluded.
- GPWBPP resident elapsed time: 76.81677979999222 s.
- WBPP black-box elapsed time: 1092.541 s.
- Raw speedup vs WBPP: 14.222686798960435x.

Comparison results:
- Shape match: yes.
- Scale applied to GPWBPP before comparison: `1 / 65535`.
- RMS diff: 0.013264537484375921.
- Relative RMS diff: 0.9911388338875652.
- Median absolute diff: 0.00013177900109440088.
- P90 absolute diff: 0.000338164740242064.
- P99 absolute diff: 0.005538512286729958.
- P99.9 absolute diff: 0.21055566686391947.
- Max absolute diff: 0.9980595544911921.

Conclusion:
- The accepted-frame mask explains WBPP's 193/200 count, but applying the same
  mask does not materially improve GPWBPP/WBPP final-master parity. The current
  dominant differences are likely calibration/output scaling, transform and
  interpolation details, and exact rejection semantics.

CUDA availability:
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

Clean-room compliance:
- Compliant. Only user-generated WBPP logs and output XISF metadata/history were
  inspected. No official WBPP/PJSR source was read or copied.
