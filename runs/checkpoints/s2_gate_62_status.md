# S2-Gate62 Status - Parallel Descriptor Fit Best Reduction

## Gate
- Gate: S2-Gate62
- Name: Parallel Descriptor Fit Best Reduction
- Status: passed
- Date: 2026-06-01 Asia/Shanghai

## Completed content
- Replaced the native triangle-descriptor best-candidate scan with a single-block parallel reduction.
- Preserved deterministic tie-breaking semantics:
  - higher candidate score wins;
  - lower candidate RMS wins for equal score;
  - lower candidate index wins for exact score/RMS ties.
- Exposed `best_reduction_mode=single_block_parallel_score_rms_index` from native bindings through `glass_cuda.py`.
- Recorded the reduction mode in resident CUDA artifacts and warnings.
- Added focused tests for native single/batch registration results and resident artifact propagation.
- Updated Phase 2 gate documentation and algorithm source ledger.

## Commands run
- Native build:
  - `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_triangle_descriptor_similarity_batch_matches_single_fits tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- 200-light A/B resident CUDA runs:
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_62_200\parallel_best_a_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
  - same command with `--out C:\glass_runs\phase2_s2_gate_62_200\parallel_best_b_20260601`
- Determinism/output audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_62_200\parallel_best_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_62_200\parallel_best_b_20260601 --out C:\glass_runs\phase2_s2_gate_62_200\resident_determinism_parallel_best_a_vs_b.json --markdown C:\glass_runs\phase2_s2_gate_62_200\resident_determinism_parallel_best_a_vs_b.md --fail-on-mismatch`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test results
- Native build: passed (`ninja: no work to do`)
- Focused tests: passed (`2 passed in 2.31s`)
- Determinism/output audit: passed
  - frame signature differences: 0
  - registration differences: 0
  - frame accounting differences: 0
  - output differences: 0
- Ruff: passed (`All checks passed!`)
- Full pytest: passed (`269 passed in 11.35s`)

## 200-light timing results
- Gate61 A/B average total elapsed: 13.400505 s
- Gate62 A/B average total elapsed: 12.594809 s
- Total speedup vs Gate61: 1.0640x
- Gate61 A/B average registration/warp: 2.567942 s
- Gate62 A/B average registration/warp: 1.791371 s
- Registration/warp speedup vs Gate61: 1.4335x
- Gate61 A/B average triangle descriptor fit: 0.822729 s
- Gate62 A/B average triangle descriptor fit: 0.063067 s
- Descriptor fit speedup vs Gate61: 13.0452x
- Gate62 average native descriptor kernel sync: 0.037106 s

### Gate62 run A
- Output: `C:\glass_runs\phase2_s2_gate_62_200\parallel_best_a_20260601`
- Total elapsed: 12.686905 s
- Resident registration/warp: 1.785096 s
- Triangle descriptor fit: 0.061963 s
- Native descriptor total: 0.058580 s
- Native descriptor kernel sync: 0.037001 s
- Native moving upload: 0.003744 s
- Native output download: 0.014632 s

### Gate62 run B
- Output: `C:\glass_runs\phase2_s2_gate_62_200\parallel_best_b_20260601`
- Total elapsed: 12.502714 s
- Resident registration/warp: 1.797647 s
- Triangle descriptor fit: 0.064171 s
- Native descriptor total: 0.060187 s
- Native descriptor kernel sync: 0.037212 s
- Native moving upload: 0.004045 s
- Native output download: 0.014212 s

## CUDA availability
- CUDA backend: available
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Driver: 596.21

## Known limitations
- Candidate scoring still runs per moving frame. Gate62 only parallelizes the final best-candidate reduction inside each frame.
- Output download for descriptor fit is now a larger share of the remaining fit time after the best reduction optimization.
- Pixel refine remains the largest registration component after this gate.
- Full resident pipeline still depends on FITS decode and H2D overlap quality for end-to-end wall time.

## Next step
- Target the next dominant registration component: pixel refine and/or warp scheduling. The likely next useful gate is a batch pixel-refine reduction or a resident warp/pixel-refine fusion audit, while preserving deterministic signatures and A/B output equality.

## Clean-room compliance
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- Only GLASS source, generated GLASS artifacts, synthetic/focused tests, and user-provided benchmark data were used.
- Original input image directories were treated as read-only.
