# S2-Gate496 Status: Resident stack minimal diagnostic-download bypass

## Gate

- Gate: S2-Gate496
- Date: 2026-06-23
- Purpose: reduce resident CUDA stack output-transfer overhead for speed runs while preserving full diagnostic output in audit/science modes.
- Status: green

## Completed work

- Added a native `download_mode` argument to `ResidentCalibratedStack::integrate_sigma_clip`.
- `download_mode="full"` preserves the previous behavior and downloads master, weight, coverage, low-rejection, and high-rejection arrays.
- `download_mode="master_weight"` downloads only the final master and weight arrays and returns no diagnostic rejection/coverage arrays.
- Wired `--resident-output-maps minimal` to use `download_mode="master_weight"` for registered-stack sigma/winsorized integration.
- Skipped geometric warp coverage-map download in the registered-stack path when minimal output maps are requested.
- Recorded stack dispatch metadata:
  - `download_mode`
  - `diagnostic_maps_downloaded`
- Added a focused regression test proving minimal stack runs omit diagnostic downloads.
- Documented the new minimal-output transfer policy in `docs/algorithm_sources.md`.

## Cleanup status

- Checked C: drive free space before/after cleanup.
- C: is not full; free space after this gate was approximately 284-285 GiB.
- Removed only regenerable workspace caches:
  - `build`
  - `.pytest_cache`
  - `.ruff_cache`
  - Python `__pycache__` directories under source/test/benchmark trees
- Preserved historical evidence under `C:\glass_runs`.
- Main future cleanup candidate, if needed: old run evidence in `C:\glass_runs` (large, not removed in this gate).

## Commands run

Native rebuild after changing pybind11 bindings:

```powershell
cmd /c "`"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat`" -arch=x64 && .venv\Scripts\cmake.exe -S . -B build -G Ninja -DGLASS_BUILD_CUDA=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=`"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe`" -DCUDAToolkit_ROOT=`"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2`" -DCMAKE_CUDA_ARCHITECTURES=120 -DPython_EXECUTABLE=`"C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\python.exe`" -Dpybind11_DIR=`"C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Lib\site-packages\pybind11\share\cmake\pybind11`""
cmd /c "`"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat`" -arch=x64 && .venv\Scripts\cmake.exe --build build --config Release --target _glass_cuda_native"
```

Focused CUDA tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads tests/test_cuda_resident_stack.py
```

Full tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Real 200-light audit/full-map run:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\runs\stack_audit_full_maps --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
```

Real 200-light minimal-map run:

```powershell
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\runs\stack_minimal_maps --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
```

Scaled coverage-limited compare and acceptance were run for both audit and minimal outputs using:

- `--glass-scale 8.764434957115609e-06`
- `--glass-offset 0.0006274500691899127`
- `--min-coverage 190`
- Coverage map from the audit/full-map run.

## Test results

- Focused CUDA subset: `47 passed in 0.66s`
- Full pytest: `1141 passed in 43.76s`
- `git diff --check`: passed; only Windows line-ending warnings were reported.

## CUDA status

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Driver: 596.21
- Total VRAM: 97887 MiB
- Free VRAM before real run: 95775 MiB
- CUDA toolkit used for local native rebuild: 13.2
- Target architecture for this local rebuild: 120

## Real 200-light A/B evidence

Dataset:

- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Frames: 200 light, 20 bias, 20 dark, 20 flat
- Reference frame: `LIGHT_H_0136`
- WBPP black-box timing metadata: `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- WBPP elapsed time: 1092.541 s

Audit/full-map GLASS run:

- Run root: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\runs\stack_audit_full_maps`
- Total elapsed: 17.824206900026184 s
- Speedup vs WBPP: 61.29534997702451x
- `download_mode`: `full`
- `diagnostic_maps_downloaded`: true
- Output maps: master, weight, DQ, coverage, low rejection, high rejection

Minimal/speed GLASS run:

- Run root: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\runs\stack_minimal_maps`
- Total elapsed: 8.31593049998628 s
- Speedup vs WBPP: 131.37928461545013x
- `download_mode`: `master_weight`
- `diagnostic_maps_downloaded`: false
- Output maps: final master only for the public artifact path; diagnostic transfer is skipped by policy

Timing breakdown:

| Run | Light read/upload/calibrate (s) | Resident registration accounted (s) | Resident integration (s) | Output write (s) |
| --- | ---: | ---: | ---: | ---: |
| audit/full | 3.5688270999817178 | 2.114227600259811 | 0.29918929998530075 | 0.45300249999854714 |
| minimal | 3.507886499981396 | 2.1107486003734737 | 0.20611199998529628 | 0.1734753999626264 |

Final-master equivalence:

- minimal vs audit: RMS 0.0, p99 0.0, max 0.0
- minimal vs Gate495: RMS 0.0, p99 0.0, max 0.0
- audit vs Gate495: RMS 0.0, p99 0.0, max 0.0
- Finite pixels compared: 61,651,200

Scaled WBPP compare metrics for both audit and minimal:

- RMS difference: 0.0017794216505176163
- p99 absolute difference: 0.00042621337808668863
- Coverage fraction: 0.960532609259836
- Compared pixels: 59,217,988

## Artifacts

- Audit report: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\reports\audit_report.html`
- Minimal report: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\reports\minimal_report.html`
- Audit compare JSON: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\compare\audit_vs_wbpp_scaled_coverage190.json`
- Minimal compare JSON: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\compare\minimal_vs_wbpp_scaled_coverage190.json`
- Audit speedup summary: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\speedup\audit_vs_wbpp_scaled_speedup.json`
- Minimal speedup summary: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\speedup\minimal_vs_wbpp_scaled_speedup.json`
- Audit acceptance: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\acceptance\audit_scaled_acceptance_audit.json`
- Minimal acceptance: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\acceptance\minimal_scaled_acceptance_audit.json`
- Audit resident result contract: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\contracts\audit_resident_result_contract.json`
- Audit stack engine contract: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\contracts\audit_stack_engine_contract.json`
- Audit pipeline contract: `C:\glass_runs\phase2_s2_gate496_minimal_download_ab_real\contracts\audit_pipeline_contract.json`

## Known limitations

- Minimal mode intentionally skips DQ, coverage, and rejection-map downloads; use audit/science output-map modes for full diagnostic evidence.
- Minimal acceptance validates final-master correctness and speed, but full diagnostic contracts are attached to the audit/full-map run.
- The native module was rebuilt locally with CUDA Toolkit 13.2 for this workstation; distribution packaging still needs separate wheel/runtime policy work.
- `build/` was regenerated during the native rebuild and remains ignored by git.

## Next step

- Continue Phase 2 mainline with a substantive performance gate:
  - reduce remaining resident registration orchestration overhead;
  - add deeper stage timing around star-table construction, triangle scoring, transform selection, and warp dispatch;
  - keep audit/full-map evidence path intact while using minimal mode for top-speed benchmark runs.

## Clean-room compliance

- Compliant.
- This gate used GLASS code, GLASS artifacts, real user-provided image data, and user-generated PixInsight/WBPP black-box timing/output metadata only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or reworked.
- Input image directories were treated as read-only.
