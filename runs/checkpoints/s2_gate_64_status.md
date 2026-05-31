# S2-Gate64 Status - Explicit Fast-Coarse Pixel Refinement

## Gate
- Gate: S2-Gate64
- Name: Explicit Fast-Coarse Pixel Refinement
- Status: passed
- Date: 2026-06-01 Asia/Shanghai

## Completed content
- Added an explicit `--resident-triangle-pixel-refine-fast-coarse` mode for resident CUDA triangle registration.
- The mode raises the coarse pixel-refine sample stride to at least the final sample stride.
- The default conservative path is unchanged.
- The run artifact now records:
  - requested coarse stride
  - requested final stride
  - effective coarse stride
  - whether fast-coarse was enabled
  - whether the coarse stride was adjusted
  - fast-coarse mode name
  - existing pixel-refine workload counts, timings, and throughput
- Per-frame registration warnings now report the same fast-coarse policy.
- Added CLI support for both `glass run` and `glass audit`.
- Updated focused tests, Phase 2 gate documentation, and the algorithm source ledger.

## Commands run
- Probe using existing coarse stride controls:
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_64_probe\coarse_stride8_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 8 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- Focused tests and help:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
  - `.\.venv\Scripts\glass.exe run --help`
  - `.\.venv\Scripts\glass.exe audit --help`
- 200-light fast-coarse A/B resident CUDA runs:
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
  - same command with `--out C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_b_20260601`
- Fast-coarse A/B strict determinism/output audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_b_20260601 --out C:\glass_runs\phase2_s2_gate_64_200\resident_determinism_fast_coarse_a_vs_b.json --markdown C:\glass_runs\phase2_s2_gate_64_200\resident_determinism_fast_coarse_a_vs_b.md --fail-on-mismatch`
- Conservative-vs-fast drift audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_63_200\pixel_refine_workload_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601 --out C:\glass_runs\phase2_s2_gate_64_200\resident_determinism_gate63_vs_fast_coarse.json --markdown C:\glass_runs\phase2_s2_gate_64_200\resident_determinism_gate63_vs_fast_coarse.md`
- Numeric output drift summary:
  - wrote `C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_vs_gate63_numeric_drift.json`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test results
- Focused resident CUDA triangle-registration test: passed (`1 passed in 0.37s`)
- `glass run --help`: passed and includes `--resident-triangle-pixel-refine-fast-coarse`
- `glass audit --help`: passed and includes `--resident-triangle-pixel-refine-fast-coarse`
- Fast-coarse A/B determinism/output audit: passed
  - frame signature differences: 0
  - registration differences: 0
  - frame accounting differences: 0
  - output differences: 0
- Ruff: passed (`All checks passed!`)
- Full pytest: passed (`269 passed in 11.27s`)

## 200-light timing results
- Gate63 conservative A/B average total elapsed: 12.776409 s
- Gate64 fast-coarse A/B average total elapsed: 12.206036 s
- Total speedup vs Gate63: 1.0467x
- Gate63 conservative A/B average registration/warp: 1.785792 s
- Gate64 fast-coarse A/B average registration/warp: 1.415803 s
- Registration/warp speedup vs Gate63: 1.2613x
- Gate63 conservative A/B average pixel refine: 0.893831 s
- Gate64 fast-coarse A/B average pixel refine: 0.524737 s
- Pixel-refine speedup vs Gate63: 1.7034x
- Gate63 conservative A/B average coarse metric: 0.681170 s
- Gate64 fast-coarse A/B average coarse metric: 0.302886 s
- Coarse metric speedup vs Gate63: 2.2489x

### Gate64 run A
- Output: `C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_a_20260601`
- Total elapsed: 12.249395 s
- Resident registration/warp: 1.418799 s
- Triangle pixel refine: 0.528623 s
- Native coarse metric: 0.304341 s
- Native fine metric: 0.219114 s
- Requested coarse stride: 4
- Effective coarse stride: 8
- Final stride: 8
- Coarse candidate sample evaluations: 14985907200

### Gate64 run B
- Output: `C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_b_20260601`
- Total elapsed: 12.162677 s
- Resident registration/warp: 1.412807 s
- Triangle pixel refine: 0.520851 s
- Native coarse metric: 0.301431 s
- Native fine metric: 0.213938 s
- Requested coarse stride: 4
- Effective coarse stride: 8
- Final stride: 8
- Coarse candidate sample evaluations: 14985907200

## Conservative-vs-fast drift note
- Fast-coarse is not bit-exact relative to Gate63 conservative sampling.
- Gate63 vs Gate64 strict audit:
  - frame signature differences: 0
  - registration differences: 64
  - frame accounting differences: 0
  - output differences: 1
- Master numeric drift summary:
  - pixels compared: 61651200
  - mean absolute difference: 0.642260 ADU
  - median absolute difference: 0.417107 ADU
  - RMS difference: 3.751400 ADU
  - p95 absolute difference: 1.489120 ADU
  - p99 absolute difference: 3.408920 ADU
  - max absolute difference: 1836.101562 ADU
  - baseline std: 314.820862 ADU
  - relative RMS to baseline std: 0.011916

## CUDA availability
- CUDA backend: available
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Multiprocessors: 188
- Driver: 596.21

## Known limitations
- Fast-coarse is explicitly a performance/quality tradeoff, not a conservative replacement.
- It changes subpixel matrices for some frames and therefore changes final output pixels.
- It should remain opt-in until compared against the external reference and broader datasets.
- The current mode only raises coarse stride to the final stride; it does not yet adapt from image quality, FWHM, star density, or measured drift.

## Next step
- Add a first-class numerical drift/quality report for conservative-vs-fast resident runs, then evaluate whether fast-coarse can become an audited preset for high-throughput 200-light benchmarks.
- Longer term: reduce pixel-refine coarse work without changing sampling semantics, likely by moving coarse candidate preselection or multiresolution scoring onto the GPU.

## Clean-room compliance
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- Only GLASS source, generated GLASS artifacts, tests, and user-provided benchmark data were used.
- Original input image directories were treated as read-only.
