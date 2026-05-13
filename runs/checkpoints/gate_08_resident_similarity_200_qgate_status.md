# Gate 08 Resident Similarity 200-Light QGate Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Ran a 200-light real M38 validation using production resident CUDA `similarity_cuda_catalog`.
- Included both normal-orientation and 180-degree flipped light frames by allowing similarity rotation up to about pi.
- Enabled registration quality gates:
  - `cuda_catalog_min_pixel_ncc=0.75`
  - `cuda_catalog_min_selected_seed_inliers=8`
- Verified low-quality registrations are marked failed and assigned zero integration weight.
- Generated GLASS report and comparison reports against:
  - existing GLASS resident external-astroalign 200-light output
  - PixInsight/WBPP black-box FastIntegration output

## Commands run
- `.venv\Scripts\python -m pytest -q`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 350 --resident-star-max-candidates 128 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 96 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior none --resident-star-prior-radius-px 8 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-core-preselect-top-k 8 --reference-frame-id F000061`
- `.venv\Scripts\glass.exe report --run C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\report.html`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_astroalign_200_flat005_preview3072_matchedmasters\integration\resident_master_H.fits --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\compare_vs_astroalign_resident.html --glass-label glass_resident_similarity_qgate --reference-label glass_resident_external_astroalign`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\integration\resident_master_H.fits --reference C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\compare_vs_pixinsight_wbpp.html --glass-label glass_resident_similarity_qgate --reference-label pixinsight_wbpp_fastintegration --glass-time-seconds 4570.85339210002 --reference-time-seconds 1092.541`

## Test results
- Full test suite before the 200-light qgate run: `150 passed in 8.84s`.

## Real-data validation
- Input plan: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\processing_plan.json`
- Output run: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate`
- Report: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\report.html`
- GLASS vs astroalign-resident compare: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\compare_vs_astroalign_resident.html`
- GLASS vs PixInsight/WBPP compare: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_200_starcore8_fixed350_rotpi_qgate\compare_vs_pixinsight_wbpp.html`
- Dataset: 200 H-filter M38 lights, 20 bias, 20 dark, 20 flat, full shape `6422x9600`.
- Reference frame: `F000061`.
- Registration mode: resident CUDA `similarity_cuda_catalog`.
- Star threshold: fixed `350`.
- Max abs rotation: `3.2 rad`.
- Star prior: `none`, required for 180-degree flipped frames.
- Registration result:
  - row count: `200`
  - ok/reference frames: `192`
  - failed frames: `8`
  - failed frame ids: `F000160`, `F000194`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`
  - all failed frames were failed by the registration quality gate
  - failed frame weights: all `0.0`
  - ok inliers min/max: `48/89`
  - ok max fit RMS: `1.792734980583191 px`
  - ok mean fit RMS: `1.2459879807776806 px`
  - ok min pixel NCC: `0.795573`
  - ok mean pixel NCC: `0.9086153141361256`
  - ok frames with pixel NCC below `0.75`: `0`
  - ok 180-degree flip frame count: `102`
- Timing:
  - GLASS qgate elapsed: `4570.85339210002 s`
  - PixInsight/WBPP black-box elapsed: `1092.541 s`
  - WBPP reported time: `18:03.17`
  - current GLASS speedup vs WBPP: `0.239x`; this is slower than WBPP, not an acceleration result.
- Memory estimate:
  - calibrated stack: `45.93372344970703 GiB`
  - resident base: `46.85239791870117 GiB`
  - estimated peak: `47.3117358982563 GiB`

## Comparison notes
- GLASS vs existing astroalign-resident output:
  - robust fit-pixel RMS difference: `5.422116586843049 ADU`
  - robust fit-pixel relative RMS: `0.05358570152931445`
- GLASS vs PixInsight/WBPP:
  - direct scale differs substantially because WBPP XISF output is normalized differently from GLASS FITS ADU output.
  - robust linear fit-pixel RMS difference: `0.001934817355535557` in WBPP output scale.
  - this is not yet proof of scientific equivalence because LN/rejection/output normalization policies still differ.

## CUDA availability
- CUDA available: yes.
- Native backend loaded: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

## Known limitations
- This 200-light result is robust enough to diagnose, but it does not satisfy the final speed goal.
- Registration dominates runtime: per-frame registration mean was `22.58980002599623 s`.
- The current all-frame no-prior rot-pi strategy is too slow for a speed win; the next optimization should split/seed orientation groups or add a GPU resident orientation classifier/prior so normal frames can use the fast NCC-prior path and only flipped frames use rot-pi no-prior search.
- Integration used `rejection none` and `local-normalization off`; full WBPP-like parity still requires LN and rejection to be enabled and validated.
- Detailed diagnostics still need structured JSON instead of warning strings.

## Next step
- Implement orientation-aware registration dispatch:
  - normal-orientation frames use fixed threshold + NCC prior + `max_shift=96`
  - 180-degree flipped frames use rot-pi search
  - low-NCC/low-inlier frames remain excluded
- Re-run the 200-light benchmark and compare again against PixInsight/WBPP timing and master output.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- WBPP was used only as a black-box reference via user-generated logs/artifacts.
