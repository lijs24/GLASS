# S2-Gate 636 Status: Reference Health For CUDA-Attempt Auto Scout

## Gate

S2-Gate 636: reference health for CUDA-attempt auto scout.

## Completed Content

- Added a reference-health action backend resolver that treats `catalog_backend_resolution.attempted=cuda` as CUDA-attempted even when the official effective scout backend has fallen back to CPU.
- The resident CLI now writes `resident_reference_health.json` for guarded auto CUDA-attempt scout fallback runs.
- `resident_reference_health.json` records both:
  - `scout_backend`: the official effective backend used for the reference;
  - `health_action_backend`: the backend that triggered the health gate.
- Existing calibrated master-cache crosscheck and CUDA-calibrated diagnostic evidence now run for this default path when a resident master cache is supplied.
- Added focused tests for direct health-gate behavior and CLI stage ordering.
- Updated Phase 2 hardening, validation, and algorithm source documentation.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939`.
- Candidate run:
  `C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt`.
- Dataset: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat.
- Reference scout result: requested `auto`, attempted `cuda`, effective `cpu`.
- Official reference: `F000225`.
- Reference-health status: passed.
- Reference-health action: `fail`.
- Reference-health action backend: `cuda`.
- CPU crosscheck reference: `F000225`.
- Calibrated reference: `F000079`.
- Official reference calibrated evidence:
  - star ratio: `0.9032258064516129`;
  - rank fraction: `0.047619047619047616`.
- CUDA-calibrated diagnostic reference: `F000114`.
- Official reference CUDA-calibrated evidence:
  - star ratio: `1.0`;
  - rank fraction: `0.12698412698412698`.
- GLASS total elapsed: `12.167883900227025 s`.
- Reference scout stage elapsed: `0.7453140000579879 s`.
- Reference-health stage elapsed: `1.535151300020516 s`.
- Resident calibration/integration stage elapsed: `9.430013900040649 s`.
- Active/masked frames: `193 / 7`.
- Resident regression gate versus Gate635: passed, elapsed ratio `1.1092202985059865` with max allowed `1.2`.
- Black-box reference elapsed: `1092.541 s`.
- Acceptance speedup: `89.7889073366007x`.
- Compare at coverage >= `190`:
  - shape match: `true`;
  - RMS: `0.0056241382952344435`;
  - p99 absolute difference: `0.002143551869085057`;
  - coverage fraction: `0.9749333995120938`;
  - compared pixels: `60105814`.
- Pipeline contract: passed.
- StackEngine contract: passed.
- Warp quality contract: passed.
- Acceptance audit: passed.

## Commands Run

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cli_smoke.py -k "resident_reference_scout or resident_reference_health or reference_admission"`
- `.\.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_reference_health.py src/glass/cli.py tests/test_cli_smoke.py`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout --candidate-run C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt --out C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\gate636_resident_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\gate636_resident_regression_gate.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\gate636_vs_wbpp_compare.html --glass-time-seconds 12.167883900227025 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.7644349571156089E-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt\manifest.json --glass-run C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\gate636_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\gate636_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\gate636_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate636_reference_health_for_cuda_attempt\runs_20260625_151939\candidate_reference_health_cuda_attempt\warp_quality_contract.json --require-warp-quality-contract`

## Test Results

- Focused reference scout/health/admission tests: `13 passed, 68 deselected`.
- Ruff over touched Python files: passed.
- Full pytest: `1331 passed in 67.33s`.

## CUDA Status

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.

## Known Limitations

- The calibrated reference-health stage rereads bounded samples and adds about `1.535 s` on the real 200-light benchmark.
- This gate strengthens default-path reference admission but does not optimize registration/warp or the winsorized reducer.
- The CUDA-calibrated check remains diagnostic-only; the enforced calibrated crosscheck uses the CPU detector over calibrated samples.

## Next Step

Continue with a substantive Phase 2 gate that either reduces reference-health overhead by reusing resident GPU data, improves resident registration/warp orchestration, simplifies the DQ/mask contract path, or starts a cooperative resident reducer for heavier stacks.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned scout artifacts, resident master cache arrays, CPU/CUDA calibration and star metrics, generated artifacts, and user-owned benchmark/reference outputs. It does not read, copy, summarize, or rework external/proprietary implementation source and does not modify input image directories.
