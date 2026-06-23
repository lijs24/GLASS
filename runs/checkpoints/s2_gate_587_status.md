# S2-Gate 587 Status: Default Run Auto Resident Warp-Quality Contract

## Gate

S2-Gate 587

## Completed

- Added automatic resident in-VRAM `warp_quality_contract.json` and
  `warp_quality_contract.md` emission to `glass run --memory-mode resident`
  after the automatic StackEngine contract.
- Recorded `warp_quality_contract` in `run_state.json` and
  `run_timing.json`.
- Added default resident warp-quality thresholds:
  - `min_valid_fraction=0.75` when resident geometric coverage provenance is
    present;
  - `max_skipped_frames=10`;
  - `require_all_registered=true`;
  - `require_artifacts=true` only when coverage and DQ map paths are emitted;
  - `pixel_verify=false` for the in-VRAM resident surface.
- Extended resident warp-quality valid-fraction derivation to use
  `geometric_zero_pixels`, `geometric_warp_coverage.finite_pixels`, or the
  older `geometric_full_pixels` field.
- Added focused resident CUDA tests for automatic run-local warp-quality
  contract creation.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\report\warp_quality.py tests\test_resident_cuda_run.py tests\test_warp_quality_contract.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_warp_quality_contract.py tests\test_resident_cuda_run.py -k "test_cli_resident_cuda_run_smoke or test_cli_resident_cuda_run_generates_source_dq_cache_route or warp_quality"`
- `.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate587_auto_warp_quality\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 7.614031400065869 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\manifest.json --glass-run C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate587_auto_warp_quality\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate587_auto_warp_quality\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate587_auto_warp_quality\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\warp_quality_contract.json --require-warp-quality-contract`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Ruff: passed.
- Focused tests: `8 passed, 102 deselected in 1.37s`.
- Full pytest: `1252 passed in 53.65s`.

## Real 200-Light Validation

- Run directory:
  `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract`
- Run failed stage: none.
- Stage timing sum: `7.614031400065869 s`.
- Automatic `warp_quality_contract` stage timing:
  `0.022742300061509013 s`.
- Pipeline contract: passed, `24` checks.
- StackEngine contract: passed, default promotion ready.
- Warp-quality contract: passed, `9` checks.
- Warp-quality active/masked frames: `193 / 7`.
- Warp-quality artifact-ready active frames: `193`.
- Warp-quality min valid fraction: `1.0`.
- Hash parity versus Gate586: all six integration FITS artifacts matched.
- Compare versus WBPP black-box fastIntegration:
  - WBPP black-box reference elapsed: `1092.541 s`;
  - GLASS elapsed: `7.614031400065869 s`;
  - speedup: `143.4904773298608x`;
  - coverage190 fraction: `0.905523489118409`;
  - RMS difference: `0.005340835487175878`;
  - p99 absolute difference: `0.002133606873685496`.
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\acceptance_audit.json`
- Acceptance status: passed.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\warp_quality_contract.json`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\warp_quality_contract.md`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\pipeline_contract.json`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\default_auto_contract\stack_engine_contract.json`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\acceptance_audit.json`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\acceptance_audit.md`
- `C:\glass_runs\phase2_s2_gate587_auto_warp_quality\hash_parity_vs_gate586.json`

## Known Limitations

- This gate adds default-path evidence and hard acceptance checks; it does not
  optimize I/O, registration, warp, or integration runtime.
- Resident pixel verification is still delegated to DQ/count-map and pipeline
  pixel-closure contracts because the default resident path does not
  materialize per-frame registered FITS caches.
- The default `max_skipped_frames=10` is benchmark-oriented and should be made
  configurable before broader user-facing release policy is finalized.

## Next Step

Return to substantive Phase 2 mainline work: StackEngine default-path execution,
DQ/mask pipeline contract coverage, real 200-light regression, and CUDA
resident performance/numerical consistency. Avoid additional report-only or
release-evidence gates unless they directly block those goals.

## Clean-Room Compliance

Compliant. This gate uses only GLASS-owned source code, GLASS-generated run
artifacts, user-owned input/output data, and user-generated WBPP black-box
timing/reference outputs. It does not read, copy, summarize, or rework external
implementation source.
