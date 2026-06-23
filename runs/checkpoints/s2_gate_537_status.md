# S2-Gate 537 Status: Real 200-Light Current-Head A/B and Speedup Evidence Contract

## Gate

S2-Gate 537

## Completed

- Returned to the Phase 2 mainline real-data objective after Gate536.
- Reran the current HEAD on the real M38 H-alpha 200-light resident CUDA path.
- Kept the Gate536 science and scheduling defaults: resident CUDA,
  `similarity_cuda_triangle`, Lanczos3 warp, Winsorized Sigma rejection,
  weighting off, local normalization off, `LIGHT_H_0136` reference, audit maps,
  and shared resident master cache.
- Compared the current run against the Gate536 default rerun by SHA-256 for all
  six output maps: master, weight, coverage, low rejection, high rejection, and
  DQ. All six are bit-identical.
- Generated a fresh coverage-masked compare against the WBPP FastIntegration
  black-box master.
- Strengthened `glass.report.speedup_report` so speedup summaries include
  resident peak VRAM, shared master-cache hits/misses, FITS read mode, resident
  timing components, compared pixels, and compare timing speedup.
- Updated tests and validation docs with the current real A/B evidence.

## Commands Run

- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 5.3052115 --reference-time-seconds 1092.541 --glass-label "GLASS Gate537 resident CUDA current" --reference-label "WBPP black-box fastIntegration" --glass-scale=1.545301547671945e-05 --glass-offset=-9.765786009702931e-05 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\python.exe benchmarks\summarize_wbpp_speedup.py --glass-run C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_wbpp_speedup_summary_gate537_current.json --markdown runs\benchmarks\m38_wbpp_speedup_summary_gate537_current.md --min-speedup 2.0`
- `.venv\Scripts\python.exe -m compileall -q src\glass\report\speedup_report.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_speedup_report.py`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused speedup report tests: `3 passed in 0.17s`.
- Full pytest: `1176 passed in 43.10s`.

## Real 200-Light Results

- Current run:
  `C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default`.
- Shell elapsed: `5.3052115 s`.
- Internal `run_timing.json`: `4.940610599995125 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup by internal timing: `221.13481277012156x`.
- Speedup by compare shell timing: `205.9373127725445x`.
- Planned light frames: `200`.
- Active integrated frames: `193`.
- Zero-weight / quality-rejected frames: `7`.
- Shared master cache hits/misses: `1/0`.
- Estimated peak VRAM: `49.608429938554764 GiB`.
- Effective FITS read mode: `native_u16_gpu`.

## Stage Timing

- Light read/upload/calibrate: `2.4421659000217915 s`.
- Resident registration/warp: `0.2569173000520095 s`.
- Resident integration: `0.30478270002640784 s`.
- Output write: `0.2353500999743119 s`.

## Numerical Validation

- The current run is bit-identical to the Gate536 default rerun for all six
  output maps.
- Coverage-masked compare against WBPP FastIntegration:
  - shape match: true;
  - RMS: `0.0004279821839256963`;
  - p50 abs diff: `2.808647695928812e-05`;
  - p90 abs diff: `7.045280653983355e-05`;
  - p99 abs diff: `0.0001313822576776147`;
  - p99.9 abs diff: `0.0009162264885380911`;
  - coverage fraction: `0.9892770479074376`;
  - compared pixels: `56997300`.

## Artifacts

- Gate summary:
  `runs/checkpoints/s2_gate_537_real_ab_summary.json`.
- Speedup summary JSON:
  `runs\benchmarks\m38_wbpp_speedup_summary_gate537_current.json`.
- Speedup summary Markdown:
  `runs\benchmarks\m38_wbpp_speedup_summary_gate537_current.md`.
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json`.
- Compare HTML:
  `C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.html`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limits

- This is a shared-master-cache resident hot-path A/B. It does not claim that a
  cold run that rebuilds master calibration frames completes in 5.3 seconds.
- The WBPP comparison remains black-box and uses user-generated WBPP outputs and
  timing metadata.
- GLASS still records known algorithmic differences from WBPP around exact star
  matching, boundary policy, interpolation details, local normalization, and
  rejection implementation.

## Next

- Continue the mainline resident CUDA optimization work, with priority on the
  remaining default wall-time components: light read/upload/calibrate overlap,
  Python orchestration inside the resident light loop, and output/report
  overhead only when it materially affects the default path.

## Clean-Room

- Compliant. This gate used GLASS code, GLASS-generated artifacts, user-owned
  input images, and user-generated WBPP black-box outputs only. It did not
  inspect or copy PixInsight/WBPP/PJSR implementation source or modify input
  directories.
