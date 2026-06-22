# S2-Gate 472 Status: Real 200-Light WBPP/GLASS A/B Return

- Gate: S2-Gate 472
- Status: passed
- Scope: return from report/default-promotion gates to a real 200-light A/B
  validation of GLASS resident CUDA against a user-generated PixInsight/WBPP
  black-box baseline.
- Dataset: `C:\gpwbpp_runs\final_m38_h_200`
  - Lights: `200`
  - Bias: `20`
  - Dark: `20`
  - Flat: `20`
  - Target/filter: M38 H-alpha mono
- GLASS run: `C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410`
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`

## Commands

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410 --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit

glass compare --glass C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 59.33264669997152 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA 200-light parity contended" --reference-label "PixInsight WBPP FastIntegration black-box" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\compare_diagnostics_scaled_coverage190 --diagnostic-max-size 1600

glass acceptance-audit --manifest C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\manifest.json --glass-run C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\acceptance_audit.json --markdown C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\acceptance_audit.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01

python benchmarks\summarize_wbpp_speedup.py --glass-run C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\wbpp_speedup_summary.json --markdown C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\wbpp_speedup_summary.md --min-speedup 2.0

glass report --run C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410 --out C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\report.html

python -m pytest -q
```

## Results

- GLASS status: completed
- WBPP black-box elapsed: `1092.541 s`
- GLASS elapsed: `59.33264669997152 s`
- Speedup versus WBPP: `18.413825453037212x`
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability
  `12.0`, total memory `97886 MiB`
- Memory admission: passed
  - Estimated peak VRAM: `49.60843022540212 GiB`
  - Selected warp batch dispatch: `chunked`
  - Recommended action: `resident_full_frame`
- Frame accounting:
  - Input lights: `200`
  - Resident calibrated lights: `200`
  - Integrated frames: `193`
  - Zero-weight frames: `7`
  - Exception frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`,
    `F000217`, `F000218`
- Coverage-masked comparison against WBPP:
  - Shape match: `true`
  - Coverage threshold: `190`
  - Compared pixels: `59217988`
  - Coverage fraction: `0.960532609259836`
  - RMS difference: `0.0017794216505176163`
  - Absolute difference p50: `7.299671415239573e-05`
  - Absolute difference p90: `0.0001341039314866066`
  - Absolute difference p99: `0.00042621337808668863`
  - Absolute difference p99.9: `0.003845416396856427`
- Acceptance audit: passed
  - Minimum light/bias/dark/flat counts: passed
  - Minimum active frames: passed
  - Minimum speedup: passed
  - Shape match: passed
  - Minimum coverage fraction: passed
  - Maximum RMS diff: passed
  - Maximum abs diff p99: passed
- DQ/pixel closure: passed
- Report generated: `report.html`
- Test result: `1105 passed in 47.81s`

## Performance Notes

- This run was intentionally marked contended. At launch another GPU compute
  process was active; use the timing as qualified evidence, not final clean
  performance evidence.
- The acceptance audit still reports an `18.413825453037212x` speedup over the
  WBPP black-box baseline.
- Current optimization targets from the audit:
  - light read/upload/calibration: `37.70490640000207 s`
  - master build/load: `17.644714499998372 s`
  - resident registration/warp: `3.170013300376013 s`
  - output-map write policy: `2.368561299983412 s`

## Known Limitations

- The run used `throughput-v1` Lanczos3 parity, not the new
  `throughput-v2-fused` bilinear candidate.
- Because the GPU was shared with another long-running task, the next clean
  performance gate must rerun the same 200-light command when the GPU is idle.
- No runtime defaults or pixel algorithms were changed in this gate.

## Next Step

- Run a clean idle-GPU 200-light A/B matrix:
  - `throughput-v1` Lanczos3 parity for WBPP-like comparison;
  - `throughput-v2-fused` bilinear candidate for resident fused-dispatch speed;
  - require acceptance, DQ closure, frame accounting, and compare metrics before
    any default promotion.

## Clean-Room Compliance

- Compliant.
- This gate used GLASS-generated artifacts, user-staged input images, and
  user-generated PixInsight/WBPP black-box timing/output files only.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Input image directories were treated as read-only.
