# S2-Gate 635 Status: Guarded CUDA Reference Scout Default

## Gate

S2-Gate 635: guarded CUDA resident reference scout default.

## Completed Content

- Promoted resident reference scout `auto` from CPU-only avoidance to a guarded CUDA-attempt policy.
- `auto` now tries CUDA catalog selection when available, then validates the CUDA-selected reference against CPU scoring over the same sampled frame subset.
- If the CPU guard fails, the official scout falls back to CPU and records the CUDA candidate diagnostics.
- If CUDA candidate collection errors in `auto`, the official scout falls back to CPU and records the CUDA error count.
- Explicit `--resident-reference-scout-backend cuda` remains strict and is still protected by the resident reference-health gate.
- Added focused tests for:
  - CUDA auto guard pass;
  - CUDA auto guard miss and CPU fallback;
  - CUDA candidate error and CPU fallback;
  - existing explicit CUDA unavailable/error behavior and resident reference-health blocking.
- Updated Phase 2 hardening, validation, and algorithm source documentation.

## Real 200-Light Validation

- Evidence root:
  `C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002`.
- Candidate run:
  `C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout`.
- Dataset: M38 H-alpha, 200 lights, 20 bias, 20 dark, 20 flat.
- Reference scout result: requested `auto`, attempted `cuda`, effective `cpu`.
- CUDA candidate reference: `F000215`.
- CPU guard reference: `F000225`.
- CPU guard evidence for `F000215`:
  - selected CPU star ratio: `0.7843137254901961`;
  - selected CPU rank fraction: `0.4411764705882353`;
  - guard status: `fallback_to_cpu`.
- GLASS total elapsed: `10.969763099914417 s`.
- Resident calibration/integration stage elapsed: `9.63287049997598 s`.
- Active/masked frames: `193 / 7`.
- Resident regression gate versus Gate633: passed, elapsed ratio `1.0218540265834237` with max allowed `1.2`.
- Black-box reference elapsed: `1092.541 s`.
- Acceptance speedup: `99.5956785984306x`.
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
- `.\.venv\Scripts\python.exe -m ruff check src/glass/engine/resident_reference_scout.py tests/test_cli_smoke.py`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final`
- `.\.venv\Scripts\glass.exe resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate633_lazy_fallback\runs_20260625_144040\candidate_lazy_fallback_r2 --candidate-run C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout --out C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\gate635_resident_regression_gate.json --markdown C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\gate635_resident_regression_gate.md --max-elapsed-ratio 1.20 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\gate635_guarded_vs_wbpp_compare.html --glass-time-seconds 10.969763099914417 --reference-time-seconds 1092.541 --glass-label GLASS --reference-label WBPP --glass-scale 8.7644349571156089E-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout\manifest.json --glass-run C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\gate635_guarded_vs_wbpp_compare.json --out C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\gate635_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\gate635_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 50 --min-coverage-fraction 0.97 --max-rms-diff 0.006 --max-abs-diff-p99 0.003 --pipeline-contract-json C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate635_guarded_cuda_reference_scout\runs_20260625_151002\candidate_guarded_cuda_reference_scout\warp_quality_contract.json --require-warp-quality-contract`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused reference scout/health/admission tests: `12 passed, 67 deselected`.
- Ruff over touched Python files: passed.
- Full pytest: `1329 passed in 60.11s`.

## CUDA Status

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.

## Known Limitations

- The CUDA scout still operates on sampled raw-light crops and is not yet a calibrated, fully resident reference selector.
- On the current M38 200-light benchmark, CUDA raw-catalog selection remains diagnostic because the CPU guard correctly falls back to the CPU reference.
- The guard adds a small amount of reference-scout overhead by measuring both CUDA and CPU catalogs when CUDA is available.
- This gate does not optimize resident registration/warp or the winsorized reducer itself.

## Next Step

Continue with a substantive Phase 2 gate: resident registration/warp orchestration, a fully resident calibrated reference-health model, DQ/mask pipeline simplification, or a cooperative/segmented resident reducer for heavier stacks.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned FITS reads, CPU star metrics, CUDA catalog primitives, generated artifacts, and user-owned benchmark/reference outputs. It does not read, copy, summarize, or rework external/proprietary implementation source and does not modify input image directories.
