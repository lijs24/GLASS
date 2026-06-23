# S2-Gate 579 Status: Default 200-Light Resident DQ Benchmark Gate

## Gate

S2-Gate 579

## Completed

- Promoted the S2-Gate 578 resident calibrated-light DQ contract from a
  pipeline-contract detail to a required default 200-light benchmark check.
- Updated:
  - `benchmarks/phase2_m38_h_200_ln_on_default_contract.json`;
  - `benchmarks/phase2_m38_h_200_contract.json`.
- Both benchmark contracts now require
  `resident_calibrated_light_dq_contract` in supplied pipeline contracts.
- Updated acceptance-audit fixtures and tests:
  - passing pipeline-contract fixture now carries the resident calibrated-light
    DQ check;
  - added a negative test proving a benchmark contract fails when that check is
    missing.
- Reran the current HEAD resident CUDA default 200-light route and validated it
  against WBPP black-box output with the tightened benchmark contract.

## Commands

- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default --out C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\stack_engine_contract.md --scope all --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\resident_calibration_contract.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\resident_result_contract.json --require-default-ready`
- `.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default --out C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\pipeline_contract_pixel_verify.json --markdown C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\pipeline_contract_pixel_verify.md --pixel-verify --pixel-verify-tile-size 2048`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 7.746504300041124 --reference-time-seconds 1092.541 --glass-label "GLASS Gate579 current HEAD default" --reference-label "WBPP black-box fastIntegration" --glass-scale=8.764434957115609e-06 --glass-offset=0.0006274500691899127 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\manifest.json --glass-run C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\acceptance_audit_gate579.json --markdown C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\acceptance_audit_gate579.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\pipeline_contract_pixel_verify.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\stack_engine_contract.json`
- `.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_wbpp_speedup_summary_gate579_default_contract.json --markdown runs\benchmarks\m38_wbpp_speedup_summary_gate579_default_contract.md --min-speedup 20.0`

Note: an attempted `tests\test_benchmark_contract.py` run found no such test
file; benchmark-contract checks for this gate are covered by
`tests\test_acceptance_audit.py`.

## Test Results

- Acceptance-audit tests: `47 passed in 1.31s`.
- Pipeline-contract tests: `44 passed in 1.81s`.
- Full test suite: `1242 passed in 52.38s`.
- `git diff --check`: passed.

## Real 200-Light Validation

- Run:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default`
- Compare:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Pixel-verified pipeline contract:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\pipeline_contract_pixel_verify.json`
- StackEngine contract:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\stack_engine_contract.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\acceptance_audit_gate579.json`
- Speedup summary:
  `runs\benchmarks\m38_wbpp_speedup_summary_gate579_default_contract.json`
- Gate575 hash parity:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\gate579_vs_gate575_hash_parity.json`

## Key Results

- GLASS run timing total: `7.746504300041124 s`.
- WBPP black-box reference elapsed: `1092.541 s`.
- Speedup vs WBPP reference: `141.03664797477745x`.
- Active/rejected frames: `193 / 7`.
- Reference: `F000225`.
- Reference source: `frame_quality`.
- Master SHA256:
  `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`.
- Gate575/Gate576 output parity: all six integration FITS artifacts matched
  SHA256 exactly.
- Compare shape match: `true`.
- Coverage190 fraction after border crop: `0.905523489118409`.
- RMS diff vs WBPP: `0.005340835487175878`.
- p99 abs diff vs WBPP: `0.002133606873685496`.
- Acceptance audit: `passed`, `109` checks, `0` failed.
- New benchmark-required check:
  `contract_pipeline_contract_check:resident_calibrated_light_dq_contract`
  passed.
- Pixel pipeline contract: `passed`, `25` checks, `0` failed.
- Pixel checks passed:
  - `integration_dq_map_pixels_match_summary`;
  - `integration_rejection_sample_counts_match_maps`;
  - `integration_sample_accounting_closure`.
- StackEngine contract: `passed`, default-promotion ready.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- This gate did not change CUDA kernels or image math.

## Known Limitations

- This is benchmark-contract hardening, not a runtime optimization.
- It does not add new DQ detection modes or change calibration, registration,
  warp, LN, rejection, integration, frame admission, or output pixels.
- The next substantive targets remain resident registration/warp throughput,
  deeper default StackEngine runtime completeness, or stronger calibrated/GPU
  reference selection evidence.

## Next Step

Prefer a substantive Gate580 that improves or hardens resident registration/
warp execution on the 200-light default path, because current default
StackEngine/DQ contracts are green and the real benchmark is bitwise stable.

## Clean-Room Compliance

- Used GLASS code, GLASS-generated artifacts, user-owned 200-light outputs, and
  user-generated WBPP black-box timing/reference outputs.
- Did not read, copy, summarize, or rework external proprietary source code.
- Did not modify input image directories.
- Did not change public claims beyond measured GLASS artifacts.
