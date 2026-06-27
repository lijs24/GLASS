# S2-Gate 711 Status: Real 200-Light StackEngine A/B Baseline

## Gate

- Gate: S2-Gate 711
- Name: Real 200-Light StackEngine A/B Baseline
- Date: 2026-06-27
- Status: green

## Completed

- Returned to the Phase 2 mainline requested by the user.
- Ran the real 200-light dataset through the default CUDA resident StackEngine path.
- Produced a GLASS master, diagnostic maps, result comparison, speedup summary, acceptance audit, mainline audit, and runtime comparison.
- Extended `glass speedup-summary` with optional `--wbpp-history` so user-generated FastIntegration ProcessingHistory timing is included in the same staged timing report as GLASS resident component timings.
- Verified the real run's DQ/mask pipeline artifacts:
  - `pipeline_contract.json`: passed;
  - `stack_engine_contract.json`: passed;
  - `warp_quality_contract.json`: passed;
  - `resident_result_contract.json`: passed;
  - coverage, DQ, low-rejection, high-rejection, weight, and master FITS outputs exist.

## Real Data Run

- Run:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default`
- Dataset:
  - light: 200;
  - bias: 20;
  - dark: 20;
  - flat: 20.
- Active weighted frames: 193.
- Zero-weight frames: 7.
- Output master:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default\integration\resident_master_H.fits`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\glass_vs_wbpp_full_compare.html --glass-time-seconds 35.32760219998454 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA StackEngine Gate711" --reference-label "WBPP black-box FastIntegration" --glass-coverage-map C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default\integration\resident_coverage_map_H.fits --min-coverage 1 --diagnostics-dir C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\compare_diagnostics --diagnostic-max-size 1600 --hotspot-tile-size 512
.\.venv\Scripts\python.exe -m glass.cli speedup-summary --glass-run C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --wbpp-history C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\fastintegration_history.json --compare-json C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\glass_vs_wbpp_full_compare.json --out C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_speedup_summary.json --markdown C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_speedup_summary.md --min-speedup 1.0
.\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\glass_vs_wbpp_full_compare.json --out C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 1.0 --min-coverage-fraction 1.0 --max-rms-diff 500 --max-abs-diff-p99 200
.\.venv\Scripts\python.exe -m glass.cli phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default --compare-json C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\glass_vs_wbpp_full_compare.json --acceptance-audit C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_acceptance_audit.json --out C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_mainline_audit.md --min-lights 200 --min-active-frames 190 --min-speedup 1.0 --min-coverage-fraction 1.0 --max-rms-diff 500 --max-abs-diff-p99 200 --require-compare --require-acceptance --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli resident-runtime-compare --run gate707=C:\glass_runs\phase2_s2_gate707_h2d_timing_policy\runs_20260626_130000\default_h2d_timing_enabled --run gate711=C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\real_200_stackengine_default --baseline-label gate707 --out C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_runtime_compare_vs_gate707.json --markdown C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_runtime_compare_vs_gate707.md
.\.venv\Scripts\python.exe -m pytest -q tests/test_speedup_report.py tests/test_cli_smoke.py -q
.\.venv\Scripts\python.exe -m ruff check src/glass/report/speedup_report.py src/glass/cli.py tests/test_speedup_report.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Results

- GLASS total elapsed: 35.32760219998454 s.
- Reference total black-box elapsed: 1092.541 s.
- Total speedup: 30.925987951723428x.
- GLASS resident alignment/LN/integration estimate: 3.3542319999469328 s.
- Reference FastIntegration ProcessingHistory span: 225.69198 s.
- Alignment/LN/integration estimate speedup: 67.28573932976929x.
- Compare shape match: true.
- Compared pixels: 61,651,200.
- Coverage fraction with `min_coverage=1`: 1.0.
- Full-frame RMS difference: 319.70719017059304.
- Full-frame absolute difference p99: 140.8788137563224.
- Acceptance audit: passed, failed checks 0.
- Mainline audit: passed, failed checks 0.

## Per-Stage Timing

- `resident_reference_scout`: 5.083710200000496 s.
- `resident_calibration_integration`: 29.529289199999766 s.
- `light_read_upload_calibrate`: 22.819604300006176 s.
- `resident_registration_warp`: 0.3021223999458016 s.
- `resident_local_normalization`: 0.4433688999997685 s.
- `resident_integration`: 2.6087407000013627 s.
- `output_write`: 0.23423470000125235 s.

## Test Results

- Focused pytest:
  `97 passed`.
- Ruff:
  `All checks passed`.
- Full pytest:
  `1455 passed in 65.83s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limits

- Gate711 is a baseline and evidence gate, not the next optimization gate.
- The run is slower than Gate707's 10.697529399883933 s run. The measured regression is dominated by resident read/upload/calibration timing, not by integration math.
- The comparison thresholds in the acceptance audit are gate-local full-frame ADU thresholds for this direct FITS/XISF comparison. They are not a new release-level numerical tolerance.
- Source-DQ sidecars were not present in this dataset; the real DQ/mask evidence here is coverage, rejection, warp-edge, DQ map, and sample-accounting closure through the resident integration chain.

## Artifacts

- Compare HTML:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\glass_vs_wbpp_full_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\glass_vs_wbpp_full_compare.json`
- Compare diagnostics:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\compare_diagnostics`
- Speedup summary:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_speedup_summary.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_acceptance_audit.json`
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_mainline_audit.json`
- Runtime compare:
  `C:\glass_runs\phase2_s2_gate711_real_200_stackengine_ab_baseline\runs_20260627_080659\gate711_runtime_compare_vs_gate707.json`

## Next Step

- Next substantive gate should optimize resident I/O, upload, and calibration scheduling on the real 200-light path.
- Specifically investigate why Gate711's `light_read_upload_calibrate` was 22.819604300006176 s versus Gate707's 2.9152304000454023 s, then make the default path robust to cold/contended I/O windows without changing scientific outputs.

## Clean-Room

- Compliant.
- Used GLASS code, GLASS run artifacts, and user-generated black-box timing/history/output files only.
- Did not inspect or use proprietary implementation source.
