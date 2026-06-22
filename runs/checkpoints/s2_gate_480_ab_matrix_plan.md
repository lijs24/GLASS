# Resident 200-Light A/B Matrix Plan

- Status: ready
- Recommendation: execute_when_gpu_idle
- Root: `C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real`
- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Reference: `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`

## Readiness

- GPU: ready - GPU is below the clean benchmark utilization threshold and has enough free memory
- GPU utilization: 0
- GPU free MiB: 97062
- Disk: ready - free GiB 51.992252349853516

## Variants

### throughput_v1_lanczos3_parity

- Role: baseline
- Runtime preset: `throughput-v1`
- Warp interpolation: `lanczos3`
- Integration dispatch: `stack`
- Run dir: `C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity`

Commands:

- `run`:

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack
```

- `compare_reference`:

```powershell
glass compare --glass C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v1_lanczos3_parity_vs_wbpp.html --glass-label "GLASS throughput_v1_lanczos3_parity" --reference-label "WBPP FastIntegration black-box" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_coverage_map_H.fits --min-coverage 190.0
```

- `acceptance_audit`:

```powershell
glass acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v1_lanczos3_parity_vs_wbpp.json --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\acceptance\throughput_v1_lanczos3_parity_acceptance.json --markdown C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\acceptance\throughput_v1_lanczos3_parity_acceptance.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --benchmark-contract-profile resident_cuda_dq_v1
```

- `speedup_summary`:

```powershell
python benchmarks\summarize_wbpp_speedup.py --glass-run C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v1_lanczos3_parity_vs_wbpp.json --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\speedup\throughput_v1_lanczos3_parity_speedup.json --markdown C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\speedup\throughput_v1_lanczos3_parity_speedup.md --min-speedup 2.0
```

- `report`:

```powershell
glass report --run C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\reports\throughput_v1_lanczos3_parity_report.html
```

### throughput_v2_fused_bilinear

- Role: candidate
- Runtime preset: `throughput-v2-fused`
- Warp interpolation: `bilinear`
- Integration dispatch: `auto`
- Run dir: `C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear`

Commands:

- `run`:

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear --backend cuda --memory-mode resident --resident-runtime-preset throughput-v2-fused --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation bilinear --reference-frame-id LIGHT_H_0136 --resident-output-maps audit
```

- `compare_reference`:

```powershell
glass compare --glass C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v2_fused_bilinear_vs_wbpp.html --glass-label "GLASS throughput_v2_fused_bilinear" --reference-label "WBPP FastIntegration black-box" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear\integration\resident_coverage_map_H.fits --min-coverage 190.0
```

- `acceptance_audit`:

```powershell
glass acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v2_fused_bilinear_vs_wbpp.json --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\acceptance\throughput_v2_fused_bilinear_acceptance.json --markdown C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\acceptance\throughput_v2_fused_bilinear_acceptance.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --benchmark-contract-profile resident_cuda_dq_v1
```

- `speedup_summary`:

```powershell
python benchmarks\summarize_wbpp_speedup.py --glass-run C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v2_fused_bilinear_vs_wbpp.json --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\speedup\throughput_v2_fused_bilinear_speedup.json --markdown C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\speedup\throughput_v2_fused_bilinear_speedup.md --min-speedup 2.0
```

- `report`:

```powershell
glass report --run C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\reports\throughput_v2_fused_bilinear_report.html
```

- `compare_baseline`:

```powershell
glass compare --glass C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v2_fused_bilinear_vs_throughput_v1_lanczos3_parity.html --glass-label "GLASS throughput_v2_fused_bilinear" --reference-label "GLASS throughput_v1_lanczos3_parity" --glass-coverage-map C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v2_fused_bilinear\integration\resident_coverage_map_H.fits --min-coverage 190.0
```
