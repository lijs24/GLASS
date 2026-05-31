# S2-Gate63 Status - Pixel-Refine Workload Ledger

## Gate
- Gate: S2-Gate63
- Name: Pixel-Refine Workload Ledger
- Status: passed
- Date: 2026-06-01 Asia/Shanghai

## Completed content
- Added a workload ledger for resident CUDA batched triangle pixel refinement.
- Native batch-refine results now report:
  - `metric_workload_model=candidate_count_x_sampled_pixels`
  - coarse/fine sampled pixels per candidate
  - coarse/fine total candidate sample evaluations
  - coarse/fine effective metric throughput in Msamples/s
- The resident CUDA run now carries those fields into `resident_artifacts.json`.
- Per-frame registration warnings now include the same pixel-refine workload fields.
- Added focused assertions for native resident stack batch refine and resident CUDA triangle-registration artifacts.
- Updated Phase 2 gate documentation and the algorithm source ledger.

## Commands run
- Native build:
  - `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_batches_matrix_translation_refine`
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- 200-light A/B resident CUDA runs:
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_a_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
  - same command with `--out C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_b_20260601`
- Determinism/output audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_b_20260601 --out C:\glass_runs\phase2_s2_gate_63_200\resident_determinism_pixel_refine_workload_a_vs_b.json --markdown C:\glass_runs\phase2_s2_gate_63_200\resident_determinism_pixel_refine_workload_a_vs_b.md --fail-on-mismatch`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test results
- Native build: passed
- First focused test pass after wrapper propagation fix:
  - `tests\test_cuda_resident_stack.py::test_resident_stack_batches_matrix_translation_refine`: passed
  - `tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`: passed
- Determinism/output audit: passed
  - frame signature differences: 0
  - registration differences: 0
  - frame accounting differences: 0
  - output differences: 0
- Ruff: passed (`All checks passed!`)
- Full pytest: passed (`269 passed in 11.27s`)

## 200-light timing and workload results
- Gate63 A/B average total elapsed: 12.776409 s
- Gate63 A/B average registration/warp: 1.785792 s
- Gate63 A/B average pixel refine: 0.893831 s
- Gate63 A/B average native coarse metric: 0.681170 s
- Gate63 A/B average native fine metric: 0.206271 s
- Coarse candidates: 15552
- Fine candidates: 15552
- Coarse sampled pixels per candidate: 3854400
- Fine sampled pixels per candidate: 963600
- Coarse candidate sample evaluations: 59943628800
- Fine candidate sample evaluations: 14985907200
- Average coarse throughput: 88001.385 Msamples/s
- Average fine throughput: 72663.637 Msamples/s

### Gate63 run A
- Output: `C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_a_20260601`
- Total elapsed: 12.972573 s
- Resident registration/warp: 1.787080 s
- Triangle pixel refine: 0.893460 s
- Native coarse metric: 0.682685 s
- Native fine metric: 0.203620 s
- Coarse throughput: 87805.718 Msamples/s
- Fine throughput: 73597.495 Msamples/s

### Gate63 run B
- Output: `C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_b_20260601`
- Total elapsed: 12.580246 s
- Resident registration/warp: 1.784504 s
- Triangle pixel refine: 0.894202 s
- Native coarse metric: 0.679656 s
- Native fine metric: 0.208922 s
- Coarse throughput: 88197.052 Msamples/s
- Fine throughput: 71729.778 Msamples/s

## CUDA availability
- CUDA backend: available
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Driver: 596.21

## Known limitations
- This gate is diagnostic-only and does not reduce pixel-refine runtime.
- Gate63 total elapsed is slightly slower than Gate62 in this A/B pair, but registration/warp and pixel-refine timings are effectively unchanged; the difference is within run-level I/O/runtime variance.
- Pixel refine remains the largest registration component after Gate62. The coarse pass dominates because it evaluates about 59.94 billion candidate samples.
- The current ledger uses host steady-clock timings around synchronous native calls; CUDA-event timing can be added later if needed.

## Next step
- Optimize the coarse pixel-refine workload. Candidate directions:
  - reduce coarse sampled pixels with a multiresolution or star-mask metric;
  - reduce candidate count before full-image metric evaluation;
  - move coarse winner selection/candidate generation further onto the GPU;
  - add CUDA event timing before changing metric formulas.

## Clean-room compliance
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- Only GLASS source, generated GLASS artifacts, tests, and user-provided benchmark data were used.
- Original input image directories were treated as read-only.
