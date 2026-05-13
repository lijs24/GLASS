# Optimization Gate 04 Benchmark: M38 Triangle Pixel-Refine Stride

## Gate

Optimization Gate 04 benchmark.

## Completed content

- Benchmarked resident triangle pixel-refine final sample stride on the real M38 H-alpha 200-light parity dataset.
- Tested final strides 2, 4, and 8 against the stride 1 baseline.
- Generated HTML reports, WBPP scaled coverage-masked compare reports, and acceptance audits.
- Verified all tested stride values keep the benchmark within acceptance thresholds.

## Commands

The common command used the same M38 plan, 200 lights, 20 bias, 20 dark, 20 flat, 7 WBPP-failed frames excluded, `prefetch=2`, Lanczos3 warp, and `min_coverage=190` compare. The varied parameter was:

```powershell
--resident-triangle-pixel-refine-final-stride 2
--resident-triangle-pixel-refine-final-stride 4
--resident-triangle-pixel-refine-final-stride 8
```

Validation commands from the code gate:

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q
```

Acceptance audit commands were run for stride 2, 4, and 8, for example:

```powershell
.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\final_m38_h_200\manifest.json" --glass-run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8" --wbpp-result "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8\compare_vs_wbpp_fastintegration_scaled_coverage190.json" --out "runs\benchmarks\m38_acceptance_audit_refinefinal8.json" --markdown "runs\benchmarks\m38_acceptance_audit_refinefinal8.md" --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
```

## Test result

- Ruff: all checks passed.
- Resident CUDA run tests: 14 passed.
- Full pytest: 180 passed in 8.13 s.
- Real-data stride 2 acceptance audit: passed.
- Real-data stride 4 acceptance audit: passed.
- Real-data stride 8 acceptance audit: passed.

## Timing and quality

| Final stride | Total s | Reg/warp s | Pixel refine s | Moving catalog s | RMS vs WBPP | p99 vs WBPP | Coverage | Speedup vs WBPP |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 baseline | 111.385636 | 58.390720 | 37.927054 | 15.045235 | 0.001718* | 0.0004528* | 0.9613* | 9.8x* |
| 2 | 84.337768 | 32.219947 | 11.831580 | 14.998229 | 0.001712499 | 0.000452591 | 0.961262 | 12.954350 |
| 4 | 77.452243 | 25.331855 | 4.971519 | 14.985108 | 0.001717434 | 0.000451880 | 0.961226 | 14.105996 |
| 8 | 75.554138 | 23.686982 | 3.293600 | 15.010985 | 0.001720977 | 0.000451728 | 0.961371 | 14.460373 |

`*` Baseline quality values refer to the previous accepted stride-1 coverage190 comparison from the M38 parity benchmark.

## Acceptance evidence

- `runs\benchmarks\m38_acceptance_audit_refinefinal2.json`: passed.
- `runs\benchmarks\m38_acceptance_audit_refinefinal4.json`: passed.
- `runs\benchmarks\m38_acceptance_audit_refinefinal8.json`: passed.

## Artifacts

- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal2`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal4`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8\compare_vs_wbpp_fastintegration_scaled_coverage190.json`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusion

- Final stride 8 is the fastest accepted result in this benchmark: 75.554 s total and 14.46x faster than WBPP.
- Final stride 4 is the more conservative quality/speed compromise: 77.452 s total with RMS closer to the stride-1 accepted baseline.
- Pixel refine is no longer the dominant registration bucket at stride 8; moving catalog generation is now the largest registration component at about 15 s.
- The next high-impact optimization is batching/caching moving star catalog generation across frames.

## Known limitations

- Stride 8 is accepted by the current RMS/p99/coverage thresholds but is not proven universally safe for all datasets.
- The current command leaves the choice to the operator through CLI; no automatic confidence gate has been implemented yet.
- Native batched pixel refinement is still not implemented.

## Next step

- Implement a confidence-gated refine policy: run fast final stride 8 first, then selectively re-run final stride 1/2 only for frames with low pixel NCC, high RMS, or poor triangle inliers.
- Then optimize the new largest bucket: resident moving catalog generation.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The comparison used user-generated WBPP black-box outputs and logs only.
- No original data directory was modified.
