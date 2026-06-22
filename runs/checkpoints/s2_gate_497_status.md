# S2-Gate497 Status: Resident minimal master-only output transfer

## Gate

- Gate: S2-Gate497
- Date: 2026-06-23
- Purpose: continue Phase 2 runtime work by reducing unused resident CUDA minimal-output transfer, then validate the real 200-light speed/result path.
- Status: green

## Completed work

- Added `download_mode=master_only` to native resident stack and fused matrix integration wrappers.
- Changed `--resident-output-maps minimal` from `master_weight` to `master_only`.
- Minimal mode now downloads and writes only the final master image.
- Device-side weight-map computation remains unchanged because the existing CUDA kernels still use it internally.
- Audit/science modes still use full diagnostic downloads and remain the DQ/rejection evidence paths.
- Added `weight_map_downloaded` to native timing and resident integration dispatch artifacts.
- Made resident output-map policy record `download_mode`, `weight_map_downloaded`, and `diagnostic_maps_downloaded`.
- Fixed resident result contract false negatives for minimal policy:
  - skipped DQ maps no longer require `dq_summary.valid`;
  - skipped DQ maps pass pixel verify as `skipped_by_output_policy`;
  - skipped geometric coverage no longer fails `geometric_frame_count_matches_active`.
- Updated `docs/algorithm_sources.md` and `docs/phase2_algorithm_hardening.md`.

## Commands run

Native rebuild:

```powershell
$cmd = 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 && .venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native'
cmd.exe /c $cmd
```

Focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch tests/test_benchmarks.py::test_bench_resident_fused_matrix_dispatch_outputs_agreement
.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_result_contract.py::test_resident_result_contract_accepts_minimal_master_only_policy_without_dq_maps tests/test_resident_result_contract.py::test_resident_result_contract_passes_with_pixel_verify
```

Full tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Real 200-light run:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
```

Validation commands:

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\compare\master_only_vs_wbpp_scaled_coverage190.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\runs\stack_audit_full_maps\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\compare\master_only_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\speedup\master_only_vs_wbpp_speedup.json --markdown C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\speedup\master_only_vs_wbpp_speedup.md --min-speedup 100
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\compare\master_only_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\acceptance\master_only_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\acceptance\master_only_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 100 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\glass.exe resident-result-contract --run C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only --out C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only\resident_result_contract.json --markdown C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only\resident_result_contract.md --pixel-verify --pixel-verify-tile-size 2048 --fail-on-failed
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only --out C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\reports\master_only_report.html
```

## Test results

- Focused resident/fused/benchmark tests: `3 passed in 0.92s`
- CUDA resident stack subset: `47 passed in 0.54s`
- Focused resident result contract tests: `2 passed in 0.18s`
- Full pytest: `1142 passed in 41.80s`
- `git diff --check`: passed; only Windows line-ending warnings were reported.

## CUDA status

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Driver: 596.21
- Total VRAM: 97887 MiB
- Free VRAM before real run: 95775 MiB
- CUDA toolkit used for local native rebuild: 13.2

## Real 200-light A/B evidence

Dataset:

- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Manifest: `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
- Frames: 200 light, 20 bias, 20 dark, 20 flat
- Reference frame: `LIGHT_H_0136`
- WBPP black-box result: `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- WBPP elapsed time: 1092.541 s

GLASS master-only minimal run:

- Run root: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only`
- Total elapsed: 7.6039500999613665 s
- Dispatch: `download_mode=master_only`
- `weight_map_downloaded`: false
- `diagnostic_maps_downloaded`: false
- Output policy available/written maps: `master`
- Public integration files: `resident_master_H.fits` only
- Active frames: 193 / 200
- Speedup vs WBPP: 143.6807166850754x

Numerical validation:

- GLASS Gate497 vs Gate496 minimal master: RMS 0.0, p99 0.0, max 0.0
- Compared finite pixels for Gate497 vs Gate496: 61,651,200
- GLASS vs WBPP scaled coverage-190 RMS: 0.0017794216505176163
- GLASS vs WBPP scaled coverage-190 p99 absolute difference: 0.00042621337808668863
- Coverage fraction: 0.960532609259836
- Compared pixels: 59,217,988

Contract and acceptance:

- Resident result contract: passed with pixel verification
- Acceptance audit: passed
- HTML report generated

## Artifacts

- Run root: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only`
- Compare JSON: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\compare\master_only_vs_wbpp_scaled_coverage190.json`
- Compare HTML: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\compare\master_only_vs_wbpp_scaled_coverage190.html`
- Speedup JSON: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\speedup\master_only_vs_wbpp_speedup.json`
- Speedup Markdown: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\speedup\master_only_vs_wbpp_speedup.md`
- Acceptance JSON: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\acceptance\master_only_acceptance_audit.json`
- Acceptance Markdown: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\acceptance\master_only_acceptance_audit.md`
- Resident result contract: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\runs\stack_minimal_master_only\resident_result_contract.json`
- HTML report: `C:\glass_runs\phase2_s2_gate497_master_only_minimal_ab_real\reports\master_only_report.html`

## C: drive status

- C: remained healthy after this gate.
- Free space after validation: approximately 284.18 GiB.
- No input images, plans, WBPP black-box outputs, or preserved shared master caches were deleted.

## Known limitations

- `master_only` is intentionally a speed/minimal output mode. It does not emit weight, coverage, low/high rejection, DQ, or geometric coverage maps.
- Audit/science modes must be used for full diagnostic-map evidence and publication-quality DQ/rejection contracts.
- CUDA kernels still allocate and compute the device weight map internally. This gate removes only unused host allocation/download in minimal mode.
- The native module was rebuilt locally with CUDA Toolkit 13.2 for this workstation; distribution packaging remains separate work.

## Next step

- Continue Phase 2 mainline with resident registration/orchestration performance:
  - add or use fine timing around catalog batching, descriptor generation, transform scoring, and warp dispatch;
  - target remaining host/device orchestration and per-frame scheduling overhead;
  - preserve the audit/full-map evidence path while using `minimal/master_only` for top-speed real benchmarks.

## Clean-room compliance

- Compliant.
- This gate used GLASS code, GLASS artifacts, real user-provided image data, and user-generated PixInsight/WBPP black-box timing/output metadata only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or reworked.
- Input image directories were treated as read-only.
