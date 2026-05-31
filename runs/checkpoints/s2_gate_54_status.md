# S2-Gate 54 Status: Resident Pixel-Refine Shared Candidate Metric Workspace

## Gate

S2-Gate 54: Resident Pixel-Refine Shared Candidate Metric Workspace.

## Completed Content

- Reused a single native CUDA matrix-refine workspace across the resident
  triangle-registration batch pixel-refine path.
- Preserved the existing candidate-grid search, NCC/RMS metric kernel,
  coarse/fine refinement semantics, quality gates, warp behavior, and output
  map policy.
- Added workspace diagnostics to native results, Python normalization,
  per-frame registration warnings, `resident_artifacts.json`, resident timing
  components, and the HTML resident summary.
- Added focused CUDA tests for batch/single pixel-refine equivalence and
  resident artifact/warning propagation.
- Updated Phase 2 gate documentation and algorithm-source tracking.

## Commands Run

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m ruff check src tests`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_batches_matrix_translation_refine tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\s2_gate_54_compare.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-time-seconds 19.021167600061744 --reference-time-seconds 1092.541 --glass-label GLASS-S2G54-pixel-refine-workspace --reference-label WBPP-blackbox`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\s2_gate_54_compare.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --out C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\phase2_contract_acceptance_audit_s2_gate_54.json --markdown C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\phase2_contract_acceptance_audit_s2_gate_54.md --min-active-frames 190 --min-speedup 2.0`
- `.\.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601 --acceptance-audit C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\phase2_contract_acceptance_audit_s2_gate_54.json --out C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\s2_gate_54_report.html`
- `git diff --check`

## Test Results

- Native CUDA build: passed.
- Ruff: `All checks passed!`
- Focused CUDA tests: `2 passed in 2.21s`.
- Full pytest: `263 passed in 11.40s`.
- `git diff --check`: passed; only existing LF-to-CRLF working-copy warnings.

## Real 200-Light Benchmark

- Run path:
  `C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601`
- GLASS run elapsed from `run_timing.json`: `19.021167600061744 s`.
- PowerShell wall time: `19.3311761 s`.
- External reference elapsed: `1092.541 s`.
- Speedup vs reference: `57.43816693968111x`.
- Active/integrated frames: `193`.
- Compare RMS difference: `0.0016479948025167911`.
- Compare P99 absolute difference: `0.00042484054341912145`.
- Compared-pixel coverage fraction: `0.9604271936312675`.
- Acceptance audit: passed, `99` checks passed and `0` failed.

## Resident Registration Timing

- `triangle_moving_catalog_batch`: `1.0812433999963105 s`.
- `triangle_descriptor_fit_batch`: `0.8375810002908111 s`.
- `triangle_pixel_refine_batch`: `3.1641195002011955 s`.
- `triangle_pixel_refine_native_coarse`: `2.3896981 s`.
- `triangle_pixel_refine_native_fine`: `0.765427 s`.
- `triangle_warp`: `0.4440190000459552 s`.
- Workspace mode: `shared_candidate_metric_buffers`.
- Workspace candidate capacity: `81`.
- Workspace bytes: `8100`.

## CUDA Availability

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native backend loaded: yes.

## Artifacts

- Compare HTML:
  `C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\s2_gate_54_compare.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\s2_gate_54_compare.json`
- Acceptance JSON:
  `C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\phase2_contract_acceptance_audit_s2_gate_54.json`
- Acceptance Markdown:
  `C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\phase2_contract_acceptance_audit_s2_gate_54.md`
- HTML report:
  `C:\glass_runs\phase2_s2_gate_54_200\resident_pixel_refine_workspace_20260601\s2_gate_54_report.html`

## Known Limitations

- This gate reduces CUDA allocation churn in pixel refinement but still launches
  the coarse and fine metric searches per moving frame.
- `triangle_pixel_refine_batch` remains a major registration component; deeper
  batching of candidate metric scoring and synchronization is still needed.
- Total 200-light runtime is within the accepted regression family but is
  slightly slower than S2-Gate 53 in this run, while the pixel-refine component
  itself improved from about `3.278 s` to `3.164 s`.
- XISF pixel-writing remains outside this gate; the resident output path still
  writes FITS artifacts.

## Next Step

S2-Gate 55 should target deeper resident registration batching: either reduce
per-frame pixel-refine launch/sync frequency or batch multiple matrix metric
candidate evaluations in one native scheduling pass.

## Clean-Room Compliance

Compliant. This gate is a GLASS-owned CUDA allocation/scheduling optimization
around existing GLASS kernels and artifacts. It used project tests, GLASS
artifacts, and user-generated black-box reference outputs only; no proprietary
implementation source was read, copied, summarized, or reworked.
