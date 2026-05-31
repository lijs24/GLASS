# S2 Gate 85 Status: Fused Minimal Diagnostic Download Mode

## Gate

S2-Gate 85 - Fused Minimal Diagnostic Download Mode.

## Completed

- Added native fused `download_mode` support for resident matrix-warp weighted
  mean and sigma/winsorized-sigma integration.
- `download_mode=full` preserves the previous full diagnostic behavior:
  master, weight, coverage, rejection maps, and geometric coverage are allocated
  and downloaded when applicable.
- `download_mode=master_weight` allocates and downloads only master and weight
  maps, and passes null diagnostic-map pointers into the fused kernels.
- Wired resident fused dispatch to use `master_weight` automatically when
  `--resident-output-maps minimal` is selected.
- Kept `science` and `audit` modes on full diagnostic downloads so DQ,
  coverage, rejection, and geometric provenance remain complete in diagnostic
  modes.
- Recorded `download_mode`, `diagnostic_maps_downloaded`, and reduced
  `output_bytes` in native fused timing and resident artifacts.
- Added CLI-level CUDA coverage verifying that fused minimal output matches the
  stack route numerically while leaving unavailable diagnostic paths unset.
- Updated Phase 2 gate planning and algorithm-source documentation.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_winsorized_lanczos3_matches_warp_then_integrate tests\test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_mean_bilinear_matches_warp_then_integrate`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_85_200\fused_minimal_external_bilinear_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration external_matrix --resident-registration-results C:\glass_runs\phase2_s2_gate_81_200\default_loop_recipe_20260601\registration_results.json --resident-integration-dispatch fused_matrix --resident-warp-interpolation bilinear --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_85_200\fused_minimal_external_bilinear_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_84_200\stack_external_bilinear_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_85_200\compare_fused_minimal_vs_stack_external_bilinear.html --glass-time-seconds 9.402916999999434 --reference-time-seconds 11.254394300282001 --glass-label Gate85_fused_minimal_external_bilinear --reference-label Gate84_stack_external_bilinear --ignore-border-px 0`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Result

- Native CUDA build: passed.
- Focused CUDA resident tests: 4 passed.
- Full ruff: passed.
- Full pytest: 289 passed in 12.46 s.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## 200-Light Real Data Result

Inputs were read-only. Gate85 reused the same 200-light M38 H-alpha processing
plan, shared resident master cache, external `registration_results.json`,
excluded-frame list, bilinear matrix warp, no local normalization, no weighting,
and winsorized sigma rejection as Gate84.

- Gate84 stack external-matrix dispatch:
  `C:\glass_runs\phase2_s2_gate_84_200\stack_external_bilinear_20260601`
  - total: 11.254394300282001 s
  - registration warp/scatter: 0.23702649679034948 s
  - integration: 0.2959733996540308 s
- Gate84 fused external-matrix full diagnostic download:
  `C:\glass_runs\phase2_s2_gate_84_200\fused_external_bilinear_20260601`
  - total: 11.035161800216883 s
  - fused native total: 0.4273899 s
  - fused output bytes: 1479628800
  - download_s: 0.187026
  - sync_s: 0.2215096
- Gate85 fused external-matrix minimal diagnostic download:
  `C:\glass_runs\phase2_s2_gate_85_200\fused_minimal_external_bilinear_20260601`
  - total: 9.402916999999434 s
  - registration warp/scatter: 0.001899301540106535 s
  - integration wall: 0.302861999720335 s
  - fused native total: 0.3025801 s
  - fused output bytes: 493209600
  - download_s: 0.0747944
  - sync_s: 0.2207987
  - download_mode: `master_weight`
  - diagnostic_maps_downloaded: false
- Compare report:
  `C:\glass_runs\phase2_s2_gate_85_200\compare_fused_minimal_vs_stack_external_bilinear.html`
- Compare JSON:
  `C:\glass_runs\phase2_s2_gate_85_200\compare_fused_minimal_vs_stack_external_bilinear.json`
  - shape match: true
  - compared pixels: 61651200
  - RMS diff: 0.0
  - max abs diff: 0.0
  - speedup vs Gate84 stack external route: 1.1969045669851897x

## Known Limitations

- `master_weight` download mode is used only for fused dispatch with
  `resident-output-maps minimal`.
- Minimal fused artifacts intentionally have unavailable coverage, rejection,
  DQ, and geometric coverage diagnostics. Use `science` or `audit` when those
  maps are required.
- Kernel compute time is still dominated by the single fused winsorized-sigma
  pass (`sync_s` remains about 0.221 s on the 200-light run).
- Triangle registration still needs to route its accepted matrix list directly
  into fused integration to remove the remaining registered full-frame stack
  scatter from the main non-external registration path.

## Next Step

S2-Gate 86 should target fused rejection kernel compute time and/or route
`similarity_cuda_triangle` accepted matrices directly into fused dispatch. The
measured next bottleneck is no longer diagnostic download; it is the fused
winsorized-sigma kernel sync plus the still-non-fused triangle route.

## Clean-Room Compliance

Compliant. This gate changes only GLASS-owned CUDA allocation, copy-back, and
artifact routing. It uses project-defined output-map policy semantics and
GLASS-generated/user-generated benchmark artifacts. It did not read, copy,
summarize, or rework proprietary implementation source. Input image directories
were treated as read-only.
