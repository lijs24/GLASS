# S2-Gate 493 Status

## Gate

- Gate: S2-Gate 493
- Scope: conservative high-fraction guard for opt-in resident `cosmetic_cuda`
  source-DQ, plus immediate real 200-light A/B validation.
- Status: green

## Completed

- Added native CUDA count-only threshold kernels and bindings:
  - `ResidentCalibratedStack.count_cosmetic_threshold_mask_frame`
  - `ResidentCalibratedStack.count_cosmetic_threshold_mask_frames`
- Added Python wrappers in `glass_cuda.py`.
- Added batch count-only preflight for opt-in `cosmetic_cuda` source-DQ rows.
- Frames above `--resident-inline-source-dq-max-invalid-fraction` are now
  recorded as `skipped_high_invalid_fraction` with `would_*` counts and are not
  modified in resident GPU memory.
- Tightened the default guard to `0.0001` (`0.01%` of frame samples) after a
  real 200-light diagnostic showed the earlier `0.002` default still changed
  the diagnostic master noticeably.
- Source-DQ summaries now include:
  - `input_would_invalid_samples_before_guard`
  - `input_guarded_invalid_samples_skipped`
- Resident artifacts now include:
  - `resident_inline_source_dq_max_invalid_fraction`
  - `resident_inline_source_dq_high_fraction_guard_enabled`
  - `resident_inline_source_dq_high_fraction_skipped_frame_count`
  - `resident_inline_source_dq_high_fraction_would_invalid_samples`
- Fixed deferred source-DQ accounting so
  `resident_inline_source_dq_deferred_applied_frame_count` counts only rows
  with `applied=true`.
- Updated Phase 2 hardening and algorithm-source documentation.
- Cleaned the superseded intermediate Gate493 real-output directory
  `C:\glass_runs\phase2_s2_gate493_source_dq_guard_ab_real`, freeing about
  `1.855 GB`. The final Gate493 evidence directory is preserved.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\cli.py src\glass_cuda.py
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_source_dq.py src\glass\engine\resident_cuda.py src\glass\cli.py src\glass_cuda.py tests\test_resident_source_dq.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py
.\.venv\Scripts\cmake.exe -S . -B build -DGLASS_BUILD_PYTHON_CUDA=ON -Dpybind11_DIR="$(.\.venv\Scripts\python.exe -m pybind11 --cmakedir)"
.\.venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native
Copy-Item .\src\Release\_glass_cuda_native.cp312-win_amd64.pyd .\src\_glass_cuda_native.cp312-win_amd64.pyd -Force
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py::test_apply_resident_inline_cosmetic_thresholds_batch_skips_high_invalid_fraction tests\test_cuda_resident_stack.py::test_resident_stack_count_cosmetic_threshold_mask_frame_does_not_modify_pixels tests\test_cuda_resident_stack.py::test_resident_stack_count_cosmetic_threshold_mask_frames_batches_without_modifying_pixels tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_skips_inline_cosmetic_cuda_high_fraction_guard tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_defers_inline_cosmetic_cuda_source_dq_until_after_registration
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe stack-engine-contract --run C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_stack_engine_contract.json --markdown C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_stack_engine_contract.md --expected-integration-engine cuda_resident_stack --require-default-ready
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate492_deferred_source_dq_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\ab_current_vs_gate492_master.html --glass-label GLASS-Gate493 --reference-label GLASS-Gate492
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.html --glass-label GLASS-Gate493 --reference-label WBPP-fastIntegration --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate493_guard001_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.md --min-speedup 2.0
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current\manifest.json --glass-run C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\acceptance\ab_current_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate493_guard001_ab_real\acceptance\ab_current_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01 --pipeline-contract-json C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_pipeline_contract.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_stack_engine_contract.json
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\reports\ab_current_report.html --compare-json C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\ab_current_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate493_guard001_ab_real\acceptance\ab_current_acceptance_audit.json --pipeline-contract C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_pipeline_contract.json --stack-engine-contract C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_stack_engine_contract.json
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\cosmetic_cuda_source_dq_guarded --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache --resident-inline-source-dq cosmetic_cuda
.\.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\cosmetic_cuda_source_dq_guarded --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\cosmetic_cuda_guarded_pipeline_contract.json --markdown C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\cosmetic_cuda_guarded_pipeline_contract.md --pixel-verify
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\cosmetic_cuda_source_dq_guarded\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\cosmetic_cuda_guarded_vs_default.html --glass-label GLASS-cosmetic_cuda-guarded --reference-label GLASS-default
```

## Test Results

- Focused CUDA/source-DQ/CLI tests: `6 passed in 0.98s`.
- Ruff: all edited Python/test files passed.
- Full pytest: `1136 passed in 41.07s`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU observed before real run:
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 0 %, 825 MiB, 97887 MiB`.
- CUDA Toolkit used by CMake build: `13.2.78`.

