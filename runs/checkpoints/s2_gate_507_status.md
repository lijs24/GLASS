# S2-Gate 507 Status: Contiguous Resident Catalog Workspace

## Gate

S2-Gate 507

## Completed Content

- Continued the Phase 2 mainline resident registration optimization path.
- Consolidated batched resident grid/NMS star-catalog device workspaces:
  - grid candidate `x/y/flux` arrays now share one contiguous SoA device buffer;
  - output catalog `x/y/flux` arrays now share one contiguous SoA device buffer;
  - final catalog output download is one contiguous SoA device-to-host copy
    instead of three separate copies;
  - centroid pre-refine `x/y` snapshots are one contiguous copy instead of two
    separate copies.
- Preserved star detection thresholds, candidate ordering, centroid refinement,
  descriptor generation, registration decisions, warp, rejection, and master
  pixels.
- Added native/Python artifact fields:
  - `catalog_workspace_layout`;
  - `catalog_grid_workspace_allocation_count`;
  - `catalog_output_workspace_allocation_count`;
  - `catalog_output_download_copy_count`;
  - `catalog_centroid_before_download_copy_count`;
  - `catalog_output_download_bytes`.
- Aggregated those fields into resident artifacts as
  `triangle_catalog_*` fields and per-frame warning diagnostics.
- Added focused CUDA and CLI tests for the new catalog workspace/download
  contract.
- Ran native build, ruff, focused tests, full pytest, CUDA doctor, and a real
  200-light candidate/repeat A/B.

## Changed Files

- `cpp/src/native_bindings.cpp`
- `src/glass_cuda.py`
- `src/glass/engine/resident_cuda.py`
- `tests/test_cuda_resident_stack.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `runs/checkpoints/s2_gate_507_status.md`

## Commands Run

- `cmd /c "VsDevCmd.bat -arch=x64 && cmake --build build --config Release -j 1"`
- `python -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests/test_gpu_star_detect.py::test_resident_stack_star_grid_top_nms_candidates_batch_matches_single_calls tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `python -m pytest -q`
- `glass doctor`
- Real 200-light run command, executed for `candidate` and `repeat`:

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --backend cuda --memory-mode resident --until-stage integration `
  --local-normalization off --integration-rejection winsorized_sigma `
  --integration-weighting none --flat-floor 0.05 `
  --resident-registration similarity_cuda_triangle `
  --resident-star-threshold 350 --resident-star-max-candidates 48 `
  --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 `
  --resident-warp-interpolation lanczos3 `
  --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal `
  --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache `
  --out <candidate-or-repeat>
```

- External-reference compare:

```powershell
glass compare `
  --glass C:\glass_runs\phase2_s2_gate507_catalog_contiguous_soa_ab_real\runs_20260623_061314\repeat\integration\resident_master_H.fits `
  --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf `
  --out C:\glass_runs\phase2_s2_gate507_catalog_contiguous_soa_ab_real\runs_20260623_061314\compare_vs_wbpp_fastintegration_scaled_coverage190.html `
  --glass-time-seconds 6.6277335999766365 `
  --reference-time-seconds 1092.541 `
  --glass-label GLASS-Gate507-resident-minimal `
  --reference-label PixInsight-WBPP-fastIntegration `
  --glass-scale 8.764434957115609e-06 `
  --glass-offset 0.0006274500691899127 `
  --glass-coverage-map C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_coverage_map_H.fits `
  --min-coverage 190
```

## Test Results

- Native build: passed.
- Ruff: passed.
- Focused CUDA/resident tests: `3 passed in 0.97 s`.
- Full pytest: `1153 passed in 41.65 s`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`.

## Real 200-Light Results

Run root:

`C:\glass_runs\phase2_s2_gate507_catalog_contiguous_soa_ab_real\runs_20260623_061314`

Runtime:

- Gate507 candidate: `6.662307399965357 s`.
- Gate507 repeat: `6.6277335999766365 s`.
- Gate506 repeat baseline: `6.644183400028851 s`.
- WBPP black-box fastIntegration reference: `1092.541 s`.

Artifact contract:

- `triangle_catalog_workspace_layout=contiguous_soa`.
- `triangle_catalog_grid_workspace_allocation_count=1`.
- `triangle_catalog_output_workspace_allocation_count=1`.
- `triangle_catalog_output_download_copy_count=1`.
- `triangle_catalog_centroid_before_download_copy_count=1`.
- `triangle_catalog_output_download_bytes=114624`.
- Existing minimal integration contract remains:
  `native_map_workspace_mode=master_only_no_weight_or_diagnostic_device_maps`,
  `weight_map_downloaded=false`, `diagnostic_maps_downloaded=false`.

Component timing:

- Gate507 candidate `triangle_moving_catalog`: `0.26672859978862107 s`.
- Gate507 repeat `triangle_moving_catalog`: `0.2642694999813102 s`.
- Gate507 repeat `triangle_moving_catalog_native_total`: `0.257951 s`.
- Gate507 repeat `triangle_moving_catalog_native_output_download`:
  `0.0377995 s`.
- Gate507 repeat `triangle_moving_catalog_native_sync`: `0.2145568 s`.
- Gate507 repeat `triangle_moving_catalog_native_centroid_refine`: `0.0377232 s`.
- Gate506 repeat `triangle_moving_catalog_native_output_download` was about
  `0.0367169 s`, so this gate did not materially improve that timing component
  even though it reduced output copy count and allocation count.

Numerical agreement:

- Gate507 candidate vs Gate507 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate507 candidate vs Gate506 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate507 repeat vs Gate506 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.

External-reference comparison:

- Report:
  `C:\glass_runs\phase2_s2_gate507_catalog_contiguous_soa_ab_real\runs_20260623_061314\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate507_catalog_contiguous_soa_ab_real\runs_20260623_061314\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Speedup vs external fastIntegration reference:
  `164.84383138209589x`.
- RMS difference: `0.0017794216505176163`.
- P99 absolute difference: `0.00042621337808668863`.
- Compared pixels with `min_coverage=190`: `59217988`.

## Known Limits

- This is a resident catalog workspace consolidation and transfer-count
  simplification, not a scientific algorithm change.
- The real 200-light benchmark did not show a clear catalog output-download
  timing win; native sync and centroid/refine work still dominate the moving
  catalog component.
- The next registration performance gate should move more catalog/scoring state
  fully resident on the device or reduce synchronization phases rather than
  only reducing host download copy count.

## Next Step

Continue Phase 2 mainline work on resident registration:

- reduce `triangle_moving_catalog_native_sync`;
- reduce or batch centroid/refine synchronization phases;
- move more descriptor-fit/scoring state to persistent device workspaces;
- keep the Gate504/505/506/507 bitwise real-data baseline unless a deliberate
  science gate changes output with explicit validation.

## Clean-Room Compliance

Compliant. This gate changed GLASS-owned native CUDA binding memory layout,
Python wrapper normalization, resident artifact aggregation, and tests. It used
GLASS tests, GLASS real-run artifacts, and a user-generated external reference
output for black-box comparison. No official PixInsight/WBPP/PJSR source code
was read, copied, summarized, or reworked.
