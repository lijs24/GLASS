# Optimization Gate 05 Benchmark: M38 Triangle Candidate Sweep

## Gate

Optimization Gate 05 benchmark.

## Completed content

- Swept resident triangle star candidate limits on the M38 200-light benchmark after adopting `prefetch=2` and `final_stride=8`.
- Tested candidate limits 64, 48, and 32 against the previous 96-candidate result.
- Generated reports and WBPP scaled coverage-masked compare reports.
- Ran acceptance audit for the best observed candidate setting.

## Commands

Common command settings:

```powershell
--resident-prefetch-frames 2
--resident-triangle-pixel-refine-final-stride 8
--resident-warp-interpolation lanczos3
--resident-warp-clamping-threshold 0.30
--resident-star-grid-cols 24
--resident-star-grid-rows 16
--resident-ncc-sample-stride 4
```

Varied parameter:

```powershell
--resident-star-max-candidates 64
--resident-star-max-candidates 48
--resident-star-max-candidates 32
```

Acceptance audit was run for the best observed setting:

```powershell
.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\final_m38_h_200\manifest.json" --glass-run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48" --wbpp-result "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json "C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48\compare_vs_wbpp_fastintegration_scaled_coverage190.json" --out "runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48.json" --markdown "runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48.md" --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
```

## Test result

- Code validation from Gate 04 remains green:
  - Ruff: all checks passed.
  - Resident CUDA run tests: 14 passed.
  - Full pytest: 180 passed in 8.13 s.
- Candidate 64 run: completed, compare generated, acceptance audit passed.
- Candidate 48 run: completed, compare generated, acceptance audit passed.
- Candidate 32 run: completed and compare generated, but it was not selected because total time was slower than candidate 48.

## Timing and quality

| Candidates | Total s | Reg/warp s | Descriptor fit s | Pixel refine s | RMS vs WBPP | p99 vs WBPP | Coverage | Speedup vs WBPP |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 96 | 75.554138 | 23.686982 | 3.467549 | 3.293600 | 0.001720977 | 0.000451728 | 0.961371 | 14.460373 |
| 64 | 73.636263 | 21.640834 | 1.547370 | 3.289059 | 0.001720089 | 0.000451515 | 0.961366 | 14.836997 |
| 48 | 72.988996 | 21.040626 | 0.948178 | 3.284546 | 0.001670025 | 0.000437351 | 0.961272 | 14.968571 |
| 32 | 73.191590 | 20.569754 | 0.498134 | 3.284240 | 0.001690988 | 0.000429264 | 0.960792 | not audited |

## Best observed setting

- `--resident-prefetch-frames 2`
- `--resident-triangle-pixel-refine-final-stride 8`
- `--resident-star-max-candidates 48`
- Total elapsed: 72.988996 s.
- Speedup vs PixInsight/WBPP black-box: 14.968571x.
- Speedup vs original 111.948822 s GLASS resident baseline: 1.5338x.
- Acceptance audit: passed.

## Artifacts

- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_lanczos3_prefetch2_refinefinal8_cand48\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- `runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48.json`
- `runs\benchmarks\m38_acceptance_audit_refinefinal8_cand48.md`

## CUDA availability

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: yes.

## Optimization conclusion

- Reducing candidates primarily reduces triangle descriptor fit time.
- Candidate 48 is the best measured setting for this M38 data: faster than 64 and 32 while improving the coverage-masked WBPP RMS/p99 metrics.
- Moving catalog detection remains around 15 s and is now the dominant registration component.

## Known limitations

- Candidate 48 is empirically validated on this M38 H-alpha benchmark only.
- No automatic candidate-count selection or confidence fallback has been implemented yet.
- Moving catalog detection is still per-frame and not batched.

## Next step

- Implement an automatic fast profile capability flag for this data shape, or add a documented benchmark preset.
- Longer-term: batch resident moving catalog detection across frames.

## Clean-room compliance

- Compliant. No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- The comparison used user-generated WBPP black-box outputs and logs only.
- No original data directory was modified.
