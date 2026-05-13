# Gate 12 Checkpoint: Resident CUDA Triangle 193-Frame WBPP-Failed-Excluded Parity Run

Gate: 12

Status: green validation checkpoint

Completed content:
- Parsed the user-generated PixInsight/WBPP FastIntegration ProcessingHistory from the WBPP master XISF.
- Identified the 7 frames WBPP FastIntegration did not integrate:
  - `LIGHT_H_0100_c.xisf`
  - `LIGHT_H_0153_c.xisf`
  - `LIGHT_H_0154_c.xisf`
  - `LIGHT_H_0155_c.xisf`
  - `LIGHT_H_0156_c.xisf`
  - `LIGHT_H_0157_c.xisf`
  - `LIGHT_H_0158_c.xisf`
- Re-ran GPWBPP resident CUDA triangle registration/integration with the same 200-light plan, same `LIGHT_H_0136` reference, and these 7 frames excluded from integration.
- Generated a report and scaled comparison report against the WBPP FastIntegration master.

Commands run:
```powershell
.\.venv\Scripts\gpwbpp.exe blackbox-history --master "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\fastintegration_history.json" --max-bytes 67108864

.\.venv\Scripts\gpwbpp.exe run --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158

.\.venv\Scripts\gpwbpp.exe report --run "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\report.html"

.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\compare_vs_wbpp_fastintegration_scaled.html" --gpwbpp-time-seconds 111.8 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident CUDA triangle 193 WBPP-failed-excluded scaled" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 0.000014397802053443647 --gpwbpp-offset 0.00000831571748381842

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_gpu_registration_search.py
```

Test result:
- `43 passed in 0.95s`

CUDA availability:
- CUDA was available.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Reported VRAM: 97886 MiB
- Native backend: true

Real data result:
- Dataset: M38 H subset package with 200 lights, 20 bias, 20 dark, 20 flats in `C:\gpwbpp_runs\final_m38_h_200`.
- WBPP FastIntegration integrated 193 of 200 frames.
- GPWBPP resident CUDA triangle run matched that integration set by excluding the same 7 failed WBPP target frames.
- GPWBPP command wall time: 111.8 s.
- WBPP black-box external elapsed time: 1092.541 s.
- Speedup vs WBPP FastIntegration: 9.772280858676208x.
- Resident registration statuses: 192 ok, 1 reference, 7 excluded, 0 failed.
- Resident integration mode: winsorized sigma approximation.
- Estimated resident peak memory: 47.3117358982563 GiB.

Generated artifacts:
- `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\fastintegration_history.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\integration\resident_master_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\integration\resident_weight_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\integration\resident_coverage_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\integration\resident_low_rejection_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\integration\resident_high_rejection_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\report.html`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\compare_vs_wbpp_fastintegration_scaled.html`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded\compare_vs_wbpp_fastintegration_scaled.json`

Comparison result:
- Shape match: true.
- Applied GPWBPP scale: 1.4397802053443647e-05.
- Applied GPWBPP offset: 8.31571748381842e-06.
- `abs_diff_p50`: 2.213462721556425e-05.
- `abs_diff_p90`: 5.8946432545781136e-05.
- `abs_diff_p99`: 0.0006739846663549494.
- `abs_diff_p999`: 0.20841886494512485.
- `rms_diff`: 0.012336611842884312.
- Large residuals remain concentrated in high-signal/star-core pixels and are consistent with current known differences in interpolation, rejection, output scaling, and exact FastIntegration alignment semantics.

Known limitations:
- GPWBPP currently uses resident bilinear matrix warp; WBPP FastIntegration used Lanczos3 with clamping threshold 0.30 in the black-box log.
- GPWBPP currently uses triangle descriptors; WBPP black-box settings used pentagon descriptors (`useTriangles=false`, `polygonSides=5`).
- Local normalization was disabled for this comparison.
- GPWBPP winsorized integration is still an approximation, not a confirmed PixInsight-identical implementation.
- Output scaling differs between GPWBPP ADU-like FITS and WBPP normalized XISF; comparison uses an explicit diagnostic linear transform.

Next step:
- Implement GPU Lanczos3/clamped warp and WBPP-like polygon descriptor mode, then rerun the 193-frame parity comparison to reduce star-core residuals.

Clean-room compliance:
- Compliant. This checkpoint inspected only user-generated PixInsight/WBPP logs, settings text, output XISF ProcessingHistory, and output images.
- No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or used as implementation input.
