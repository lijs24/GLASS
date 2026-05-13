# Optimization Gate 07 Benchmark: M38 Shared-sort Catalog

## Gate

Optimization Gate 07 benchmark.

## Completed content

- Ran the accepted M38 200-light resident triangle benchmark with:
  - batched moving catalog scheduling;
  - shared-memory parallel sorting inside grid/NMS candidate catalog generation.
- Generated a fresh resident HTML report and WBPP scaled coverage-masked compare report.
- Ran the acceptance audit against the user-generated PixInsight/WBPP black-box result.
- Verified the output master and coverage map are byte-identical to the previous accepted batch-catalog run.

## Commands

```powershell
.\.venv\Scripts\gpwbpp.exe run --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort" --backend cuda --memory-mode resident --resident-prefetch-frames 2 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
```

```powershell
.\.venv\Scripts\gpwbpp.exe report --run "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\report.html"
```

```powershell
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\integration\resident_master_H.fits" --reference "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.html" --gpwbpp-time-seconds 63.91419059992768 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP shared-sort final-stride8 cand48 scaled coverage190" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 8.764434957115609e-06 --gpwbpp-offset 0.0006274500691899127 --gpwbpp-coverage-map "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\integration\resident_coverage_map_H.fits" --min-coverage 190
```

```powershell
.\.venv\Scripts\gpwbpp.exe acceptance-audit --manifest "C:\gpwbpp_runs\final_m38_h_200\manifest.json" --gpwbpp-run "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort" --wbpp-result "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json "C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.json" --out "runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog_sharedsort.json" --markdown "runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog_sharedsort.md" --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
```

## Test result

- Code gate tests:
  - Targeted CUDA star/resident tests: `12 passed`.
  - Full pytest: `181 passed in 8.02s`.
- M38 acceptance audit: passed.

## Timing and quality

| Run | Total s | Read/upload/calibrate s | Registration/warp s | Moving catalog s | Descriptor fit s | Pixel refine s | RMS vs WBPP | p99 vs WBPP | Coverage | Speedup vs WBPP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cand48 previous | 72.988996 | 48.852833 | 21.040626 | 14.949664 | 0.948178 | 3.284546 | 0.001670025 | 0.000437351 | 0.961272 | 14.968571 |
| batch catalog | 72.786956 | 48.756547 | 20.882500 | 14.896177 | 0.918728 | 3.259151 | 0.001670025 | 0.000437351 | 0.961272 | 15.010121 |
| batch catalog + shared sort | 63.914191 | 49.455402 | 11.309667 | 5.372982 | 0.919543 | 3.262213 | 0.001670025 | 0.000437351 | 0.961272 | 17.093872 |

## Key Result

- Moving catalog time dropped from about `14.90 s` to `5.37 s`.
- Registration/warp dropped from about `20.88 s` to `11.31 s`.
- Total run time dropped from `72.79 s` to `63.91 s`.
- Compared with the original optimization baseline `111.948822 s`, this is about `1.75x` faster.
- Compared with PixInsight/WBPP black-box `1092.541 s`, this is about `17.09x` faster.

## Byte Identity Check

The shared-sort run is byte-identical to the previous accepted batch-catalog run for the final outputs:

- `resident_master_H.fits` SHA256:
  - `2D85C820BC6D4914A165F8245AD482BC39FFBA859014F823F8FC372F9F5BA998`
- `resident_coverage_map_H.fits` SHA256:
  - `CB151D52BC0BB8485E2D0D2121994868A34A81DB3AB8D807F70D1FB5DF5AEAF7`

## Artifacts

- Run directory: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort`
- Report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\report.html`
- Compare report: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- Compare JSON: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance audit: `runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog_sharedsort.json`
- Acceptance audit summary: `runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog_sharedsort.md`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusion

The single-thread sort inside grid/NMS catalog extraction was a major resident registration bottleneck. The next largest wall-time target is now again the I/O/read/decode/upload/calibrate path at about `49.46 s`; within registration, the remaining meaningful targets are pixel refinement at about `3.26 s`, matrix warp at about `1.59 s`, and further fused catalog generation at about `5.37 s`.

## Known limitations

- The shared sort is still per-frame and per-catalog call, not a fused multi-frame star detection pipeline.
- Catalog arrays still return to host before triangle descriptor generation.
- I/O and FITS decode remain dominant and need pinned-memory/asynchronous prefetch work next.

## Clean-room compliance

- Compliant. The benchmark used GPWBPP code and user-generated PixInsight/WBPP black-box outputs only.
- No PixInsight/WBPP/PJSR official source was read, copied, summarized, or modified.
- No original image data directory was modified.
