# S2-Gate 480 Status: Resident Light-Loop Master-Load Accounting

- Gate: S2-Gate 480
- Status: green checkpoint
- Date: 2026-06-22

## Completed

- Corrected resident light-loop timing semantics so master calibration
  build/load performed inside the light loop is explicitly accounted for.
- Added resident timing fields:
  - `light_master_build_or_load_in_loop`
  - `light_loop_accounted_without_master`
  - `light_loop_accounted`
  - `light_loop_unaccounted`
  - `light_loop_unaccounted_without_master`
- Updated `resident_light_pipeline_profile` so master build/load can be the
  dominant component and recommends `reuse_or_prebuild_master_calibration_cache`
  when appropriate.
- Updated HTML resident runtime rows to display both corrected unaccounted
  timing and the legacy without-master diagnostic bucket.
- Updated `docs/algorithm_sources.md` with clean-room provenance and
  limitations.
- Ran a fresh real M38 H-alpha 200-light baseline probe.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\engine\resident_light_pipeline_profile.py src\glass\report\html_report.py tests\test_resident_cuda_run.py tests\test_resident_light_pipeline_profile.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_light_pipeline_profile.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke
.\.venv\Scripts\glass.exe resident-ab-matrix-plan --root C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out runs\checkpoints\s2_gate_480_ab_matrix_plan.json --markdown runs\checkpoints\s2_gate_480_ab_matrix_plan.md --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190.0 --min-speedup 2.0 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --min-gpu-free-mib 65000 --max-gpu-utilization 20 --min-disk-free-gib 8
.\.venv\Scripts\glass.exe resident-ab-matrix-execute --plan runs\checkpoints\s2_gate_480_ab_matrix_plan.json --out runs\checkpoints\s2_gate_480_ab_matrix_execution_baseline.json --variant throughput_v1_lanczos3_parity --wait-ready-timeout-s 180 --wait-ready-interval-s 5 --wait-ready-consecutive-samples 3 --fail-on-failed --fail-on-blocked
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate479_source_dq_fastskip_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\gate480_vs_gate479_baseline.html --glass-label "Gate480 light-loop accounting" --reference-label "Gate479 source-DQ fast-skip" --glass-coverage-map C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\runs\throughput_v1_lanczos3_parity\integration\resident_coverage_map_H.fits --min-coverage 190.0
.\.venv\Scripts\python.exe -m ruff check src tests docs
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_light_pipeline_profile.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Ruff targeted: passed.
- Initial focused tests: `4 passed in 0.39s`.
- Ruff full: passed.
- Focused tests after real probe: `5 passed in 1.72s`.
- First full pytest failed one expected assertion because the resident light
  pipeline profile can now report `master_build_or_load` as the dominant
  component.
- After updating the assertion, focused retry passed: `4 passed in 0.64s`.
- Final full pytest: `1120 passed in 40.80s`.

## Real 200-Light Result

Reference WBPP black-box elapsed time:

- `1092.541 s`

Gate480 baseline `throughput_v1_lanczos3_parity`:

- GLASS elapsed: `30.73063499998534 s`
- Speedup vs WBPP: `35.552177818666x`
- Acceptance: passed
- Weighted frames: `193`
- Zero-weight frames: `7`
- Effective FITS mode: `native_u16_gpu`
- Source-DQ fast-skip: enabled for `200` frames

## Corrected Timing

- Light loop total: `14.049948500003666 s`
- Master build/load inside light loop: `10.830587800010107 s`
- Accounted without master: `3.019770900020376 s`
- Accounted with master: `13.850358700030483 s`
- Corrected `light_loop_unaccounted`: `0.19958979997318238 s`
- Legacy `light_loop_unaccounted_without_master`: `11.03017759998329 s`
- Resident light profile dominant component: `master_build_or_load`
- Resident light profile recommendation:
  `reuse_or_prebuild_master_calibration_cache`

## Gate479 Comparison

- Gate479 elapsed: `30.656666999973822 s`
- Gate480 elapsed delta: `+0.0739680000115186 s`
- Gate480 speedup delta: `-0.08577982366129078x`
- Gate480 vs Gate479 baseline pixel diff:
  - RMS: `0.0`
  - p99: `0.0`
  - max abs diff: `0.0`
  - shape match: `true`

## Artifacts

- `runs/checkpoints/s2_gate_480_ab_matrix_plan.json`
- `runs/checkpoints/s2_gate_480_ab_matrix_plan.md`
- `runs/checkpoints/s2_gate_480_ab_matrix_execution_baseline.json`
- `runs/checkpoints/s2_gate_480_real_baseline_summary.json`
- `C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\reports\throughput_v1_lanczos3_parity_report.html`
- `C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\throughput_v1_lanczos3_parity_vs_wbpp.html`
- `C:\glass_runs\phase2_s2_gate480_lightloop_accounting_ab_real\compare\gate480_vs_gate479_baseline.html`

## Known Limitations

- This is a diagnostic semantics correction, not a speed optimization.
- The real run remains storage/cache sensitive.
- `master_build_or_load` is now correctly identified as the dominant current
  light-loop component for this benchmark, but the physical native FITS read
  cumulative time remains a separate bottleneck at about `20.45 s`.

## Next Step

The next substantive gate should reduce or amortize master build/load for
resident runs, for example by proving a reusable resident master cache path or
prebuilding masters before the timed light-ingest loop without changing the
accepted 200-light science output. FITS read scheduling remains the second
major optimization target.

## Clean-Room Compliance

- This gate used GLASS-owned code and artifacts plus user-generated WBPP
  black-box timing/output metadata.
- No official PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
- Original image directories were not modified.
