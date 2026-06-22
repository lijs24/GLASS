# S2-Gate 486 Status: Resident Master Raw-u16 GPU Decode

## Gate

- Gate: S2-Gate 486
- Status: passed
- Scope: reduce resident master-cache cold-build read/decode/upload cost by
  reusing existing GLASS raw-u16 GPU decode primitives for eligible calibration
  FITS frames, while preserving StackEngine-compatible DQ provenance, result
  contracts, CPU fallback, and the real 200-light A/B evidence chain.

## Completed

- Extended the Gate485 resident CUDA master mean builder to prefer raw-u16 GPU
  decode for eligible calibration master groups.
- Eligibility is limited to simple FITS frames with:
  - `BITPIX=16`;
  - `BSCALE=1`;
  - `BZERO=32768`;
  - no `BLANK`.
- Raw frames are read as compact bytes with `read_simple_fits_u16be_raw_timed`,
  decoded/stored into a short-lived `ResidentCalibratedStack` via
  `calibrate_frames_fits_u16be_bzero_host_async_multistream_callback_release_timed`,
  then reduced with `integrate_mean`.
- Unsupported FITS inputs fall back to the Gate485 native-direct float32 upload
  path. CUDA-unavailable systems fall back to the Gate484 CPUStackEngine
  full-frame path.
- The cache builder fingerprint was bumped to
  `resident_stack_engine_resident_cuda_raw_u16_mean_master_cache_v1`.
- Added unit coverage for CPU fallback, CUDA native-direct dispatch, and raw-u16
  GPU decode dispatch.
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
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\cold_raw_u16_master_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
```

Comparison and acceptance:

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\cold_raw_u16_master_cache\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_cold_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_cold_diagnostics
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate485_resident_cuda_master_mean_ab_real\runs\warm_cuda_master_mean_cache\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_gate485_warm_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_gate485_diagnostics
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --glass-scale 0.000008764434957115609 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.md --min-speedup 20
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache\manifest.json --glass-run C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\acceptance\warm_threshold_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\acceptance\warm_threshold_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\runs\warm_raw_u16_master_cache --out C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\reports\warm_report.html --compare-json C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\acceptance\warm_threshold_acceptance_audit.json
```

Full validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,compute_cap --format=csv,noheader
```

## Test Results

- Focused StackEngine/resident tests: `24 passed in 0.34s`.
- Ruff: `All checks passed!`.
- Full pytest: `1127 passed in 41.22s`.

## Real 200-Light Results

- Dataset: M38 H-alpha benchmark, `200` lights, `20` bias, `20` dark, `20`
  flats, user-generated WBPP black-box reference output.
- Output root:
  `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real`.
- Cold raw-u16 total: `26.353526399994735 s`.
- Cold `master_build_or_load`: `6.047361700038891 s`.
- Warm raw-u16 total: `20.477806099923328 s`.
- Warm `master_build_or_load`: `0.3097565000061877 s`.
- Gate485 cold master-build comparison: `7.568977500020992 s` ->
  `6.047361700038891 s` (`1.2516164693724727x`).
- Gate484 cold master-build comparison: `15.344373799976893 s` ->
  `6.047361700038891 s` (`2.5373666337633174x`).
- Gate481 helper cold master-build comparison: `10.911685600003693 s` ->
  `6.047361700038891 s` (`1.8043712516705457x`).
- Raw-u16 master-cache groups avoided float32 host payloads:
  - bias: `1479628800` bytes;
  - dark: `2712652800` bytes;
  - flat: `986419200` bytes.
- Warm-vs-cold master difference: RMS/p99/max all `0.0`.
- Warm-vs-Gate485 warm master difference: RMS/p99/max all `0.0`.
- Warm-vs-WBPP scaled coverage>=190 compare:
  - RMS: `0.0017794216505176163`.
  - p99 absolute difference: `0.00042621337808668863`.
  - max absolute difference: `0.5499989986419678`.
- Warm GLASS vs WBPP speedup: `53.35244384426956x`.
- Threshold acceptance audit: `passed`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total VRAM: `97886-97887 MiB`.
- Sampled VRAM during final check: `825 MiB` used, `95775 MiB` free.

## Disk / Cleanup Note

- C: free after the gate: about `29.75 GiB`.
- Keep current Gate486 artifacts and
  `C:\gpwbpp_runs\final_m38_h_200` for the active 200-light evidence chain.
- If C: fills again, old `C:\glass_runs\phase2_s2_gate_*` directories are the
  preferred cleanup candidates. The source tree and user-owned raw image
  directories were not modified.

## Artifacts

- Summary:
  `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\gate486_real_ab_summary.json`.
- Warm report:
  `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\reports\warm_report.html`.
- Acceptance:
  `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\acceptance\warm_threshold_acceptance_audit.json`.
- Speedup:
  `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json`.
- Compare:
  `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json`.

## Known Limitations

- Raw-u16 GPU decode applies only to simple unsigned-style FITS frames with
  `BITPIX=16`, `BSCALE=1`, `BZERO=32768`, and no `BLANK`.
- Robust resident master rejection is still deferred.
- The remaining cold-cache cost is close to the calibration-frame FITS read
  floor; broader end-to-end gains now likely require light read/upload overlap,
  registration orchestration reductions, or DQ/mask pipeline work.
- CPU-only systems fall back to the Gate484 CPUStackEngine full-frame path.
- This gate does not change registration, warp, local normalization,
  winsorized light rejection, or CUDA integration formulas.

## Next Step

- Return to Phase 2 mainline DQ/mask pipeline contract tightening, or attack
  the larger resident light read/upload/calibration and registration
  orchestration costs identified in the 200-light timing profile.
- Keep running the real 200-light A/B after each performance-affecting change.

## Clean-Room Compliance

- This gate used GLASS-owned source code, existing GLASS CUDA primitives,
  GLASS-generated artifacts, user-owned M38 FITS inputs, and user-generated
  WBPP black-box outputs/timing only.
- It did not inspect or copy official PixInsight/WBPP/PJSR source code.
- It did not modify input image directories.
- The raw-u16 builder changes execution strategy only; it does not import
  external implementation behavior or proprietary formulas.
