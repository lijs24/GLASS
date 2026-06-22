# S2-Gate 508 Status: Fused Global-Mean Catalog Sync

## Gate

S2-Gate 508

## Completed Content

- Continued the Phase 2 mainline resident registration optimization path.
- Fused resident global-mean centroid-background reduction into the initial
  batched catalog stream enqueue path:
  - mean sum/count workspaces are allocated before catalog stream launch;
  - each frame's mean reduction is launched on the same stream as its grid/NMS
    catalog kernel;
  - the first catalog stream synchronization now covers both catalog generation
    and global-mean reduction;
  - centroid refinement remains a separate synchronization because it depends
    on catalog seeds and per-frame background values.
- Reduced the real global-mean centroid catalog sync phase contract from 3
  phases to 2 phases.
- Preserved star detection thresholds, candidate ordering, centroid formula,
  descriptor generation, registration decisions, warp, rejection, accepted
  frames, and master pixels.
- Added native/Python/resident artifact fields:
  - `catalog_centroid_mean_sync_mode`;
  - `catalog_centroid_mean_blocks`;
  - `triangle_catalog_centroid_mean_sync_mode`;
  - `triangle_catalog_centroid_mean_blocks`;
  - fused timing model
    `batch_multistream_bulk_download_centroid_global_mean_fused_sync`.
- Added focused CUDA and CLI tests for the new fused global-mean sync contract.
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
- `runs/checkpoints/s2_gate_508_status.md`

## Commands Run

- `cmd /c "VsDevCmd.bat -arch=x64 && cmake --build build --config Release -j 1"`
- `python -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
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
  --glass C:\glass_runs\phase2_s2_gate508_catalog_mean_fused_sync_ab_real\runs_20260623_062032\repeat\integration\resident_master_H.fits `
  --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf `
  --out C:\glass_runs\phase2_s2_gate508_catalog_mean_fused_sync_ab_real\runs_20260623_062032\compare_vs_wbpp_fastintegration_scaled_coverage190.html `
  --glass-time-seconds 6.605046200042125 `
  --reference-time-seconds 1092.541 `
  --glass-label GLASS-Gate508-resident-minimal `
  --reference-label PixInsight-WBPP-fastIntegration `
  --glass-scale 8.764434957115609e-06 `
  --glass-offset 0.0006274500691899127 `
  --glass-coverage-map C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_coverage_map_H.fits `
  --min-coverage 190
```

## Test Results

- Native build: passed.
- Ruff: passed.
- Focused CUDA/resident tests: `2 passed in 0.99 s`.
- Full pytest: `1153 passed in 41.72 s`.

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

`C:\glass_runs\phase2_s2_gate508_catalog_mean_fused_sync_ab_real\runs_20260623_062032`

Runtime:

- Gate508 candidate: `6.634354900044855 s`.
- Gate508 repeat: `6.605046200042125 s`.
- Gate507 repeat baseline: `6.6277335999766365 s`.
- WBPP black-box fastIntegration reference: `1092.541 s`.

Artifact contract:

- `triangle_catalog_timing_model=batch_multistream_bulk_download_centroid_global_mean_fused_sync`.
- `triangle_catalog_sync_phase_count=2`.
- `triangle_catalog_centroid_mean_sync_mode=fused_with_catalog_sync`.
- `triangle_catalog_centroid_mean_blocks=4096`.
- `triangle_catalog_workspace_layout=contiguous_soa`.
- `triangle_catalog_output_download_copy_count=1`.
- `triangle_catalog_centroid_before_download_copy_count=1`.
- Existing minimal integration contract remains:
  `native_map_workspace_mode=master_only_no_weight_or_diagnostic_device_maps`,
  `weight_map_downloaded=false`, `diagnostic_maps_downloaded=false`.

Component timing:

- Gate508 candidate `triangle_moving_catalog`: `0.2533915998064913 s`.
- Gate508 repeat `triangle_moving_catalog`: `0.25295329990331084 s`.
- Gate508 repeat `triangle_moving_catalog_native_total`: `0.2463567 s`.
- Gate508 repeat `triangle_moving_catalog_native_sync`: `0.2331699 s`.
- Gate508 repeat `triangle_moving_catalog_native_output_download`:
  `0.0066761 s`.
- Gate508 repeat `triangle_moving_catalog_native_centroid_refine`:
  `0.0066019 s`.
- Gate507 repeat `triangle_moving_catalog`: `0.2642694999813102 s`.
- Gate507 repeat `triangle_moving_catalog_native_total`: `0.257951 s`.
- Gate507 repeat `triangle_moving_catalog_native_output_download`:
  `0.0377995 s`.
- Gate507 repeat `triangle_moving_catalog_native_sync`: `0.2145568 s`.
- Gate507 repeat `triangle_moving_catalog_native_centroid_refine`:
  `0.0377232 s`.

Numerical agreement:

- Gate508 candidate vs Gate508 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate508 candidate vs Gate507 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate508 repeat vs Gate507 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.

External-reference comparison:

- Report:
  `C:\glass_runs\phase2_s2_gate508_catalog_mean_fused_sync_ab_real\runs_20260623_062032\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate508_catalog_mean_fused_sync_ab_real\runs_20260623_062032\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Speedup vs external fastIntegration reference:
  `165.41004663873994x`.
- RMS difference: `0.0017794216505176163`.
- P99 absolute difference: `0.00042621337808668863`.
- Compared pixels with `min_coverage=190`: `59217988`.

## Disk Check

- C drive free space at checkpoint time: about `427.5 GB`.
- Project checkout size: about `2.38 GB`.
- Historical run artifacts:
  - `C:\glass_runs`: about `94.49 GB`;
  - `C:\gpwbpp_runs`: about `83.69 GB`.
- No cleanup was performed in this gate, to avoid deleting benchmark evidence.

## Known Limits

- This is a resident CUDA scheduling optimization, not a scientific algorithm
  change.
- The sync phase contract is improved from 3 to 2 for the real global-mean
  centroid path, but native sync and registration/warp orchestration still
  dominate the registration component.
- The next substantive gate should continue the resident registration/warp
  performance path: batch more descriptor/scoring/refinement work on device,
  reduce Python/CPU orchestration, and keep real 200-light bitwise parity unless
  a deliberate science change is introduced with explicit validation.

## Next Step

Return immediately to the real 200-light A/B mainline and target resident
registration/warp residency:

- reduce per-frame host/device round trips after catalog generation;
- keep star catalogs, descriptors, and scoring buffers resident across the
  batch where possible;
- preserve the Gate504-Gate508 bitwise real-data baseline unless a deliberate
  science gate changes output with explicit validation.

## Clean-Room Compliance

Compliant. This gate changed GLASS-owned native CUDA stream scheduling, Python
wrapper normalization, resident artifact aggregation, documentation, and tests.
It used GLASS tests, GLASS real-run artifacts, and a user-generated external
reference output for black-box comparison. No official PixInsight/WBPP/PJSR
source code was read, copied, summarized, or reworked.
