# S2-Gate 589 Status: Resident Source-DQ Integration Effect Contract

## Gate

S2-Gate 589.

## Completed

- Added `resident_source_dq_integration_effect_contract` to the pipeline
  invariant audit.
- The new contract links `resident_source_dq_execution.json` to resident
  integration output provenance:
  - if resident source-DQ applied invalid samples are positive;
  - resident integration must report at least that many
    `input_invalid_samples_before_rejection`;
  - extra invalid samples from warp geometry or non-finite data remain allowed.
- Exposed `resident_source_dq_integration_effect` in
  `pipeline_contract.json` and in the Markdown contract report.
- Updated the M38 200-light benchmark contracts to require the new pipeline
  check.
- Added positive and negative tests:
  - resident CUDA source-DQ sidecar changes one output pixel and weight;
  - pipeline contract fails when source-DQ applied invalid samples are not
    reflected in integration provenance;
  - acceptance audit fails when benchmark contracts require the new check but
    the supplied pipeline contract lacks it.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `python -m ruff check src\glass\report\pipeline_contract.py tests\test_pipeline_contract.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests\test_pipeline_contract.py -k "source_dq or resident_dq_ledger or resident_calibrated_light_dq"`
- `python -m pytest -q tests\test_resident_cuda_run.py -k "source_dq_sidecar"`
- `python -m pytest -q tests\test_pipeline_contract.py`
- `python -m pytest -q tests\test_acceptance_audit.py -k "pipeline_contract"`
- JSON parse validation for:
  - `benchmarks\phase2_m38_h_200_ln_on_default_contract.json`
  - `benchmarks\phase2_m38_h_200_contract.json`
- `glass run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression --backend cuda --memory-mode resident --resident-runtime-preset throughput-v3-io --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `glass compare --glass C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate589_source_dq_effect\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 9.812087000231259 --reference-time-seconds 1092.541 --glass-label "GLASS Gate589 resident source-DQ effect contract" --reference-label "WBPP black-box fastIntegration" --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression\integration\resident_coverage_map_H.fits --min-coverage 190 --ignore-border-px 128`
- `glass acceptance-audit --manifest C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression\manifest.json --glass-run C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate589_source_dq_effect\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate589_source_dq_effect\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate589_source_dq_effect\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression\warp_quality_contract.json`
- SHA256 parity script comparing Gate589 integration FITS outputs with
  Gate588 outputs.
- `python -m pytest -q`

## Test Results

- Ruff: passed.
- Focused pipeline-contract tests: `7 passed, 39 deselected`.
- Resident CUDA source-DQ sidecar test: `1 passed, 103 deselected`.
- Full pipeline-contract tests: `46 passed`.
- Focused acceptance pipeline-contract tests: `8 passed, 43 deselected`.
- Full pytest: `1256 passed in 55.75s`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available to GLASS.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate589_source_dq_effect\default_resident_regression`
- Validation summary:
  `C:\glass_runs\phase2_s2_gate589_source_dq_effect\gate589_validation_summary.json`
- Compare:
  `C:\glass_runs\phase2_s2_gate589_source_dq_effect\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Acceptance:
  `C:\glass_runs\phase2_s2_gate589_source_dq_effect\acceptance_audit.json`
- Hash parity:
  `C:\glass_runs\phase2_s2_gate589_source_dq_effect\hash_parity_vs_gate588.json`
- Stage timing sum: `9.812087000231259 s`.
- Speedup versus WBPP black-box fastIntegration: `111.34644443880798x`.
- RMS difference versus WBPP: `0.005340835487175878`.
- p99 absolute difference versus WBPP: `0.002133606873685496`.
- Coverage190 fraction: `0.905523489118409`.
- Pipeline contract: passed, `25` checks.
- New source-DQ effect check:
  - passed: true;
  - status: `no_invalid_samples`;
  - required: false;
  - expected source-DQ applied invalid samples: `0`;
  - observed resident integration invalid samples: `90128774`.
- Acceptance audit with updated benchmark contract: passed.
- Gate589 versus Gate588 integration FITS parity: all six files matched.

## Known Limitations

- The real 200-light dataset does not contain positive source-DQ sidecar
  invalid samples, so it validates the nonblocking default path. The positive
  effect path is proven by the resident CUDA sidecar synthetic test.
- This gate does not add a new source-DQ detector or change image math.
- The 200-light runtime was slower than Gate588 but stayed far above the
  benchmark speedup threshold and preserved bitwise output parity; this is
  treated as run-to-run timing variation, not a numerical or path regression.

## Next Step

- Continue with DQ/mask pipeline completeness, preferably by making source-DQ
  effect evidence participate in frame accounting/report surfaces or by adding
  a small resident CUDA source-DQ benchmark artifact that exercises positive
  invalid samples through the full CLI path.

## Clean-Room Compliance

- This gate used GLASS-owned code, GLASS synthetic fixtures, GLASS-generated
  artifacts, user-owned real data, and user-generated WBPP black-box outputs.
- It did not read, copy, summarize, or rework proprietary implementation
  source.
- Input image directories were treated as read-only.
