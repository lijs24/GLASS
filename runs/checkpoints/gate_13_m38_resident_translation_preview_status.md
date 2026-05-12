# Gate 13 Status: M38 Resident Translation Preview Comparison

Gate: 13 partial black-box comparison.

Completed content:
- Ran a real 200-light M38 H dataset through the resident CUDA path with:
  - 200 light frames.
  - 20 bias frames.
  - 20 dark frames.
  - 20 flat frames.
  - `--flat-floor 0.05`.
  - `--integration-rejection winsorized_sigma`.
  - `--resident-registration translation_preview`.
  - `--reference-frame-id F000196` (`LIGHT_H_0136`, observed from user-generated
    WBPP logs).
- Generated a fresh resident run report and PixInsight/WBPP compare report.

Commands run:
- `.\\.venv\\Scripts\\python.exe -m gpwbpp.cli run --plan C:\\gpwbpp_runs\\final_m38_h_200\\processing_plan.json --out C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_preview --reference-frame-id F000196`
- `.\\.venv\\Scripts\\python.exe -m gpwbpp.cli compare --gpwbpp C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\integration\\resident_master_H.fits --reference C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\\gpwbpp_runs\\final_m38_h_200\\winsorized_flatfloor005_align_preview_scaled_resident_vs_wbpp_compare.html --gpwbpp-time-seconds 81.22572250000667 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident CUDA winsorized flat-floor 0.05 translation-preview" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 0.000015259021896696421 --clip-low 0 --clip-high 1`
- `.\\.venv\\Scripts\\python.exe -m gpwbpp.cli report --run C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run --out C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\report.html`

Run results:
- GPWBPP resident elapsed time: 81.22572250000667 s.
- WBPP black-box elapsed time: 1092.541 s.
- Raw speedup vs WBPP: 13.450677523981522x.
- Resident integration kernel time: 0.25992599996970966 s.
- Light read/upload/calibrate plus registration loop: 55.712976299982984 s.
- Master build/load: 18.859306900005322 s.
- Output write: 3.0766756999655627 s.
- Resident memory estimate peak: 47.3117358982563 GiB.

Registration diagnostics:
- Reference frame: `F000196` / `LIGHT_H_0136.fits`.
- Preview scale: 10.
- Status counts: 199 ok, 1 reference, 0 failed.
- Estimated integer shifts: all 200 frames `(0, 0)`.
- This means the dataset is already coarsely aligned at the preview resolution,
  or the preview estimator is not sensitive enough for sub-preview-pixel drift.

Comparison results:
- Shape match: yes.
- Scale applied to GPWBPP before comparison: `1 / 65535`.
- RMS diff: 0.013271217746005768.
- Relative RMS diff: 0.9916379893786382.
- Median absolute diff: 0.00011742929928004742.
- P99 absolute diff: 0.0074825316539498575.
- P99.9 absolute diff: 0.21053871907113791.
- Max absolute diff: 0.9897591453045607.

Artifacts:
- `C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\integration\\resident_master_H.fits`
- `C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\integration\\resident_weight_map_H.fits`
- `C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\integration\\resident_coverage_map_H.fits`
- `C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\integration\\resident_low_rejection_map_H.fits`
- `C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\integration\\resident_high_rejection_map_H.fits`
- `C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\registration_results.json`
- `C:\\gpwbpp_runs\\final_m38_h_200\\gpwbpp_resident_winsorized_flatfloor005_align_preview_run\\report.html`
- `C:\\gpwbpp_runs\\final_m38_h_200\\winsorized_flatfloor005_align_preview_scaled_resident_vs_wbpp_compare.json`
- `C:\\gpwbpp_runs\\final_m38_h_200\\winsorized_flatfloor005_align_preview_scaled_resident_vs_wbpp_compare.html`

CUDA availability:
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

Known limitations:
- This comparison still proves speed but not final master parity.
- Resident `winsorized_sigma` is still a mean/std approximation.
- WBPP integrated 193/200 frames; the resident run accepted all 200 because the
  preview registration found no failures.
- Resident warp is integer translation only and did not change this dataset.
- Missing parity items remain: exact robust rejection, WBPP-like frame rejection,
  cosmetic correction, Local Normalization, interpolation/crop/coverage policy,
  and final output scaling semantics.

Next step:
- Implement a real resident star-detection/quality pass and use it to match
  WBPP's rejected-frame behavior before improving robust Winsorized Sigma
  Clipping.

Clean-room compliance:
- Compliant. The WBPP reference is a black-box output/log produced by the user.
  No official WBPP/PJSR source was read or copied.
