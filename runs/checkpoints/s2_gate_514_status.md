# S2-Gate 514 Status: Current Default 200-Light A/B Audit

Gate: S2-Gate 514

Status: passed

Date: 2026-06-23 local

## Objective

Return from the Gate513 Lanczos3 semantic fix to the substantive Phase 2 target:
run the current GLASS resident CUDA default path on the real M38 H-alpha
200-light benchmark and compare it against the existing user-generated WBPP
black-box output.

## Completed

- Ran a cold-start GLASS resident CUDA audit-map stack without passing a shared
  `--resident-master-cache-dir`.
- Generated master, weight, coverage, DQ, low-rejection, and high-rejection
  maps.
- Compared the GLASS master against the WBPP black-box FastIntegration master
  with the established scale/offset and coverage>=190 comparison region.
- Ran resident calibration, resident result, pipeline, StackEngine, and
  acceptance contracts.
- Updated `benchmarks/phase2_m38_h_200_audit_maps_contract.json` so required
  command tokens match the current default A/B route instead of the old
  Gate460 hand-tuned parity route.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Real 200-Light Dataset

- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Manifest: `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
- Frames: 200 light, 20 bias, 20 dark, 20 flat
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- WBPP reference master:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`
- GLASS run root:
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127`

## Commands

- `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --out C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit`
- `glass compare --glass C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\s2_gate_514_compare_vs_wbpp.html --glass-time-seconds 21.205785 --reference-time-seconds 1092.541 --glass-label GLASS-S2G514-current-cold-audit --reference-label WBPP-blackbox --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_coverage_map_H.fits --min-coverage 190`
- `glass resident-calibration-contract --run C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit --out C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\resident_calibration_contract_s2_gate_514.json --fail-on-failed`
- `glass resident-result-contract --run C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit --out C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\resident_result_contract_s2_gate_514.json --pixel-verify --fail-on-failed`
- `glass pipeline-contract --run C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit --out C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\pipeline_contract_s2_gate_514.json --pixel-verify --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\resident_calibration_contract_s2_gate_514.json`
- `glass stack-engine-contract --run C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit --out C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\stack_engine_contract_s2_gate_514.json --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\resident_calibration_contract_s2_gate_514.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\resident_result_contract_s2_gate_514.json`
- `glass acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\s2_gate_514_compare_vs_wbpp.json --out C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\phase2_contract_acceptance_audit_s2_gate_514.json --markdown C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\phase2_contract_acceptance_audit_s2_gate_514.md --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\pipeline_contract_s2_gate_514.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\stack_engine_contract_s2_gate_514.json`
- `python -m pytest -q tests/test_acceptance_audit.py tests/test_benchmarks.py`
- `python -m pytest -q`
- `glass doctor`

## Test Results

- Benchmark/acceptance focused tests: `65 passed in 5.12 s`.
- Full pytest: `1156 passed in 41.51 s`.
- `glass doctor`: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## A/B Results

- GLASS internal elapsed: `20.824213800020516 s`.
- GLASS conservative shell elapsed: `21.205785 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup vs WBPP:
  - internal timing: `52.46493387418658x`;
  - shell timing: `51.52089394474197x`.
- Integrated frames: `193 / 200`.
- Zero-weight quality-rejected frames: `7`.
- Shape match: `true`.
- Coverage fraction: `0.960532609259836`.
- Coverage max/median: `193` / `192`.
- RMS diff: `0.0017794216505176163`.
- P99 absolute diff: `0.00042621337808668863`.

## Contract Results

- Initial acceptance attempt failed only because the audit-map benchmark
  contract still required obsolete Gate460 command tokens.
- After refreshing the contract to the current default A/B route:
  - resident calibration contract: passed;
  - resident result contract: passed with pixel verification;
  - pipeline contract: passed with pixel verification;
  - StackEngine contract: passed and default-promotion ready;
  - acceptance audit: passed.

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_514_real_200_ab_summary.json`
- Compare:
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\s2_gate_514_compare_vs_wbpp.html`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\phase2_contract_acceptance_audit_s2_gate_514.json`
- Acceptance markdown:
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\phase2_contract_acceptance_audit_s2_gate_514.md`
- Output maps:
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_master_H.fits`
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_weight_map_H.fits`
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_coverage_map_H.fits`
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_dq_map_H.fits`
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_low_rejection_map_H.fits`
  `C:\glass_runs\phase2_s2_gate514_real_200_ab\runs_20260623_071127\glass_current_cold_audit\integration\resident_high_rejection_map_H.fits`

## Known Limitations

- WBPP was not rerun in this gate; it uses the existing user-generated
  black-box timing/output from the same staged 200-light dataset.
- Local normalization remains off for this benchmark route.
- The resident CUDA winsorized-sigma implementation remains the documented
  GLASS approximation, not a claim of exact PixInsight algorithm identity.
- Explicit Lanczos3+winsorized `fused_matrix` remains unpromoted after Gate513.

## Next Step

Return to substantive performance work: reduce the remaining I/O/upload/
calibration overlap cost and resident registration/warp orchestration cost on
the real 200-light route, while keeping this A/B contract green.

## Clean-Room Compliance

Compliant. This gate used GLASS code, GLASS artifacts, the user-staged real
M38 H-alpha data, and user-generated WBPP black-box timing/output artifacts.
No official PixInsight/WBPP/PJSR implementation source was read, copied,
summarized, or modified. Original image directories remained read-only.
