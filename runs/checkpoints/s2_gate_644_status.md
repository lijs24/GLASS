# S2-Gate 644 Status: Reference Health Sample Input Reuse

## Gate

- Gate: S2-Gate 644
- Status: passed
- Date: 2026-06-25
- Objective: reduce resident reference-health execution overhead by reusing
  sampled light/bias/dark/flat inputs between CPU calibrated checks and CUDA
  calibrated diagnostics, without changing reference-health math, frame
  admission, or output pixels.

## Completed

- Added a sampled-input cache to `resident_reference_health`.
- The cache stores only strided sample inputs, not full image crops.
- CPU calibrated reference-health rows fill the cache.
- CUDA calibrated diagnostic rows reuse the same sampled inputs while still
  running separate CUDA calibration and CUDA catalog logic.
- Cache diagnostics are written into `resident_reference_health.json`:
  enabled flag, hit count, miss count, and stored bytes.
- The cache is enabled only when CUDA calibrated diagnostics are available, so
  CPU-only runs do not retain extra sampled inputs.
- Added focused test assertions proving CUDA calibrated diagnostics hit the
  cache after the CPU calibrated pass fills it.
- Updated Phase 2 docs, validation summary, and algorithm-source independence
  log.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_reference_health.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py -k "resident_reference_health"
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final --resident-mainline-framework-gate strict --resident-mainline-min-lights 200 --resident-mainline-min-active-frames 190 --resident-mainline-max-masked-frames 10
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_vs_wbpp_compare.html --glass-time-seconds 11.457953899982385 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate643_stackengine_dq_postcondition\runs_20260625_170853\candidate_default_strict --candidate-run C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict --out C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_vs_gate643_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_vs_gate643_regression_gate.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\manifest.json --glass-run C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict\warp_quality_contract.json --require-warp-quality-contract
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict --acceptance-audit C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_acceptance_audit.json --compare-json C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_mainline_audit.md --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --require-acceptance --require-compare --fail-on-not-green
.\.venv\Scripts\python.exe -m glass.cli doctor --json C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_doctor.json --allow-cpu-only
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident reference-health tests: `6 passed, 75 deselected`.
- Full pytest: `1350 passed in 59.69 s`.
- Ruff: all touched files passed.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict`.
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\gate644_ab_summary.json`.
- `resident_reference_health.json`: passed.
- Sample input cache: enabled, `64` misses, `64` hits, stored bytes
  `9437184`.
- CPU scout row reuse remained enabled.
- Calibrated reference remained `F000079`.
- CUDA-calibrated diagnostic reference remained `F000114`.
- `resident_mainline_framework.json`: passed.
- GLASS elapsed: `11.457953899982385 s`.
- Black-box reference elapsed: `1092.541 s`.
- Speedup: `95.35219023718358x`.
- Resident reference-health stage: `0.4174907000269741 s`.
- Resident calibration/integration stage: `9.786083100014366 s`.
- Frame accounting: `200` planned lights, `193` integrated frames, `7`
  zero-weight/masked frames.
- Resident regression versus Gate643: passed, elapsed ratio
  `0.9631800297627578`.
- Compare at coverage >= `190`: shape match true, RMS
  `0.0056241382952344435`, p99 absolute difference
  `0.002143551869085057`, coverage fraction `0.9749333995120938`, compared
  pixels `60105814`.
- Acceptance audit: passed.
- Phase 2 mainline audit: passed.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `resident_reference_health.json`
- `resident_mainline_framework.json`
- `run_timing.json`
- `gate644_vs_wbpp_compare.json`
- `gate644_vs_gate643_regression_gate.json`
- `gate644_acceptance_audit.json`
- `gate644_mainline_audit.json`
- `gate644_ab_summary.json`
- `gate644_doctor.json`

## Known Limitations

- This gate optimizes sampled reference-health I/O and slicing only.
- It does not change the dominant resident calibration/integration stage.
- CPU and CUDA calibrated health checks still compute their metrics separately;
  only their sampled inputs are shared.

## Next Step

- Target the largest remaining measured stage:
  resident calibration/integration execution, especially the read/upload/
  calibration scheduling and resident integration reducer path.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-owned reference scout/health artifacts,
  GLASS CPU/CUDA calibration and catalog code, and user-owned benchmark/
  reference outputs.
- No external/proprietary implementation source was read, copied, summarized,
  or reworked.
- Input image directories were treated as read-only.
