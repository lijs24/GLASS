# S2-Gate 485 Status: Resident CUDA Master Mean Builder

## Gate

- Gate: S2-Gate 485
- Status: passed
- Scope: move resident master-cache mean construction from the Gate484 CPU
  full-frame StackEngine fast path onto existing GLASS resident CUDA primitives
  while preserving StackEngine-compatible DQ provenance, result contracts,
  CPU-only fallback, and the real 200-light A/B evidence chain.

## Completed

- Added a resident CUDA master mean builder in `src/glass/engine/resident_cuda.py`.
- The CUDA path reads calibration frames through the fast/native FITS path,
  uploads them one at a time into a short-lived `ResidentCalibratedStack`, and
  reduces them with `ResidentCalibratedStack.integrate_mean`.
- The CUDA path records:
  - `tile_stack_mode=stack_engine_cuda_mean`;
  - `execution_path=resident_cuda_mean_no_rejection`;
  - per-group read/upload/integrate timing;
  - native FITS backend counts;
  - resident stack byte requirements;
  - StackEngine-compatible DQ provenance and result contracts.
- CUDA unavailable, device unavailable, or unsupported FITS inputs fall back to
  the Gate484 CPUStackEngine full-frame path and record the fallback reason.
- The cache builder fingerprint was bumped to
  `resident_stack_engine_resident_cuda_mean_master_cache_v1`.
- Updated `docs/algorithm_sources.md` and
  `docs/phase2_algorithm_hardening.md`.

## Commands Run

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_master_stack_engine.py tests\test_stack_engine.py tests\test_stack_engine_result_contract.py
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_master_stack_engine.py
```

Real 200-light cold/warm A/B:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\cold_cuda_master_mean_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\shared_master_cache
```

Comparison and acceptance:

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\cold_cuda_master_mean_cache\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_cold_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_cold_diagnostics
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_gate484_warm_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_gate484_diagnostics
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --glass-scale 0.000008764434957115609 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.md --min-speedup 20
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache\manifest.json --glass-run C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\acceptance\warm_threshold_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\acceptance\warm_threshold_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache --out C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\reports\warm_report.html --compare-json C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\acceptance\warm_threshold_acceptance_audit.json
```

Full validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,compute_cap --format=csv,noheader
```

## Test Results

- Focused StackEngine/resident tests: `23 passed in 0.31s`.
- Ruff: `All checks passed!`.
- Full pytest: `1126 passed in 41.32s`.

## Real 200-Light Results

- Dataset: M38 H-alpha benchmark, `200` lights, `20` bias, `20` dark, `20`
  flats, user-generated WBPP black-box reference output.
- Output root:
  `C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real`.
- Cold CUDA-master total: `27.771337599959224 s`.
- Cold `master_build_or_load`: `7.568977500020992 s`.
- Warm CUDA-master total: `20.304512000002433 s`.
- Warm `master_build_or_load`: `0.30791140004293993 s`.
- Gate484 cold total comparison: `35.3481062000501 s` ->
  `27.771337599959224 s` (`1.2728269235437186x`).
- Gate484 cold master-build comparison: `15.344373799976893 s` ->
  `7.568977500020992 s` (`2.0272716889347784x`).
- Gate481 helper cold master-build comparison: `10.911685600003693 s` ->
  `7.568977500020992 s` (`1.4416327172294316x`).
- Warm-vs-cold master difference: RMS/p99/max all `0.0`.
- Warm-vs-Gate484 warm master difference: RMS/p99/max all `0.0`.
- Warm-vs-WBPP scaled coverage>=190 compare:
  - RMS: `0.0017794216505176163`.
  - p99 absolute difference: `0.00042621337808668863`.
  - max absolute difference: `0.5499989986419678`.
- Warm GLASS vs WBPP speedup: `53.80779405089219x`.
- Threshold acceptance audit: `passed`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total VRAM: `97886-97887 MiB`.
- Sampled VRAM during final check: `825 MiB` used, `95775 MiB` free.

## Disk / Cleanup Note

- C: free after the gate: about `32.3 GiB`.
- Keep current Gate485 artifacts and
  `C:\gpwbpp_runs\final_m38_h_200` for the active 200-light evidence chain.
- If C: fills again, old `C:\glass_runs\phase2_s2_gate_*` directories are the
  preferred cleanup candidates. The source tree and user-owned raw image
  directories were not modified.

## Artifacts

- Summary:
  `C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\gate485_real_ab_summary.json`.
- Warm report:
  `C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\reports\warm_report.html`.
- Acceptance:
  `C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\acceptance\warm_threshold_acceptance_audit.json`.
- Speedup:
  `C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json`.
- Compare:
  `C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json`.

## Known Limitations

- This gate covers mean/no-rejection resident master-cache construction only.
- Robust resident master rejection is still deferred.
- The path still reads calibration frames on the host before upload. The next
  likely gain is read/H2D overlap or raw-u16 GPU decode for master frames.
- CPU-only systems fall back to the Gate484 CPUStackEngine full-frame path.
- This gate does not change registration, warp, local normalization,
  winsorized light rejection, or CUDA integration formulas.

## Next Step

- Add overlap/raw-u16 decode for resident master-cache calibration-frame reads,
  or start the next major mainline target: DQ/mask pipeline contract tightening
  across calibration -> registration -> integration.
- Keep running the real 200-light A/B after each performance-affecting change.

## Clean-Room Compliance

- This gate used GLASS-owned source code, existing GLASS CUDA primitives,
  GLASS-generated artifacts, user-owned M38 FITS inputs, and user-generated
  WBPP black-box outputs/timing only.
- It did not inspect or copy official PixInsight/WBPP/PJSR source code.
- It did not modify input image directories.
- The CUDA builder changes execution strategy only; it does not import external
  implementation behavior or proprietary formulas.
