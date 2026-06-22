# S2-Gate 481 Status: Real 200-light shared master-cache A/B

## Scope

- Returned to the Phase 2 substantive path: real M38 H-alpha 200-light A/B validation.
- Fixed a compare CLI output-contract blocker found during the A/B run:
  - `glass compare --out foo.html` keeps writing `foo.html` plus `foo.json`.
  - `glass compare --out foo.json` now writes machine-readable JSON to `foo.json` and the sibling HTML report to `foo.html`.
- Validated the existing resident shared master-frame cache path on the real 200-light data set.

## Real Data

- Dataset: `M38_H_200light_20bias_20dark_20flat`.
- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`.
- Run root: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real`.
- WBPP black-box result: `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`.

## Commands

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\cold_shared_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\shared_master_cache

.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\warm_shared_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\shared_master_cache

.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\warm_shared_cache\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\cold_shared_cache\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\compare\warm_vs_cold_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\compare\warm_vs_cold_diagnostics

.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\warm_shared_cache\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --diagnostics-dir C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\compare\warm_vs_wbpp_scaled_coverage190_diagnostics --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\warm_shared_cache\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 20.172424699936528 --reference-time-seconds 1092.541

.\.venv\Scripts\python.exe benchmarks\summarize_wbpp_speedup.py --glass-run C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\warm_shared_cache --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.md --min-speedup 20.0

.\.venv\Scripts\python.exe -m pytest -q tests/test_compare_report.py
.\.venv\Scripts\python.exe -m pytest -q
```

## Results

- Cold shared-cache run: `30.655031500034966 s`.
- Warm shared-cache run: `20.172424699936528 s`.
- Warm/cold speedup from cache reuse: `1.5196503125443033x`.
- Master build/load timing:
  - Cold: `10.911685600003693 s`, cache misses `1`.
  - Warm: `0.30265010002767667 s`, cache hits `1`.
- Warm-cache gain: `10.482606800098438 s`.
- Warm vs cold master compare:
  - Shape match: `true`.
  - RMS diff: `0.0`.
  - p99 abs diff: `0.0`.
  - max abs diff: `0.0`.
- Warm GLASS vs WBPP black-box FastIntegration, coverage >= 190:
  - GLASS: `20.172424699936528 s`.
  - WBPP: `1092.541 s`.
  - Speedup: `54.160122853423644x`.
  - Shape match: `true`.
  - Compared pixels: `59217988`.
  - Coverage fraction: `0.960532609259836`.
  - RMS diff: `0.0017794216505176163`.
  - p99 abs diff: `0.00042621337808668863`.
  - p99.9 abs diff: `0.003845416396856427`.

## Test Results

- `tests/test_compare_report.py`: `7 passed in 0.37s`.
- Full suite: `1121 passed in 41.01s`.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- VRAM: `97887 MiB total`, `95775 MiB free` before/after the run sample.
- Resident FITS read mode: `native_u16_gpu`.
- Raw GPU decode: enabled.

## Artifacts

- Summary: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\gate481_real_ab_summary.json`.
- Cold run: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\cold_shared_cache`.
- Warm run: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\runs\warm_shared_cache`.
- Shared cache: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\shared_master_cache`.
- Warm/cold compare JSON: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\compare\warm_vs_cold_master.json`.
- Warm/WBPP compare JSON: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json`.
- Speedup summary: `C:\glass_runs\phase2_s2_gate481_master_cache_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json`.

## Disk Cleanup Note

- C: had about `50.32 GiB` free before this gate and about `47.84 GiB` free after.
- The repository itself is about `2.34 GiB`; the disk pressure comes from historic run artifacts under `C:\glass_runs` and `C:\gpwbpp_runs`, not from the source tree.
- No historic run artifacts were deleted in this gate.

## Known Limits

- This gate validates shared master-cache reuse and compare-output contract correctness; it does not yet eliminate the remaining resident registration/warp orchestration overhead.
- The current WBPP comparison uses the established scaled coverage>=190 compare protocol from the same benchmark family.

## Next Step

- Continue the resident performance path: reduce the remaining post-cache resident runtime by batching resident registration/warp orchestration and reducing host/device round trips.

## Clean-room

- Compliant. This gate used GLASS artifacts and user-generated WBPP black-box timing/output metadata only.
- No official PixInsight/WBPP/PJSR implementation source was read or summarized for this work.
