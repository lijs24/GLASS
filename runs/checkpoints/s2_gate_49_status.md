# S2-Gate 49 Status: Shared Reference Device Buffers For Triangle Descriptor Fit

## Gate

S2-Gate 49: Shared Reference Device Buffers For Triangle Descriptor Fit

## Completed Content

- Reworked native `estimate_similarity_from_triangle_descriptors_batch_f32`
  so the shared reference catalog coordinates, triangle descriptors, and
  descriptor indices are copied to CUDA device memory once per batch.
- Reused those reference device buffers for every moving-frame triangle
  descriptor similarity fit in the batch.
- Preserved the existing descriptor definition, similarity scoring kernel,
  matrix output, RMS, inlier, and candidate-count semantics.
- Added auditable batch result fields:
  - `reference_device_reuse`
  - `reference_device_bytes`
- Propagated shared-reference device reuse diagnostics through:
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
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\s2_gate_49_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 23.404214899986982 --reference-time-seconds 1092.541 --glass-label GLASS-S2G49-resident-shared-reference-descriptor --reference-label WBPP-blackbox
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\s2_gate_49_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\phase2_contract_acceptance_audit_s2_gate_49.json --markdown C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\phase2_contract_acceptance_audit_s2_gate_49.md --min-active-frames 190 --min-speedup 2.0
.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\phase2_contract_acceptance_audit_s2_gate_49.json --out C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\s2_gate_49_report.html
```

## Test Results

- Focused CUDA batch descriptor/resident smoke tests: `2 passed`
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
  `C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601`
- Total resident CUDA runtime: `23.404214899986982 s`
- Reference runtime: `1092.541 s`
- Speedup vs reference: `46.68137789149285x`
- Coverage-masked RMS difference: `0.0015706278875147963`
- Coverage-masked P99 absolute difference: `0.00043026520870625973`
- Coverage fraction: `0.9574331399875429`
- Input / integrated / zero-weight frames: `200 / 193 / 7`
- Resident registration/warp total: `10.122825696133077 s`
- Triangle descriptor fit total: `0.886693499982357 s`
- Triangle descriptor fit batch: `0.886693499982357 s`
- Triangle descriptor reference device reuse: `true`
- Triangle descriptor reference device bytes: `6024`
- Triangle moving catalog batch: `5.358661899808794 s`
- Triangle moving descriptor batch: `0.11910170083865523 s`
- Triangle pixel refine batch: `3.2898754999041557 s`
- Triangle warp component: `0.44374069990590215 s`
- I/O + upload + calibration: `6.207380600273609 s`
- Output write: `0.5508277998305857 s`
- Resident triangle descriptor fit batch mode:
  `native_batch_shared_reference_device`
- Resident triangle pixel refine batch mode:
  `native_batch_one_seed_per_frame`
- Acceptance performance regression status: `ok`

## Artifacts

- `C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\resident_artifacts.json`
- `C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\s2_gate_49_compare.html`
- `C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\s2_gate_49_compare.json`
- `C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\phase2_contract_acceptance_audit_s2_gate_49.json`
- `C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\phase2_contract_acceptance_audit_s2_gate_49.md`
- `C:\glass_runs\phase2_s2_gate_49_200\resident_shared_reference_descriptor_20260601\s2_gate_49_report.html`

## Known Limits

- The batch descriptor-fit route now reuses shared reference buffers on device,
  but moving catalog coordinates/descriptors and per-fit output buffers are
  still allocated per moving frame.
- Moving triangle descriptor generation remains per frame, although resident
  orchestration caches those descriptors for the batch fit.
- The current batch route is enabled only for the fixed-threshold resident
  catalog-batch path; auto-threshold runs retain per-frame fit fallback.

## Next Step

S2-Gate 50 should reduce the remaining resident registration bottleneck by
batching or reusing moving descriptor-fit buffers, or by moving more of the
triangle moving-catalog/descriptor generation path into a resident native
batch primitive.

## Clean-Room Compliance

Compliant. The gate changes only GLASS-owned resident CUDA descriptor-fit
memory scheduling and diagnostics, uses user-generated benchmark outputs as
reference data, and does not read, copy, summarize, or rework proprietary
implementation source.
