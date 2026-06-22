# S2-Gate 492 Status

## Gate

- Gate: S2-Gate 492
- Scope: registration-safe ordering for opt-in resident `cosmetic_cuda` source-DQ, plus immediate return to real 200-light A/B.
- Status: green

## Completed

- Checked C: usage before the run. C: had about `291 GB` free; the repository was about `2.4 GB`, while generated `C:\glass_runs` artifacts were about `231 GB`.
- Cleaned only reproducible in-repository build/cache folders (`build`, `.pytest_cache`, `.ruff_cache`, non-venv `__pycache__`), freeing about `55 MB`. Historical `C:\glass_runs` evidence was preserved.
- Changed resident `cosmetic_cuda` source-DQ ordering:
  - threshold statistics are still computed after calibration while frames are resident;
  - destructive threshold application is deferred when resident registration is enabled;
  - deferred rows are applied immediately before explicit warp, with a post-registration flush for reference, failed, excluded, and fused-matrix frames;
  - resident artifacts now report `resident_inline_source_dq_application_order`, deferred/applied/pending frame counts, and deferred apply timing.
- Added a CUDA resident regression for `similarity_cuda_triangle + cosmetic_cuda` proving registration remains valid and source-DQ rows are marked `post_registration_pre_warp`.
- Updated Phase 2 hardening and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_defers_inline_cosmetic_cuda_source_dq_until_after_registration
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_stack_engine_contract.md --expected-integration-engine cuda_resident_stack --require-default-ready
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate491_source_dq_contract_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\ab_current_vs_gate491_master.html --glass-label GLASS-Gate492 --reference-label GLASS-Gate491
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.html --glass-label GLASS-Gate492 --reference-label WBPP-fastIntegration --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.md --min-speedup 2.0
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current\manifest.json --glass-run C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\acceptance\ab_current_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\acceptance\ab_current_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --pipeline-contract-json C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_stack_engine_contract.json
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\cosmetic_cuda_source_dq_deferred --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache --resident-inline-source-dq cosmetic_cuda
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\cosmetic_cuda_source_dq_deferred --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\cosmetic_cuda_deferred_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\cosmetic_cuda_deferred_pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\reports\ab_current_report.html --compare-json C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\acceptance\ab_current_acceptance_audit.json --pipeline-contract C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_pipeline_contract.json --stack-engine-contract C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_stack_engine_contract.json
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\cosmetic_cuda_source_dq_deferred\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\cosmetic_cuda_deferred_vs_default.html --glass-label GLASS-cosmetic_cuda-deferred --reference-label GLASS-default
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_defers_inline_cosmetic_cuda_source_dq_until_after_registration tests\test_pipeline_contract.py::test_pipeline_contract_passes_resident_source_dq_execution_contract tests\test_pipeline_contract.py::test_pipeline_contract_passes_resident_result_contract
.\.venv\Scripts\python.exe -m pytest -q
```

Note: an early parallel attempt ran `speedup-summary` and `acceptance-audit` before the compare JSON existed; both were rerun successfully after compare completed.

## Test Results

- Focused source-DQ tests: `2 passed in 1.36s`.
- Focused post-refactor regression set: `4 passed in 0.71s`.
- Ruff: all edited Python files passed.
- Full pytest: `1132 passed in 43.27s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU observed in run artifacts: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Default run estimated resident peak: `49.608429938554764 GiB`.

## Real 200-Light Default A/B Result

- Run: `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current`.
- GLASS elapsed: `19.737044300010893 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup: `55.354843582095874x`.
- Active frames: `193 / 200`.
- Current vs Gate491 master: RMS/p99/max all `0.0`.
- Current vs WBPP coverage >= 190:
  - RMS: `0.0017794216505176163`.
  - P99 absolute diff: `0.00042621337808668863`.
  - Coverage fraction: `0.960532609259836`.
- Acceptance audit: passed.

## Real 200-Light Source-DQ Diagnostic

- Run: `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\cosmetic_cuda_source_dq_deferred`.
- Pipeline contract: passed with pixel verification.
- Registration status counts: `192 ok`, `1 reference`, `7 excluded`.
- Coverage active frames: `193 / 200`.
- Source-DQ summary:
  - rows: `200`;
  - passed: `true`;
  - input invalid samples before rejection: `96,803,833`;
  - application order: `post_registration_pre_warp`;
  - deferred frame count: `200`;
  - deferred applied frame count: `200`;
  - deferred pending frame count: `0`;
  - deferred apply time: about `0.03819 s`.

## Artifacts

- Default run report:
  `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\reports\ab_current_report.html`.
- Default pipeline contract:
  `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_pipeline_contract.json`.
- Default StackEngine contract:
  `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\ab_current_stack_engine_contract.json`.
- Default speedup summary:
  `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.json`.
- Default acceptance audit:
  `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\acceptance\ab_current_acceptance_audit.json`.
- Source-DQ diagnostic contract:
  `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\contracts\cosmetic_cuda_deferred_pipeline_contract.json`.
- Source-DQ vs default compare:
  `C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\compare\cosmetic_cuda_deferred_vs_default.json`.

## Known Limitations

- `cosmetic_cuda` remains opt-in and diagnostic for light frames. The execution order is now registration-safe, but the global threshold can still mask real star-core samples after registration; star-aware or structure-aware masking is the next scientific step.
- The default route intentionally keeps inline source-DQ off, so default pixels remain identical to Gate491.
- No WBPP rerun was performed in this gate; comparison uses the existing user-generated WBPP black-box timing/output artifact for the same dataset.

## Next Step

- Build a star-aware light-frame source-DQ detector or conservative source-DQ policy, then validate it on the 200-light dataset without losing active frames or degrading the WBPP compare metrics.
- Continue resident registration/warp performance work only after DQ policy remains numerically safe.

## Clean-Room Compliance

- Compliant. This gate used GLASS code/artifacts, GLASS-generated tests, user-owned M38 H-alpha data, and user-generated WBPP black-box timing/output artifacts.
- No official PixInsight/WBPP/PJSR implementation source was read, summarized, copied, or modified.
- Input image directories were treated as read-only.
