# Optimization Gate 08 Benchmark: M38 Prefetch Worker Sweep

## Gate

Optimization Gate 08 benchmark.

## Completed content

- Swept resident CPU RAM prefetch depth and worker count on the accepted M38 200-light benchmark after the shared-sort registration optimization.
- Generated a fresh resident HTML report and WBPP scaled coverage-masked compare report for the best setting.
- Ran the acceptance audit against the user-generated PixInsight/WBPP black-box result.
- Verified the best prefetch-worker output master and coverage map are byte-identical to previous accepted runs.

## Commands

Common settings:

```powershell
--backend cuda
--memory-mode resident
--until-stage integration
--local-normalization off
--integration-rejection winsorized_sigma
--integration-weighting none
--flat-floor 0.05
--resident-registration similarity_cuda_triangle
--resident-star-threshold 350
--resident-star-max-candidates 48
--resident-star-tolerance-px 3
--resident-star-grid-cols 24
--resident-star-grid-rows 16
--resident-ncc-sample-stride 4
--resident-triangle-pixel-refine-final-stride 8
--resident-warp-interpolation lanczos3
--resident-warp-clamping-threshold 0.30
```

Swept settings:

```powershell
--resident-prefetch-frames 4 --resident-prefetch-workers 2
--resident-prefetch-frames 8 --resident-prefetch-workers 4
--resident-prefetch-frames 16 --resident-prefetch-workers 8
--resident-prefetch-frames 32 --resident-prefetch-workers 16
```

Best-run report:

```powershell
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\report.html"
```

Best-run compare:

```powershell
.\.venv\Scripts\glass.exe compare --glass "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\integration\resident_master_H.fits" --reference "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.html" --glass-time-seconds 39.175000299932435 --reference-time-seconds 1092.541 --glass-label "GLASS shared-sort prefetch16-workers8 scaled coverage190" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\integration\resident_coverage_map_H.fits" --min-coverage 190
```

Acceptance audit:

```powershell
.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\final_m38_h_200\manifest.json" --glass-run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort" --wbpp-result "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.json" --out "runs\benchmarks\m38_acceptance_audit_prefetch16_workers8_sharedsort.json" --markdown "runs\benchmarks\m38_acceptance_audit_prefetch16_workers8_sharedsort.md" --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
```

## Test result

- Code gate tests:
  - Ruff: passed.
  - Targeted CLI/resident tests: `5 passed`.
  - Full pytest: `181 passed in 7.93s`.
- M38 acceptance audit for best run: passed.

## Timing and quality

| Prefetch | Workers | Total s | Read/upload/calibrate s | Read wait s | Worker decode sum s | H2D/calibrate s | Registration/warp s | Speedup vs WBPP |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 1 | 63.914191 | 49.455402 | 34.502889 | 39.963254 | 3.881125 | 11.309667 | 17.093872 |
| 4 | 2 | 50.658224 | 35.469229 | 20.110092 | 51.983574 | 4.060655 | 11.295974 | not audited |
| 8 | 4 | 41.349994 | 26.867695 | 9.937690 | 68.757624 | 4.853106 | 11.322156 | not audited |
| 16 | 8 | 39.175000 | 24.712707 | 5.870130 | 118.331854 | 5.741592 | 11.312836 | 27.888730 |
| 32 | 16 | 39.931750 | 25.465598 | 1.089001 | 233.243166 | 8.561642 | 11.299603 | not audited |

## Key Result

- Best setting: `--resident-prefetch-frames 16 --resident-prefetch-workers 8`.
- Total time improved from the shared-sort baseline `63.914191 s` to `39.175000 s`.
- Read wait dropped from about `34.50 s` to `5.87 s`.
- Worker decode sum increased because more reads happen concurrently; that is expected and reflects overlap rather than wall time.
- `32/16` over-prefetched: read wait nearly vanished, but H2D/calibration and memory contention increased, making it slower than `16/8`.
- Compared with the original optimization baseline `111.948822 s`, the best run is about `2.86x` faster.
- Compared with PixInsight/WBPP black-box `1092.541 s`, the best run is about `27.89x` faster.

## Quality

- Acceptance audit: passed.
- Shape match: true.
- Coverage fraction: `0.9612716865202948`.
- RMS diff vs WBPP coverage190: `0.0016700247556533851`.
- abs diff p99 vs WBPP coverage190: `0.0004373512882739298`.
- Final master SHA256 remains `2D85C820BC6D4914A165F8245AD482BC39FFBA859014F823F8FC372F9F5BA998`.

## Artifacts

- Best run directory: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort`
- Report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\report.html`
- Compare report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- Compare JSON: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch16_workers8_sharedsort\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance audit: `runs\benchmarks\m38_acceptance_audit_prefetch16_workers8_sharedsort.json`
- Acceptance audit summary: `runs\benchmarks\m38_acceptance_audit_prefetch16_workers8_sharedsort.md`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusion

Configurable multi-worker CPU RAM prefetch is a major win on this C-drive staged M38 dataset. The remaining resident run budget is now dominated by:

- master build/load, about `11.06 s`;
- light read/upload/calibrate loop, about `24.71 s`, with `5.87 s` read wait and `5.74 s` H2D/calibrate;
- resident registration/warp, about `11.31 s`.

The next I/O optimization should avoid excessive CPU memory contention while reducing the remaining `5.87 s` read wait and `5.74 s` H2D/calibrate time, likely via a bounded preset/autotune and then pinned/asynchronous H2D.

## Known limitations

- Pinned host buffers and asynchronous H2D streams are not implemented yet.
- The optimal worker/depth setting is hardware and storage dependent.
- This sweep was run on the staged C-drive M38 benchmark, not directly on external USB storage.

## Clean-room compliance

- Compliant. The benchmark used GLASS code and user-generated PixInsight/WBPP black-box outputs only.
- No PixInsight/WBPP/PJSR official source was read, copied, summarized, or modified.
- No original image data directory was modified.
