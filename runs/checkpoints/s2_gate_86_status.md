# S2 Gate 86 Status: Triangle Registration Fused Matrix Dispatch

## Gate

S2-Gate 86 - route accepted resident `similarity_cuda_triangle` registration
matrices directly into fused resident matrix integration.

## Completed

- Extended `resident_integration_dispatch=fused_matrix` eligibility to
  `resident_registration=similarity_cuda_triangle`.
- Preserved existing triangle catalog, descriptor fit, pixel-refine, quality
  gate, zero-weight, and registration-result behavior.
- Deferred accepted triangle matrices to fused integration instead of applying
  registration-stage resident matrix warp/scatter.
- Added per-frame warnings for
  `resident_registration_application=fused_matrix_deferred`,
  `triangle_warp_batch_mode=fused_matrix_deferred`, and
  `triangle_warp_batch_timing_model=fused_integration_deferred`.
- Added resident artifact fields:
  `triangle_fused_matrix_deferred`,
  `triangle_fused_matrix_deferred_count`, and updated fused dispatch eligible
  registration modes.
- Added a CLI-level CUDA A/B test that compares triangle stack dispatch against
  triangle fused dispatch on the same synthetic shifted pair.
- Updated Phase 2 hardening notes and algorithm-source documentation.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_86_200\fused_triangle_lanczos3_tuned_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-integration-dispatch fused_matrix --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_86_200\stack_triangle_bilinear_tuned_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation bilinear --resident-warp-clamping-threshold 0.3 --resident-warp-batch-dispatch loop --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_86_200\fused_triangle_bilinear_tuned_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-integration-dispatch fused_matrix --resident-warp-interpolation bilinear --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_86_200\fused_triangle_bilinear_tuned_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_86_200\stack_triangle_bilinear_tuned_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_86_200\compare_fused_triangle_bilinear_vs_stack.html --glass-time-seconds 10.383039500098675 --reference-time-seconds 12.168695699889213 --glass-label Gate86_fused_triangle_bilinear --reference-label Gate86_stack_triangle_bilinear --ignore-border-px 0`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_86_200\fused_triangle_lanczos3_tuned_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_81_200\default_loop_recipe_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_86_200\compare_fused_triangle_lanczos3_vs_gate81_stack.html --glass-time-seconds 12.414336500223726 --reference-time-seconds 12.323173000011593 --glass-label Gate86_fused_triangle_lanczos3 --reference-label Gate81_stack_triangle_lanczos3 --ignore-border-px 0`
- `git diff --check`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Result

- Native CUDA build: passed; target was already up to date.
- Focused resident CUDA tests: 3 passed, then the new Gate86 test passed
  again after a readability cleanup.
- Full ruff: passed.
- Full pytest: 290 passed in 12.77 s.
- `git diff --check`: passed with only Git LF/CRLF normalization warnings.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## 200-Light Real Data Result

Inputs were read-only. Gate86 used the existing M38 H-alpha 200-light plan,
shared resident master cache, seven known excluded light frames, no local
normalization, no weighting, and winsorized sigma rejection.

An initial untuned bilinear stack attempt omitted the validated real-data star
threshold/candidate parameters and did not complete within the 600 s command
timeout. The leftover GLASS process was explicitly stopped, and the accepted
benchmark used the Gate81 tuned triangle recipe.

Stack triangle bilinear baseline:

- Run:
  `C:\glass_runs\phase2_s2_gate_86_200\stack_triangle_bilinear_tuned_20260601`
- Total elapsed: 12.168695699889213 s.
- Light read/upload/calibrate: 6.259132499806583 s.
- Resident registration/warp: 1.1808692985214293 s.
- Triangle warp component: 0.23835190013051033 s.
- Resident integration: 0.2930009998381138 s.
- Triangle deferred matrix count: 0.

Fused triangle bilinear:

- Run:
  `C:\glass_runs\phase2_s2_gate_86_200\fused_triangle_bilinear_tuned_20260601`
- Total elapsed: 10.383039500098675 s.
- Light read/upload/calibrate: 6.311886600218713 s.
- Resident registration/warp: 0.9658080013468862 s.
- Resident integration: 0.29876379994675517 s.
- Fused native total: 0.2984901 s.
- Fused native sync: 0.2238549 s.
- Fused download: 0.0671116 s.
- Triangle deferred matrix count: 192.
- Download mode: `master_weight`.
- Diagnostic maps downloaded: false.

Comparison:

- Report:
  `C:\glass_runs\phase2_s2_gate_86_200\compare_fused_triangle_bilinear_vs_stack.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate_86_200\compare_fused_triangle_bilinear_vs_stack.json`
- Shape match: true.
- Compared pixels: 61651200.
- RMS diff: 0.0.
- Max abs diff: 0.0.
- Speedup vs stack triangle bilinear: 1.1719781765034765x.

Fused triangle Lanczos3 diagnostic run:

- Run:
  `C:\glass_runs\phase2_s2_gate_86_200\fused_triangle_lanczos3_tuned_20260601`
- Total elapsed: 12.414336500223726 s.
- Fused native total: 2.5535266 s.
- Fused native sync: 2.4825162 s.
- Speedup vs Gate81 stack triangle Lanczos3: 0.9926565950415078x.
- RMS diff vs Gate81 stack triangle Lanczos3: 0.5446892640575016.

## Known Limitations

- Gate86 makes fused triangle routing opt-in. The default stack route remains
  unchanged.
- Fused triangle dispatch currently requires local normalization to be off.
- `resident-output-maps minimal` intentionally skips coverage/rejection/DQ and
  geometric diagnostic map downloads.
- Bilinear fused dispatch is faster and pixel-identical against the bilinear
  stack route on the 200-light test.
- Fused Lanczos3 is currently not a speed win because the fused Lanczos3
  winsorized kernel sync dominates the saved registration-stage warp/scatter.
  Lanczos3 also showed small nonzero differences against the older stack
  baseline, so it needs a focused numerical/edge-semantics gate before being
  promoted.

## Next Step

S2-Gate 87 should optimize or split the fused Lanczos3 winsorized-sigma kernel,
or make bilinear fused triangle the recommended high-speed path while adding a
dedicated Lanczos3 correctness/performance gate. The remaining major timing
blocks are I/O + H2D + calibration and triangle descriptor/pixel-refine
orchestration.

## Clean-Room Compliance

Compliant. This gate uses only GLASS-owned CUDA/Python routing, tests, and
user-generated benchmark artifacts. It did not read, copy, summarize, or rework
proprietary implementation source. Input image directories were treated as
read-only.
