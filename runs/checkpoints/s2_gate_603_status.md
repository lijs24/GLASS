# S2-Gate 603 Status: Default Auto Hardened 200-Frame Winsorized Integration

## Gate

S2-Gate 603

## Completed

- Promoted supported resident CUDA `winsorized_sigma` auto groups from the old
  64-frame guarded window to the native hardened prototype limit of 256 frames.
- Added resident auto large-stack rejection guard resolution:
  - implicit base default remains `rejection_max_fraction=0.5`;
  - supported resident auto groups above 64 frames use effective
    `rejection_max_fraction=0.015`;
  - explicit CLI/plan guard values are preserved.
- Recorded guard source/resolution in:
  - resident winsorized runtime contract;
  - resident integration dispatch artifact;
  - output rows;
  - rejection descriptors;
  - top-level integration results.
- Verified that the 200-light M38 default command, with no explicit
  `--resident-winsorized-mode hardened_cpu_parity` and no explicit
  `--integration-rejection-max-fraction`, resolves to:
  - requested mode: `auto`;
  - effective mode: `hardened_cpu_parity`;
  - guard source: `resident_auto_large_stack_coverage_guard`;
  - effective guard: `0.015`.
- Updated documentation:
  - `docs/integration_model.md`;
  - `docs/known_limitations.md`;
  - `docs/algorithm_sources.md`;
  - `docs/phase2_algorithm_hardening.md`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_resident_auto_winsorized_contract_selects_hardened_within_limit tests\test_resident_cuda_run.py::test_resident_auto_winsorized_contract_selects_hardened_for_200_frame_default tests\test_resident_cuda_run.py::test_resident_auto_winsorized_contract_falls_back_over_hardened_limit tests\test_resident_cuda_run.py::test_resident_auto_large_stack_default_rejection_guard_is_coverage_preserving tests\test_resident_cuda_run.py::test_resident_auto_large_stack_preserves_explicit_rejection_guard tests\test_resident_cuda_run.py::test_cli_resident_cuda_hardened_winsorized_matches_cpu_baseline
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\compare_default_auto_hardened_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 12.4060653 --reference-time-seconds 1092.541 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128 --diagnostics-dir C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\compare_default_auto_hardened_diagnostics_scaled_coverage190
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened\manifest.json --glass-run C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\compare_default_auto_hardened_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\acceptance_default_auto_hardened_audit.json --markdown C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\acceptance_default_auto_hardened_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened\warp_quality_contract.json
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident auto/hardened tests: `6 passed in 1.10s`.
- Ruff: `All checks passed!`.
- Full pytest: `1280 passed in 52.95s`.

## Real 200-Light Validation

- Run directory:
  `C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\real_200_default_auto_hardened`
- Compare report:
  `C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\compare_default_auto_hardened_vs_wbpp_fastintegration_scaled_coverage190.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\compare_default_auto_hardened_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\acceptance_default_auto_hardened_audit.json`
- Acceptance markdown:
  `C:\glass_runs\phase2_s2_gate603_default_auto_hardened_200\acceptance_default_auto_hardened_audit.md`

Key metrics:

- Acceptance status: `passed`.
- Acceptance checks: `128`, failures: `0`.
- GLASS shell elapsed: `12.4060653 s`.
- GLASS run timing: `11.991980199934915 s`.
- WBPP black-box timing: `1092.541 s`.
- Acceptance speedup vs WBPP: `91.10597097266134x`.
- Compare speedup from explicit shell timing: `88.06506926898088x`.
- Native hardened integration timing: `3.7137935999780893 s`.
- Requested/effective winsorized mode: `auto` -> `hardened_cpu_parity`.
- Effective rejection max fraction: `0.015`.
- Guard source: `resident_auto_large_stack_coverage_guard`.
- Coverage>=190 acceptance fraction: `1.0`.
- RMS diff vs WBPP reference: `0.0055611675566298235`.
- Absolute diff p99 vs WBPP reference: `0.002161672392394391`.
- DQ count-map input dtypes:
  `coverage=uint16`, `low_rejection=uint16`, `high_rejection=uint16`,
  `geometric_warp_coverage=float32`.

## CUDA Availability

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total VRAM: `97886 MiB`.
- Native backend: available.

## Known Limitations

- Hardened resident winsorized remains a one-iteration prototype limited to
  256 frames per filter/shape group.
- Groups above 256 frames still fall back to `fast_approx` until segmented
  hardened reductions are implemented.
- Minimal-output runs still prefer the faster non-parity approximation.
- The 200-light default hardened path is slower than the fast approximation,
  but remains well above the benchmark speed contract.

## Next Step

Target a larger Phase 2 compute/completeness lever:

- segmented hardened reductions for groups above 256 frames;
- resident registration/warp orchestration and batching;
- broader source-DQ/mask propagation cases through the resident default path.

## Clean-Room Compliance

Compliant. This gate changes GLASS-owned runtime policy, rejection guard
resolution, and artifact fields only. Validation uses GLASS tests, GLASS
artifacts, user-owned 200-light inputs, and user-generated black-box reference
outputs. No external or proprietary implementation source was inspected,
copied, summarized, or reworked.
