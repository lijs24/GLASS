# Optimization Gate 06 Benchmark: M38 Resident Catalog Batch

## Gate

Optimization Gate 06 benchmark.

## Completed content

- Ran the accepted M38 200-light resident triangle benchmark with the new batched grid/NMS moving-catalog path.
- Generated a fresh resident HTML report and WBPP scaled coverage-masked compare report.
- Ran the acceptance audit against the user-generated PixInsight/WBPP black-box result.
- Verified the new batch-catalog output master and coverage map are byte-identical to the previous accepted candidate-48 run.

## Commands

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog" --backend cuda --memory-mode resident --resident-prefetch-frames 2 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id LIGHT_H_0136 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
```

```powershell
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\report.html"
```

```powershell
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\compare_vs_wbpp_fastintegration_scaled_coverage190.html" --glass-time-seconds 72.78695579990745 --reference-time-seconds 1092.541 --glass-label "GLASS final-stride8 cand48 batch catalog scaled coverage190" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\integration\resident_coverage_map_H.fits" --min-coverage 190
```

```powershell
.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\final_m38_h_200\manifest.json" --glass-run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog" --wbpp-result "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\compare_vs_wbpp_fastintegration_scaled_coverage190.json" --out "runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog.json" --markdown "runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog.md" --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
```

```powershell
Get-FileHash "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48\integration\resident_master_H.fits", "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\integration\resident_master_H.fits", "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48\integration\resident_coverage_map_H.fits", "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\integration\resident_coverage_map_H.fits"
```

## Test result

- Code gate tests from this increment:
  - Ruff: passed.
  - Targeted CUDA/resident tests: `2 passed`.
  - Full pytest: `181 passed in 8.00s`.
- M38 acceptance audit: passed.

## Timing and quality

| Run | Total s | Read/upload/calibrate s | Registration/warp s | Moving catalog s | Descriptor fit s | Pixel refine s | RMS vs WBPP | p99 vs WBPP | Coverage | Speedup vs WBPP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cand48 previous | 72.988996 | 48.852833 | 21.040626 | 14.949664 | 0.948178 | 3.284546 | 0.001670025 | 0.000437351 | 0.961272 | 14.968571 |
| cand48 batch catalog | 72.786956 | 48.756547 | 20.882500 | 14.896177 | 0.918728 | 3.259151 | 0.001670025 | 0.000437351 | 0.961272 | 15.010121 |

Additional timing field:

- `triangle_moving_catalog_batch`: 14.895883 s.

## Byte Identity Check

- `resident_master_H.fits` SHA256 for previous cand48 and batch-catalog run:
  - `2D85C820BC6D4914A165F8245AD482BC39FFBA859014F823F8FC372F9F5BA998`
- `resident_coverage_map_H.fits` SHA256 for previous cand48 and batch-catalog run:
  - `CB151D52BC0BB8485E2D0D2121994868A34A81DB3AB8D807F70D1FB5DF5AEAF7`

## Artifacts

- Run directory: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog`
- Report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\report.html`
- Compare report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- Compare JSON: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48_batchcatalog\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance audit: `runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog.json`
- Acceptance audit summary: `runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48_batchcatalog.md`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusion

The batch wrapper is correct and slightly faster, but it only improved the full M38 run by about 0.20 s. The catalog phase remains about 14.9 s, so repeated Python calls and scratch allocation are not the dominant cost. The next meaningful optimization must move inside the catalog kernels: fused multi-frame star catalog generation, fewer full-frame scans, persistent/batched descriptor buffers, or a fully device-resident catalog-to-descriptor path that avoids per-frame D2H catalog copies.

## Known limitations

- This is a scheduling/buffer-reuse batch, not a fused multi-frame CUDA kernel.
- Catalog arrays still return to host before descriptor generation.
- I/O/read/decode remains the largest overall wall-time component.

## Clean-room compliance

- Compliant. The benchmark used GLASS code and user-generated PixInsight/WBPP black-box outputs only.
- No PixInsight/WBPP/PJSR official source was read, copied, summarized, or modified.
- No original image data directory was modified.
