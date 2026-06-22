# S2-Gate 491 Status: Resident Source-DQ Degenerate Active-Frame Guard

## Gate

- Gate: S2-Gate 491
- Scope: resident source-DQ execution contract, degenerate active-frame guard, and immediate return to real 200-light A/B validation.
- Status: green

## Completed

- Added resident source-DQ execution validation to `glass pipeline-contract`.
- Surfaced resident source-DQ execution state in the HTML pipeline-contract report section.
- Added `active_frame_count_not_degenerate` to the resident result contract so a multi-frame resident integration cannot silently pass after collapsing to one active frame.
- Added regression coverage for passing/failing source-DQ execution contracts and degenerate resident active-frame counts.
- Verified an existing diagnostic `cosmetic_cuda` source-DQ run now fails the new guard because it collapsed to `1 / 200` active frames.
- Reran the default resident CUDA 200-light A/B path after the contract fix.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py::test_pipeline_contract_passes_resident_result_contract tests\test_pipeline_contract.py::test_pipeline_contract_fails_degenerate_resident_active_frame_count tests\test_pipeline_contract.py::test_pipeline_contract_fails_resident_result_contract tests\test_pipeline_contract.py::test_pipeline_contract_passes_resident_source_dq_execution_contract tests\test_pipeline_contract.py::test_pipeline_contract_fails_resident_source_dq_execution_contract
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_result_contract.py tests\test_pipeline_contract.py src\glass\report\pipeline_contract.py src\glass\report\html_report.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_contract.py tests\test_resident_source_dq.py
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\runs\default_runtime_stack --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\gate490_pipeline_contract_with_degenerate_guard.json --markdown C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\gate490_pipeline_contract_with_degenerate_guard.md --pixel-verify
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\cosmetic_cuda_source_dq --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\cosmetic_cuda_pipeline_contract_with_degenerate_guard.json --markdown C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\cosmetic_cuda_pipeline_contract_with_degenerate_guard.md --pixel-verify
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_stack_engine_contract.md --expected-integration-engine cuda_resident_stack --require-default-ready
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\runs\default_runtime_stack\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\compare\ab_current_vs_gate490_master.html --glass-label GLASS-Gate491 --reference-label GLASS-Gate490
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.html --glass-label GLASS-Gate491 --reference-label WBPP-fastIntegration --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.md --min-speedup 2.0
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current\manifest.json --glass-run C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\acceptance\ab_current_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\acceptance\ab_current_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --pipeline-contract-json C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_stack_engine_contract.json
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\reports\ab_current_report.html --compare-json C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\acceptance\ab_current_acceptance_audit.json --pipeline-contract C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_pipeline_contract.json --stack-engine-contract C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\contracts\ab_current_stack_engine_contract.json
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused pipeline/source-DQ tests: `43 passed in 1.38s`.
- Focused degenerate guard tests: `5 passed in 0.23s`.
- Ruff: all edited Python files passed.
- Full pytest: `1131 passed in 41.45s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- VRAM: `97887 MiB` total, `95775 MiB` free when sampled.

## Real 200-Light A/B Result

- Run: `C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current`.
- GLASS elapsed: `19.793096599983983 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup: `55.19808355812724x`.
- Active frames: `193 / 200`.
- Current vs Gate490 master: RMS/p99/max all `0.0`.
- Current vs WBPP coverage >= 190:
  - RMS: `0.0017794216505176163`.
  - P99 absolute diff: `0.00042621337808668863`.
  - Coverage fraction: `0.960532609259836`.
- Acceptance audit: passed.

## Diagnostic Source-DQ Finding

- Diagnostic run: `C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\cosmetic_cuda_source_dq`.
- `resident_source_dq_execution` passed its streaming/invalid-sample execution contract.
- The run collapsed to `1 / 200` active frames after registration because light-frame `cosmetic_cuda` source-DQ was too aggressive for stars.
- New resident result contract correctly fails this run on `active_frame_count_not_degenerate`.

## Known Limitations

- `cosmetic_cuda` source-DQ for light frames remains diagnostic/opt-in; it needs star-aware masking or a more conservative detector before promotion.
- Resident winsorized sigma default remains the documented fast mean/std approximation, not the hardened CPU-parity prototype.
- The 200-light result uses existing user-generated WBPP black-box timing/output artifacts; WBPP was not rerun in this gate.

## Next Step

- Return to Phase 2 substance: make DQ/source-mask application star-aware or defer light-frame cosmetic source-DQ until after registration, then repeat a real A/B only if it can keep active-frame counts and compare metrics green.

## Clean-Room Compliance

- Compliant. This gate used GLASS code/artifacts, user-owned image data, and user-generated WBPP black-box timing/output artifacts only.
- No official PixInsight/WBPP/PJSR implementation source was read, summarized, copied, or modified.
- Input image directories were treated as read-only.
