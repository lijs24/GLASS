# S2-Gate 628 Status: Current 200-Light Default Resident A/B Rebaseline

## Gate

S2-Gate 628

## Completed Content

- Ran the current `main` resident CUDA default path on the real 200-light M38 H
  dataset.
- Compared the candidate run against the Gate626 default resident baseline with
  `glass resident-regression-gate`.
- Compared the candidate master against the WBPP black-box reference output
  with the established scale/offset and coverage threshold.
- Recorded current stage timings and the next optimization target.

## Commands Run

- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate628_real200_default_ab\real_200_default_gate628_20260625_133115 --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\real_200_default_gate626_20260625_131241 --candidate-run C:\glass_runs\phase2_s2_gate628_real200_default_ab\real_200_default_gate628_20260625_133115 --out C:\glass_runs\phase2_s2_gate628_real200_default_ab\resident_regression_gate_gate628_vs_gate626.json --markdown C:\glass_runs\phase2_s2_gate628_real200_default_ab\resident_regression_gate_gate628_vs_gate626.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate628_real200_default_ab\real_200_default_gate628_20260625_133115\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate628_real200_default_ab\gate628_resident_vs_wbpp_compare.html --diagnostics-dir C:\glass_runs\phase2_s2_gate628_real200_default_ab\compare_diagnostics --glass-time-seconds 11.385932999895886 --reference-time-seconds 1092.541 --glass-label GLASS_Gate628 --reference-label WBPP_blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate628_real200_default_ab\real_200_default_gate628_20260625_133115\integration\resident_coverage_map_H.fits --min-coverage 190`

## Test Results

- Gate627 full pytest before this real-data validation: `1322 passed in 60.65 s`.
- Real 200-light `glass run`: completed through integration.
- Real 200-light resident regression gate: passed.
- WBPP black-box compare report: generated.

## Real 200-Light Results

- Candidate run:
  `C:\glass_runs\phase2_s2_gate628_real200_default_ab\real_200_default_gate628_20260625_133115`
- Baseline run:
  `C:\glass_runs\phase2_s2_gate626_deterministic_winsorized\real_200_default_gate626_20260625_131241`
- Candidate elapsed: `11.385932999895886 s`.
- Baseline elapsed: `11.000130000058562 s`.
- Candidate/baseline elapsed ratio: `1.0350725854908325`.
- Active frames: `193 / 200`.
- Regression failed checks: `[]`.
- Resident hardened winsorized total: `3.386850400012918 s`.
- Resident hardened native kernel sync: `3.2286805 s`.
- Native selector: `small_256`.
- Resident winsorized mode: `hardened_cpu_parity`.

## WBPP Black-Box Compare

- Compare JSON:
  `C:\glass_runs\phase2_s2_gate628_real200_default_ab\gate628_resident_vs_wbpp_compare.json`
- Compare HTML:
  `C:\glass_runs\phase2_s2_gate628_real200_default_ab\gate628_resident_vs_wbpp_compare.html`
- Reference elapsed: `1092.541 s`.
- GLASS elapsed: `11.385932999895886 s`.
- Speedup vs WBPP black-box timing: `95.95533365688962x`.
- Shape match: true, `6422 x 9600`.
- Coverage comparison threshold: `min_coverage=190`.
- Compared coverage fraction: `0.9749333995120938`.

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend loaded: yes.

## Known Limits

- This gate does not change algorithms; it is a real-data rebaseline before
  the next optimization gate.
- WBPP compare metrics still show edge/hotspot differences, so the strongest
  correctness proof here is the zero-drift resident regression gate against the
  latest accepted GLASS real 200-light baseline plus passing runtime contracts.

## Next Step

Proceed to a substantive optimization gate targeting the measured bottlenecks:
resident calibration/integration orchestration, hardened winsorized kernel
time, or resident registration/warp orchestration. Any promoted change must
pass the Gate628-style 200-light regression gate.

## Clean-Room Compliance

Compliant. WBPP was used only as a black-box reference output and timing target
through user-generated files. No external proprietary source was inspected,
copied, summarized, or reworked.
