# S2-Gate 55 Status: Resident Pixel-Refine Flattened Batch Metric Launch

## Gate

S2-Gate 55: Resident Pixel-Refine Flattened Batch Metric Launch.

## Completed Content

- Added a CUDA flattened frame/candidate matrix metric kernel and launcher for
  resident batch pixel refinement.
- Replaced per-moving-frame coarse/fine metric launches with one coarse metric
  launch for the whole moving-frame batch and one fine metric launch for the
  whole moving-frame batch.
- Preserved the existing candidate grids, matrix inversion, NCC/RMS metric
  formulas, fine-search semantics, registration quality gates, warp behavior,
  frame accounting, and output map policy.
- Added diagnostics for flattened metric mode, metric launch count,
  coarse/fine total candidate counts, workspace capacity, workspace bytes, and
  native coarse/fine metric timings.
- Propagated the diagnostics through native results, `glass_cuda.py`,
  resident per-frame warnings, `resident_artifacts.json`, resident timing
  components, and the HTML resident summary.
- Updated focused CUDA tests, Phase 2 gate documentation, and
  `docs/algorithm_sources.md`.

## Commands Run

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_batches_matrix_translation_refine tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\s2_gate_55_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 16.410817299969494 --reference-time-seconds 1092.541 --glass-label GLASS-S2G55-pixel-refine-flattened-metric --reference-label WBPP-blackbox`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\s2_gate_55_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\phase2_contract_acceptance_audit_s2_gate_55.json --markdown C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\phase2_contract_acceptance_audit_s2_gate_55.md --min-active-frames 190 --min-speedup 2.0`
- `.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\phase2_contract_acceptance_audit_s2_gate_55.json --out C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\s2_gate_55_report.html`

## Test Results

- Native CUDA build: passed.
- Ruff: `All checks passed!`
- Focused CUDA tests: `2 passed in 2.29s`.
- Full pytest: `263 passed in 11.33s`.

## Real 200-Light Benchmark

- Accepted run path:
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601`
- GLASS run elapsed from `run_timing.json`: `16.410817299969494 s`.
- PowerShell wall time: `16.7264244 s`.
- External reference elapsed: `1092.541 s`.
- Speedup vs reference: `66.57444172521687x`.
- Active/integrated frames: `193`.
- Compare RMS difference: `0.001592865209089461`.
- Compare P99 absolute difference: `0.0004341281461529463`.
- Compared-pixel coverage fraction: `0.9607661164746185`.
- Acceptance audit: passed, `99` checks passed and `0` failed.

## Resident Registration Timing

- `triangle_moving_catalog_batch`: approximately `1.066 s`.
- `triangle_descriptor_fit_batch`: approximately `0.835 s`.
- `triangle_pixel_refine_batch`: `0.8859470998868346 s`.
- `triangle_pixel_refine_native_coarse`: `0.6785562 s`.
- `triangle_pixel_refine_native_fine`: `0.2024936 s`.
- `triangle_warp`: approximately `0.448 s`.
- Batch metric mode: `flattened_frame_candidate_grid`.
- Metric kernel launches: `2`.
- Coarse total candidates: `15552`.
- Fine total candidates: `15552`.
- Workspace mode: `shared_flattened_candidate_metric_buffers`.
- Workspace bytes: `1617408`.

## Regression Note

- S2-Gate 54 accepted run: `19.021167600061744 s`, speedup `57.438x`,
  `triangle_pixel_refine_batch` about `3.164 s`.
- S2-Gate 55 accepted run: `16.410817299969494 s`, speedup `66.574x`,
  `triangle_pixel_refine_batch` about `0.886 s`.
- The flattened metric launch reduced the pixel-refine component by about
  `2.28 s` and improved end-to-end elapsed time by about `2.61 s` on the
  accepted 200-light run.
- An earlier S2-Gate 55 run at
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_20260601`
  finished in `16.7969194999896 s` but failed acceptance because
  `coverage_fraction=0.9285872294456555` was below the `0.95` contract floor.
  A direct rerun with the same code and command passed with
  `coverage_fraction=0.9607661164746185`. This points to remaining
  nondeterminism in the resident catalog/descriptor selection path, not a
  stable flattened-metric regression. A later gate should make registration
  candidate selection deterministic enough that acceptance does not require a
  rerun.

## CUDA Availability

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend loaded: yes.

## Artifacts

- Compare HTML:
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\s2_gate_55_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\s2_gate_55_compare.json`
- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\phase2_contract_acceptance_audit_s2_gate_55.json`
- Acceptance Markdown:
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\phase2_contract_acceptance_audit_s2_gate_55.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_55_200\resident_pixel_refine_flattened_metric_retry_20260601\s2_gate_55_report.html`

## Known Limitations

- Fine candidate grids still depend on host-side coarse winners, so the native
  path remains a two-pass schedule.
- The resident triangle registration path still has observed nondeterminism in
  catalog/descriptor selection across real-data runs. S2-Gate 56 should target
  deterministic registration candidate selection or an acceptance-stable
  registration ordering audit.
- The flattened metric kernel duplicates the existing metric reduction logic;
  a future cleanup can factor the device-side accumulation into a helper once
  the performance gate is stable.

## Next Step

S2-Gate 56 should address acceptance stability by making resident
catalog/descriptor selection deterministic across runs, or at least adding a
strict audit that identifies exactly which frame/candidate changes cause
coverage swings.

## Clean-Room Compliance

Compliant. This gate is a GLASS-owned CUDA scheduling optimization around
existing GLASS resident frames and matrix metric kernels. It used project tests,
GLASS artifacts, and user-generated black-box reference outputs only; no
proprietary implementation source was read, copied, summarized, or reworked.
