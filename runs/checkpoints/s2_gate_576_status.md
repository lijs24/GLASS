# S2-Gate 576 Status: Default LN-On 200-Light A/B Validation

## Gate

- Gate: S2-Gate 576
- Objective: return to the substantive Phase 2 mainline by validating the current default resident CUDA, LN-on, winsorized, audit-map 200-light path against the stored WBPP black-box output and GLASS contracts.
- Status: green
- Clean-room status: compliant. This gate uses GLASS artifacts and user-generated WBPP black-box timing/output metadata only. It does not inspect external implementation source or modify input image directories.

## Completed

- Reused the current HEAD safe default 200-light run from Gate575:
  `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass`.
- Generated a coverage-masked compare against the WBPP FastIntegration black-box master.
- Generated a resident CUDA StackEngine contract audit and required it to be default-ready for the resident CUDA surface.
- Ran acceptance audit with current LN-on default thresholds, binding both pipeline and StackEngine contracts.
- Generated a speedup summary for the current default LN-on path.
- Ran an explicit `F000162` center-reference probe to test whether coverage190 was mainly a reference-center problem. It was not; coverage190 remained essentially unchanged, so no reference-selection code was changed.
- Updated `docs/phase2_algorithm_hardening.md` with the validation result.

## Commands Run

- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 7.975543199805543 --reference-time-seconds 1092.541 --glass-label "GLASS Gate575 safe default" --reference-label "WBPP black-box fastIntegration" --glass-scale=8.764434957115609e-06 --glass-offset=0.0006274500691899127 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate576_reference_selection_ab\explicit_center_candidate_F000162 --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache --reference-frame-id F000162`
- `.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate576_reference_selection_ab\explicit_center_candidate_F000162\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate576_reference_selection_ab\explicit_center_candidate_F000162\compare_vs_wbpp_fastintegration_scaled_coverage190.json --glass-time-seconds 7.5 --reference-time-seconds 1092.541 --glass-label "GLASS explicit F000162 probe" --reference-label "WBPP black-box fastIntegration" --glass-scale=8.764434957115609e-06 --glass-offset=0.0006274500691899127 --ignore-border-px 128 --glass-coverage-map C:\glass_runs\phase2_s2_gate576_reference_selection_ab\explicit_center_candidate_F000162\integration\resident_coverage_map_H.fits --min-coverage 190`
- `.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass --out C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\stack_engine_contract.md --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\resident_calibration_contract.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\resident_result_contract.json --require-default-ready`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\manifest.json --glass-run C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\acceptance_audit_ln_on_default.json --markdown C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\acceptance_audit_ln_on_default.md --min-active-frames 190 --min-speedup 20.0 --min-coverage-fraction 0.90 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --pipeline-contract-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\stack_engine_contract.json`
- `.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out runs\benchmarks\m38_wbpp_speedup_summary_gate576_ln_on_default.json --markdown runs\benchmarks\m38_wbpp_speedup_summary_gate576_ln_on_default.md --min-speedup 20.0`
- `.venv\Scripts\python.exe -m pytest -q`: `1238 passed in 50.92s`.

## Real 200-Light Result

- GLASS run: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass`
- WBPP black-box elapsed: `1092.541 s`
- GLASS run timing total: `7.975543199805543 s`
- Speedup vs WBPP: `136.9864061455573x`
- Active/rejected frames: `193 / 7`
- Rejected frames: `F000160`, `F000213`, `F000214`, `F000215`, `F000216`, `F000217`, `F000218`
- Reference scout backend: `cpu`
- Selected reference: `F000225`
- Master SHA256: `3c5f942f3be7fe629c6be55c1e2d14a94b8f23128c057384f03df8f09a38333d`

## Compare Result

- Compare JSON: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Compare HTML: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- Shape match: `true`
- Min coverage: `190`
- Ignore border: `128 px`
- Coverage190 compared pixels: `52171830`
- Coverage190 fraction after border crop: `0.905523489118409`
- RMS diff: `0.005340835487175878`
- p99 abs diff: `0.002133606873685496`

## Contracts

- Acceptance audit: `passed`
- Acceptance checks: `16`, failed `0`
- Acceptance audit JSON: `C:\glass_runs\phase2_s2_gate575_cuda_calibrated_reference_health\default_safe_auto_should_pass\acceptance_audit_ln_on_default.json`
- StackEngine contract: `passed`
- StackEngine checks: `7`, failed `0`
- Pipeline contract: `passed`
- LN contract: `passed`

## Timing Highlights

- light read/upload/calibrate: `2.4911861000582576 s`
- resident registration/warp: `0.26176169991958886 s`
- resident local normalization: `1.2233816999942064 s`
- resident integration: `0.35036330006551 s`
- output write: `0.36934209999162704 s`

## CUDA

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21

## Known Limitations

- The old LN-off parity contract used a stricter `coverage_fraction >= 0.95` at `min_coverage=190`. The current LN-on default path has lower post-rejection coverage at the same threshold, while still passing RMS and p99 numerical bounds.
- The explicit `F000162` center-reference probe did not materially improve coverage190, so this gate does not change reference-selection code.
- This gate validates current behavior and records the LN-on acceptance evidence; it does not introduce a new algorithmic optimization.
- A future substantive gate should make the benchmark contract explicitly model LN-on post-rejection coverage semantics instead of relying on the older LN-off threshold.

## Next Step

Continue with Phase 2 core engineering: DQ/mask pipeline completeness, StackEngine default surfaces, and any real-data contract update that encodes LN-on coverage semantics without weakening numerical correctness.
