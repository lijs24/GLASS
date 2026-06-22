# S2-Gate 484 Status: StackEngine Full-Frame Finite-Only Master Mean Fast Path

## Gate

- Gate: S2-Gate 484
- Status: passed
- Scope: reduce the resident master-cache cold-build regression introduced by
  moving resident master construction under `CPUStackEngine`, while preserving
  StackEngine/DQ provenance and real 200-light numerical agreement.

## Completed

- Added a metadata-gated `CPUStackEngine` full-frame fast path for
  mean/weighted-mean requests when rejection and output maps are disabled.
- Kept the generic StackEngine path tile/out-of-core by default. The full-frame
  path requires `request.metadata["full_frame_fast_path"]`.
- Let resident master-cache FITS sources declare `mask_from_finite_only=True`,
  allowing the explicit fast path to derive validity from `np.isfinite` without
  issuing separate mask tile reads.
- Bumped the resident master cache builder fingerprint to
  `resident_stack_engine_full_frame_mean_master_cache_v1`.
- Recorded `execution_path=full_frame_mean_no_rejection` in StackEngine metrics
  and DQ provenance for resident master-cache bias/dark/flat products.
- Updated algorithm-source and Phase 2 hardening documentation.

## Commands Run

Focused validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_stack_engine.py tests\test_stack_engine_result_contract.py tests\test_resident_master_stack_engine.py
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\stack_engine.py src\glass\engine\resident_cuda.py tests\test_stack_engine.py tests\test_resident_master_stack_engine.py
```

Real 200-light cold/warm A/B:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\cold_finite_full_frame_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache --backend cuda --memory-mode resident --resident-runtime-preset throughput-v1 --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-integration-dispatch stack --resident-master-cache-dir C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\shared_master_cache
```

Comparison and acceptance:

```powershell
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\cold_finite_full_frame_cache\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_cold_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_cold_diagnostics
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate483_stackengine_fast_mean_ab_real\runs\warm_fast_mean_cache\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_gate483_warm_master.json --diagnostics-dir C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_gate483_diagnostics
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --glass-scale 0.000008764434957115609 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache\integration\resident_coverage_map_H.fits --min-coverage 190 --diagnostics-dir C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190_diagnostics
.\.venv\Scripts\glass.exe speedup-summary --glass-run C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json --markdown C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.md --min-speedup 20
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache\manifest.json --glass-run C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\acceptance\warm_threshold_acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\acceptance\warm_threshold_acceptance_audit.md --min-lights 200 --min-bias 20 --min-dark 20 --min-flat 20 --min-active-frames 190 --min-speedup 20 --min-coverage-fraction 0.95 --max-rms-diff 0.01 --max-abs-diff-p99 0.01
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\runs\warm_finite_full_frame_cache --out C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\reports\warm_report.html --compare-json C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json --acceptance-audit C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\acceptance\warm_threshold_acceptance_audit.json
```

Full validation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,compute_cap --format=csv,noheader
```

## Test Results

- Focused StackEngine/resident tests: `22 passed in 0.29s`.
- Ruff: `All checks passed!`.
- Full pytest: `1125 passed in 41.28s`.

## Real 200-Light Results

- Dataset: M38 H-alpha benchmark, `200` lights, `20` bias, `20` dark, `20`
  flats, user-generated WBPP black-box reference output.
- Output root:
  `C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real`.
- Cold full-frame total: `35.3481062000501 s`.
- Cold `master_build_or_load`: `15.344373799976893 s`.
- Warm full-frame total: `20.491344500042032 s`.
- Warm `master_build_or_load`: `0.30085249996045604 s`.
- Gate483 cold total comparison: `52.42856379994191 s` ->
  `35.3481062000501 s` (`1.4832071484459783x`).
- Gate483 cold master-build comparison: `32.28885949996766 s` ->
  `15.344373799976893 s` (`2.1042800391122043x`).
- Warm-vs-cold master difference: RMS/p99/max all `0.0`.
- Warm-vs-Gate483 warm master difference: RMS/p99/max all `0.0`.
- Warm-vs-WBPP scaled coverage>=190 compare:
  - RMS: `0.0017794216505176163`.
  - p99 absolute difference: `0.00042621337808668863`.
  - max absolute difference: `0.5499989986419678`.
- Warm GLASS vs WBPP speedup: `53.31719448656768x`.
- Threshold acceptance audit: `passed`.

## CUDA

- CUDA available: yes.
- Python binding: `glass_cuda.cuda_available() == True`.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- Driver: `596.21`.
- Total VRAM: `97886-97887 MiB`.
- Sampled VRAM during final check: `825 MiB` used, `95775 MiB` free.

## Disk / Cleanup Note

- C: free after the gate: about `34.92 GiB`.
- Repository size: about `2.338 GiB`.
- Heavy generated-output roots:
  - `C:\glass_runs`: about `219.346 GiB`.
  - `C:\gpwbpp_runs`: about `351.769 GiB`.
- Keep current Gate484 artifacts and
  `C:\gpwbpp_runs\final_m38_h_200` for the active 200-light evidence chain.
- If C: fills again, old `C:\glass_runs\phase2_s2_gate_*` directories are the
  preferred cleanup candidates. Source tree, virtual environment, and
  user-owned raw image directories should not be deleted for this gate.

## Artifacts

- Summary:
  `C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\gate484_real_ab_summary.json`.
- Warm report:
  `C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\reports\warm_report.html`.
- Acceptance:
  `C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\acceptance\warm_threshold_acceptance_audit.json`.
- Speedup:
  `C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\speedup\warm_vs_wbpp_speedup_with_compare.json`.
- Compare:
  `C:\glass_runs\phase2_s2_gate484_finite_full_frame_mean_ab_real\compare\warm_vs_wbpp_scaled_coverage190.json`.

## Known Limitations

- The full-frame path is not a general StackEngine default. It requires explicit
  metadata and trades CPU RAM for lower overhead.
- Gate481's older helper still has a faster cold master-build/load number
  (`10.911685600003693 s`) than this StackEngine path, so native/CUDA master
  mean building remains the next performance target.
- Robust resident master-frame rejection remains deferred. A previous direct
  CPU StackEngine robust attempt exceeded 30 minutes on the real calibration
  set before writing cache output.
- This gate does not change registration, warp, local normalization,
  winsorized light rejection, or CUDA integration formulas.

## Next Step

- Build a native/CUDA resident master mean builder or GPU-resident master-cache
  path so cold-cache performance can recover Gate481 helper speed while keeping
  StackEngine/DQ provenance.
- Continue Phase 2 mainline work on DQ/mask pipeline contracts and resident
  registration/warp orchestration reductions.

## Clean-Room Compliance

- This gate used GLASS-owned source code, GLASS-generated artifacts, user-owned
  M38 FITS inputs, and user-generated WBPP black-box outputs/timing only.
- It did not inspect or copy official PixInsight/WBPP/PJSR source code.
- It did not modify input image directories.
- The full-frame optimization changes execution strategy only; it does not
  import external implementation behavior or proprietary formulas.
