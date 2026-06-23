# S2-Gate 558: Current Full 200-Light A/B Acceptance Refresh

## Scope

This gate stops the micro-optimization thread and returns to the Phase 2
mainline: a real 200-light, 20-bias, 20-dark, 20-flat resident CUDA run against
the existing WBPP black-box reference.

The run is intentionally self-contained for master calibration frames. It does
not pass the shared `--resident-master-cache-dir` used by recent hot-cache
performance probes. The resident master cache records `cache_hit_count=0` and
`cache_miss_count=1`.

## Completed

- Ran the current default resident CUDA path on the full M38 H-alpha 200-light
  benchmark.
- Generated a coverage-masked compare against the WBPP FastIntegration master.
- Ran `glass acceptance-audit` with the resident CUDA DQ benchmark profile.
- Wrote a speedup summary for the current full run.
- Confirmed DQ pixel closure remains passed.
- Explicitly did not promote the ready-min selector, refill-mode matrix, or
  single-notify micro-optimization probes because the real 200-light evidence
  did not justify them.

## Commands

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --out C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default

.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 13.716492 --reference-time-seconds 1092.541 --glass-label "GLASS Gate558 current full default" --reference-label "WBPP black-box fastIntegration" --glass-scale=1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\integration\resident_coverage_map_H.fits --min-coverage 190

.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\manifest.json --glass-run C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\acceptance_audit.md --min-active-frames 190 --min-speedup 2.0 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --benchmark-contract-profile resident_cuda_dq_v1

.\.venv\Scripts\python.exe -m glass.cli speedup-summary --glass-run C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_wbpp_speedup_summary_gate558_current_full.json --markdown runs\benchmarks\m38_wbpp_speedup_summary_gate558_current_full.md --min-speedup 2.0

.\.venv\Scripts\python.exe -m pytest -q tests/test_speedup_report.py tests/test_benchmark_contract_profile.py tests/test_phase2_status.py

.\.venv\Scripts\python.exe -m pytest -q
```

## Results

- GLASS run: `C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default`
- Run timing total: `13.36161980003817 s`
- Shell timing: `13.716492 s`
- WBPP black-box elapsed: `1092.541 s`
- Speedup by `run_timing.json`: `81.76710730811836x`
- Speedup by shell timing embedded in compare: `79.65163396005333x`
- Active weighted frames: `193`
- Zero-weight frames: `7`
- DQ closure: passed
- Acceptance audit: passed
- Focused report/status tests: `116 passed in 1.48 s`
- Full pytest: `1189 passed in 44.12 s`

## Image Comparison

- Shape match: true
- Coverage mask: min coverage `190`, ignored border `128 px`
- Coverage fraction: `0.9892770479074376`
- Compared pixels: `56997300`
- RMS diff: `0.0004279821839256963`
- Absolute diff p99: `0.0001313822576776147`

## Stage Timing

These values are resident timing buckets and can overlap; they are not intended
to sum to wall-clock time.

- Master build/load: `8.650153900031 s`
- Light read/upload/calibrate: `10.856784100004006 s`
- Light read wait: `0.7544263000017963 s`
- Registration/warp: `0.25406019965885207 s`
- Integration: `0.32319869997445494 s`
- Output write: `0.3425363000133075 s`

## CUDA

- CUDA backend: available
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Resident estimated peak VRAM: `49.608429938554764 GiB`
- FITS read mode: `native_u16_gpu`
- Runtime preset behavior: prefetch `32`, workers `16`, calibration batch `16`,
  wave `4`, remaining-index model `set_with_sequential_cursor`

## Artifacts

- Summary JSON: `runs/checkpoints/s2_gate_558_current_full_ab_summary.json`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Compare HTML:
  `C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- Acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\acceptance_audit.json`
- Acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate558_real_200_full_ab\runs_20260623_173204\current_full_default\acceptance_audit.md`
- Speedup summary JSON:
  `runs\benchmarks\m38_wbpp_speedup_summary_gate558_current_full.json`
- Speedup summary Markdown:
  `runs\benchmarks\m38_wbpp_speedup_summary_gate558_current_full.md`

## Known Limitations

- Local normalization remains off for this fastest parity run.
- This gate validates the current full resident default against the stored
  WBPP black-box reference; it does not rerun WBPP.
- Timing is excellent but still partly dependent on the current high-VRAM
  resident mode and local disk/cache state.

## Next Step

Return to engineering completeness: make the default route documentation and
contract bundle point at this current full A/B evidence, then continue with DQ
mask propagation and StackEngine default-path hardening only when it changes
runtime behavior or formal contracts.

## Source Boundary

This gate uses GLASS artifacts and user-generated WBPP black-box timing/output
files only. It does not read or modify PixInsight installation source files.
