# S2-Gate 60 Status: Parallel Deterministic Resident Grid Top-K

## Gate

- Gate: S2-Gate 60
- Status: green
- Completed at: 2026-06-01 Asia/Shanghai

## Completed Work

- Added a deterministic one-block-per-cell CUDA grid top-k catalog kernel for
  the standard resident triangle-registration catalog path.
- Preserved the existing GLASS catalog ordering contract: flux descending, then
  y ascending, then x ascending.
- Kept the Gate58 serial deterministic per-cell path as the fallback for larger
  per-cell candidate budgets that would use excessive shared memory.
- Surfaced the optimized mode in native/Python artifacts as
  `deterministic_parallel_per_cell`.
- Updated resident CUDA tests to require the new deterministic top-k mode.
- Updated Phase 2 planning and algorithm-source documentation for this
  clean-room scheduling optimization.

## Commands Run

- Native CUDA build:
  - `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- Focused CUDA/resident tests:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke tests\test_resident_determinism.py`
- Real 200-light resident CUDA run A:
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_60_200\parallel_grid_a_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- Real 200-light resident CUDA run B:
  - same command as run A, with `--out C:\glass_runs\phase2_s2_gate_60_200\parallel_grid_b_20260601`
- Resident determinism and output-pixel audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_60_200\parallel_grid_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_60_200\parallel_grid_b_20260601 --out C:\glass_runs\phase2_s2_gate_60_200\resident_determinism_parallel_a_vs_b.json --markdown C:\glass_runs\phase2_s2_gate_60_200\resident_determinism_parallel_a_vs_b.md --fail-on-mismatch`
- CUDA device probe:
  - `.\.venv\Scripts\python.exe -c "import json, glass_cuda; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native CUDA build: passed, `ninja: no work to do`.
- Focused CUDA/resident tests: passed, `8 passed in 2.42s`.
- Ruff: passed, `All checks passed!`.
- Full pytest: passed, `269 passed in 11.60s`.

## Real 200-Light Result

- Baseline for comparison: S2-Gate58 run
  `C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_c_20260601`.
- Gate58 total elapsed: 20.466891599819064 s.
- Gate58 `resident_registration_warp`: 9.454468900337815 s.
- Gate58 `triangle_catalog_native_total_s`: 7.0875667 s.
- Gate58 top-k mode: `deterministic_serial_per_cell`.

- Gate60 run A:
  - Run path: `C:\glass_runs\phase2_s2_gate_60_200\parallel_grid_a_20260601`.
  - Total elapsed: 13.565146599896252 s.
  - `light_h2d_calibrate_store`: 2.870661701541394 s.
  - `resident_registration_warp`: 2.551808001473546 s.
  - `resident_integration`: 0.3289978001266718 s.
  - `triangle_catalog_native_total_s`: 0.219214 s.
  - Top-k mode: `deterministic_parallel_per_cell`.
- Gate60 run B:
  - Run path: `C:\glass_runs\phase2_s2_gate_60_200\parallel_grid_b_20260601`.
  - Total elapsed: 13.308597500436008 s.
  - `light_h2d_calibrate_store`: 2.809015197213739 s.
  - `resident_registration_warp`: 2.5539593980647624 s.
  - `resident_integration`: 0.3063433999195695 s.
  - `triangle_catalog_native_total_s`: 0.2196618 s.
  - Top-k mode: `deterministic_parallel_per_cell`.

- Gate60 average total elapsed: 13.43687205016613 s.
- Total speedup versus Gate58 deterministic serial catalog: 1.5231886947651643x.
- Total elapsed reduction: 34.34825222661111 percent.
- Registration/warp speedup: 3.7034467732285417x.
- Registration/warp reduction: 72.99812684689313 percent.
- Native catalog total speedup: 32.29873554203718x.
- Native catalog total reduction: 96.90390356396928 percent.

## Determinism Audit

- Audit JSON:
  - `C:\glass_runs\phase2_s2_gate_60_200\resident_determinism_parallel_a_vs_b.json`
- Audit Markdown:
  - `C:\glass_runs\phase2_s2_gate_60_200\resident_determinism_parallel_a_vs_b.md`
- Audit result: pass.
- Artifact differences: 0.
- Frame signature differences: 0.
- Registration differences: 0.
- Frame accounting differences: 0.
- Output pixel/map differences: 0.

## CUDA Availability

- CUDA available: yes.
- Device:
  - NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
  - Compute capability: 12.0.
  - VRAM: 97886 MiB.
  - Multiprocessors: 188.
  - Driver: 596.21.

## Known Limitations

- The optimized deterministic path is currently enabled for
  `candidates_per_cell <= 16`; larger per-cell budgets use the Gate58 serial
  deterministic fallback.
- The resident catalog timing model is still `per_frame_launch_sync_download`;
  later gates can reduce host/native round trips by batching more of descriptor
  generation and candidate scoring.
- The 200-light validation used `--resident-output-maps minimal`, so optional
  maps absent from both runs were not written.
- Total wall time is now less dominated by deterministic catalog extraction;
  the next major targets are resident registration orchestration and overlapped
  read/decode/H2D scheduling.

## Next Step

- Continue resident registration hardening by reducing per-frame host/native
  orchestration around star catalog, descriptor, candidate scoring, and warp
  scheduling while keeping this Gate60 output-pixel determinism audit as a
  regression guard.

## Clean-Room Compliance

- No PixInsight or WBPP/PJSR source was read or used.
- Only GLASS source, tests, generated artifacts, and local benchmark outputs
  were inspected or modified.
- Input image directories were treated as read-only.