## Real 200-Light Default A/B Result

- Run: `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\default_runtime_stack_ab_current`.
- GLASS elapsed: `17.58118659997126 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup: `62.14262011198868x`.
- Active frames: `193 / 200`.
- Current vs Gate492 master: RMS/p99/max all `0.0`.
- Current vs WBPP coverage >= 190:
  - RMS: `0.0017794216505176163`.
  - P99 absolute diff: `0.00042621337808668863`.
  - Coverage fraction: `0.960532609259836`.
  - Max absolute diff: `0.5499989986419678`.
- Acceptance audit: passed.

## Real 200-Light Source-DQ Guard Diagnostic

- Run: `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\runs\cosmetic_cuda_source_dq_guarded`.
- Guard fraction: `0.0001`.
- Pipeline contract: passed with pixel verification.
- Source-DQ rows: `200`.
- `skipped_high_invalid_fraction`: `200`.
- Applied rows: `0`.
- Would-invalid samples before guard: `96,803,833`.
- Guarded invalid samples skipped: `96,803,833`.
- Applied invalid samples before rejection: `0`.
- Deferred frame count: `200`.
- Deferred applied frame count: `0`.
- Deferred pending frame count: `0`.
- Min/max would-invalid frame fraction:
  `0.0009139968078480225` / `0.015298420793107028`.
- Guarded diagnostic vs default master: RMS/p99/max all `0.0`.

## Artifacts

- Default run report:
  `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\reports\ab_current_report.html`.
- Default pipeline contract:
  `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_pipeline_contract.json`.
- Default StackEngine contract:
  `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\ab_current_stack_engine_contract.json`.
- Default speedup summary:
  `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\speedup\ab_current_vs_wbpp_speedup_with_compare.json`.
- Default acceptance audit:
  `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\acceptance\ab_current_acceptance_audit.json`.
- Source-DQ diagnostic contract:
  `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\contracts\cosmetic_cuda_guarded_pipeline_contract.json`.
- Source-DQ guarded vs default compare:
  `C:\glass_runs\phase2_s2_gate493_guard001_ab_real\compare\cosmetic_cuda_guarded_vs_default.json`.

## Disk

- C: free space after final run and intermediate cleanup: about `287.5 GB`.
- Final Gate493 evidence directory size: about `1.855 GB`.

## Known Limitations

- `cosmetic_cuda` remains opt-in and diagnostic for light frames. The new guard
  prevents large global-threshold masks from modifying resident pixels, but it
  does not yet distinguish true hot/cold defects from stars or nebulosity.
- The default production route keeps inline source-DQ off. This is intentional:
  default output remains pixel-identical to Gate492 while source-DQ research
  continues behind explicit flags.
- The WBPP comparison uses the existing user-generated WBPP black-box timing
  and output artifact for the same 200-light dataset; WBPP was not rerun in this
  gate.

## Next Step

- Implement a star-aware or structure-aware resident light-frame defect detector
  before promoting any light-frame cosmetic source-DQ application beyond
  diagnostic mode.
- Return to CUDA resident performance work after the DQ/mask path remains
  numerically safe under the 200-light A/B contract.

## Clean-Room Compliance

- Compliant. This gate used GLASS code/artifacts, GLASS-generated tests,
  user-owned M38 H-alpha data, and user-generated WBPP black-box timing/output
  artifacts.
- No official PixInsight/WBPP/PJSR implementation source was read, summarized,
  copied, or modified.
- Input image directories were treated as read-only.
