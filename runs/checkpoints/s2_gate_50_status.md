# S2-Gate 50 Status: Shared Moving And Output Device Buffers For Descriptor Fit

## Gate

S2-Gate 50: Shared Moving And Output Device Buffers For Descriptor Fit

## Completed Content

- Extended native `estimate_similarity_from_triangle_descriptors_batch_f32`
  to pre-validate all moving catalogs/descriptors before launching fits.
- Allocated reusable moving-catalog and output/candidate CUDA workspaces once
  per batch, alongside the existing shared reference device buffers from
  S2-Gate 49.
- Reused those moving/output device workspaces for each moving-frame triangle
  descriptor similarity fit in the batch.
- Preserved descriptor generation, descriptor similarity scoring, matrix
  output, RMS, inlier count, candidate count, registration results, and frame
  accounting semantics.
- Added auditable batch result fields:
  - `moving_device_reuse`
  - `moving_device_bytes`
  - `output_device_reuse`
  - `output_device_bytes`
- Propagated diagnostics through:
  - Python CUDA wrapper normalization
  - resident per-frame warnings
  - `resident_artifacts.json`
  - HTML resident summary rows
- Updated the Phase 2 gate plan and algorithm source log.

## Commands Run

```powershell
cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_triangle_descriptor_similarity_batch_matches_single_fits tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\s2_gate_50_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 23.143438499886543 --reference-time-seconds 1092.541 --glass-label GLASS-S2G50-resident-descriptor-workspaces --reference-label WBPP-blackbox
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\s2_gate_50_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\phase2_contract_acceptance_audit_s2_gate_50.json --markdown C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\phase2_contract_acceptance_audit_s2_gate_50.md --min-active-frames 190 --min-speedup 2.0
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\phase2_contract_acceptance_audit_s2_gate_50.json --out C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\s2_gate_50_report.html
```

## Test Results

- Focused CUDA descriptor/resident smoke tests: `2 passed`
- Full suite: `260 passed`
- Ruff: `All checks passed`
- Native CUDA build: passed
- Real 200-light acceptance audit: `passed`

## CUDA Availability

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Real-Data Result

- Run directory:
  `C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601`
- Total resident CUDA runtime: `23.143438499886543 s`
- Reference runtime: `1092.541 s`
- Speedup vs reference: `47.207375861860626x`
- Coverage-masked RMS difference: `0.001558294284488301`
- Coverage-masked P99 absolute difference: `0.00043095467146486016`
- Coverage fraction: `0.9574613308418977`
- Input / integrated / zero-weight frames: `200 / 193 / 7`
- Resident registration/warp total: `10.041651099920273 s`
- Triangle descriptor fit batch: `0.823492799885571 s`
- Triangle descriptor moving workspace reuse: `true`
- Triangle descriptor moving workspace bytes: `6584`
- Triangle descriptor output workspace reuse: `true`
- Triangle descriptor output workspace bytes: `4196216`
- Triangle moving catalog batch: `5.362747700419277 s`
- Triangle moving descriptor batch: `0.1233094041235745 s`
- Triangle pixel refine batch: `3.263707799836993 s`
- Triangle warp component: `0.4440311989746988 s`
- I/O + upload + calibration: `6.221945900004357 s`
- Output write: `0.5245058997534215 s`
- Acceptance performance regression status: `ok`

## Performance Note

- Compared with S2-Gate 49, total runtime improved from `23.404214899986982 s`
  to `23.143438499886543 s`.
- Descriptor-fit batch time improved from `0.886693499982357 s` to
  `0.823492799885571 s`.
- A separate experimental batch catalog-output download path was tried during
  development and rejected because it regressed the 200-light benchmark; it is
  not part of the committed default path.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\resident_artifacts.json`
- `C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\s2_gate_50_compare.html`
- `C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\s2_gate_50_compare.json`
- `C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\phase2_contract_acceptance_audit_s2_gate_50.json`
- `C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\phase2_contract_acceptance_audit_s2_gate_50.md`
- `C:\glass_runs\phase2_s2_gate_50_200\resident_descriptor_workspaces_20260601\s2_gate_50_report.html`

## Known Limits

- Moving descriptor generation still runs per moving frame.
- Descriptor scoring still launches once per moving fit; this gate removes
  allocation churn but does not fuse descriptor scoring across moving frames.
- Full-frame grid/NMS star catalog scanning remains the largest resident
  registration component.

## Next Step

S2-Gate 51 should target the actual dominant registration component:
`triangle_moving_catalog_batch`, likely by reducing full-frame star-scan work,
using a resident multi-frame catalog kernel, or introducing a scientifically
audited ROI/coarse-grid preselection path.

## Clean-Room Compliance

Compliant. The gate changes only GLASS-owned resident CUDA descriptor-fit
memory scheduling and diagnostics, uses user-generated benchmark outputs as
reference data, and does not read, copy, summarize, or rework proprietary
implementation source.
