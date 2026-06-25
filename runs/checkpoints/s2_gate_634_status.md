# S2-Gate 634 Status: Latest-HEAD Real 200-Light Acceptance

## Gate

S2-Gate 634 is a self-audit and mainline acceptance checkpoint. It stops the
recent drift toward small report/default-promotion gates and verifies the
current HEAD against the real 200-light objective: same benchmark data, same
black-box reference output, clear speed advantage, stable image agreement, and
passing pipeline/StackEngine/warp contracts.

## Completed

- Reused the latest green HEAD real 200-light GLASS run from Gate633:
  `C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2`.
- Recomputed the GLASS-vs-reference compare for the latest HEAD output:
  `C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_vs_wbpp_compare.json`.
- Generated a speedup summary with a hard `50x` minimum speedup threshold:
  `C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_wbpp_speedup_summary.json`.
- Ran `glass acceptance-audit` with real-data frame-count, speed, coverage,
  compare, pipeline, StackEngine, and warp-quality thresholds:
  `C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_acceptance_audit.json`.
- Updated Phase 2 and validation documentation so the latest acceptance record
  points at Gate634 instead of older hot-path evidence.

## Real 200-Light Results

- Gate root:
  `C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407`
- GLASS elapsed: `10.735156700015068 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `101.77224520611482x`.
- Light frame count: `200`.
- Active weighted frames: `193`.
- Zero-weight frames: `7`.
- Calibration frames: `20` bias, `20` dark, `20` flat.
- Compare shape match: `true`.
- Coverage fraction: `0.9749333995120938`.
- Compared pixels: `60105814`.
- RMS difference: `0.0056241382952344435`.
- p99 absolute difference: `0.002143551869085057`.
- Pipeline contract: passed.
- StackEngine contract: passed.
- Warp quality contract: passed.
- Acceptance audit status: passed.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_vs_wbpp_compare.html --glass-time-seconds 10.735156700015068 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\compare_diagnostics

.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_wbpp_speedup_summary.json --markdown C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_wbpp_speedup_summary.md --min-speedup 50

.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2\manifest.json --glass-run C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate634_latest_head_ab\runs_20260625_145407\gate634_latest_head_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2\warp_quality_contract.json --require-warp-quality-contract

.\.venv\Scripts\python.exe -m pytest -q tests/test_speedup_report.py tests/test_acceptance_audit.py tests/test_resident_runtime_compare.py
.\.venv\Scripts\ruff.exe check src tests docs --select E,F --ignore E501
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused speedup/acceptance/runtime tests: `56 passed in 1.61s`.
- Ruff: passed.
- Full pytest: `1327 passed in 62.87s`.

## CUDA Availability

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Driver: `596.21`.
- Reported VRAM from the latest run family: about `97887 MiB`.

## Known Limits

- This gate did not run a fresh GLASS processing pass; it reused the latest
  green Gate633 HEAD run because no processing code changed before the
  acceptance audit.
- This gate intentionally does not improve runtime. It verifies that the latest
  HEAD still satisfies the real 200-light acceptance bar after recent changes.
- The next gate must return to a processing-framework change rather than
  another evidence-only checkpoint.

## Next Step

Proceed to a substantive framework gate. Preferred candidates:

- Resident registration/warp orchestration cleanup that reduces host/device
  round trips while preserving the `193 / 7` frame accounting.
- A cooperative or segmented resident CUDA winsorized reducer that scales past
  the bounded local-array implementation.
- Deeper native read/H2D/calibration overlap using CPU RAM and pinned buffers
  as a cache layer under the 96 GiB VRAM resident design.

## Clean-Room Compliance

Compliant. The gate uses GLASS-generated outputs, user-owned benchmark inputs,
and user-generated black-box reference timing/output artifacts. It does not
inspect, copy, summarize, or rework external/proprietary implementation source,
and it does not modify input image directories.
