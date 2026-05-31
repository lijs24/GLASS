# S2-Gate 58 Status: Deterministic Resident Grid Top-K Catalog Mode

## Gate

- Gate: S2-Gate 58
- Status: green
- Completed at: 2026-06-01 Asia/Shanghai

## Completed Work

- Added opt-in deterministic resident grid top-k star catalog mode.
- Added a deterministic serial-per-cell CUDA candidate scan for grid top-k + NMS.
- Wired deterministic resident catalog selection through:
  - native `ResidentCalibratedStack` single-frame and batch methods
  - `src/glass_cuda.py` wrappers
  - resident CUDA engine options and artifact fields
  - `glass run` and `glass audit` CLI flags
- Fixed the resident batch catalog path so `--resident-star-catalog-deterministic`
  actually calls the deterministic CUDA launch for moving-frame batches.
- Updated resident determinism audit comparison to treat matching `NaN`
  diagnostics as equal, avoiding false diffs for failed or excluded frames.
- Updated Phase 2 planning docs with the S2-Gate 58 scope and validation rule.

## Commands Run

- Native build:
  - `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke`
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_determinism.py tests\test_cuda_resident_stack.py::test_resident_stack_grid_star_catalog_batch_reports_native_timing tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_cli_smoke.py::test_cli_audit_resident_cuda_smoke`
- Real 200-light repeated resident CUDA run:
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_c_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_d_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- Real determinism audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_c_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_d_20260601 --out C:\glass_runs\phase2_s2_gate_58_200\resident_determinism_deterministic_c_vs_d_fixed.json --markdown C:\glass_runs\phase2_s2_gate_58_200\resident_determinism_deterministic_c_vs_d_fixed.md --fail-on-mismatch`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`
- CUDA probe:
  - `.\.venv\Scripts\python.exe -c "import glass_cuda as g; print(g.cuda_available()); print(g.list_devices())"`

## Test Results

- Native build: passed.
- Focused tests: passed, `7 passed in 0.44s` for the final focused set.
- Ruff: passed, `All checks passed!`.
- Full pytest: passed, `268 passed in 11.42s`.

## Real 200-Light Result

- Baseline run: `C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_c_20260601`
- Candidate run: `C:\glass_runs\phase2_s2_gate_58_200\deterministic_grid_d_20260601`
- Determinism audit JSON:
  - `C:\glass_runs\phase2_s2_gate_58_200\resident_determinism_deterministic_c_vs_d_fixed.json`
- Determinism audit Markdown:
  - `C:\glass_runs\phase2_s2_gate_58_200\resident_determinism_deterministic_c_vs_d_fixed.md`
- Audit result: pass.
- Artifact differences: 0.
- Frame signature differences: 0.
- Registration differences: 0.
- Frame accounting differences: 0.
- Total elapsed:
  - Baseline: 20.466891599819064 s.
  - Candidate: 20.220896600279957 s.
- Representative timing from baseline artifact:
  - light H2D + calibration store: 2.8449381003156304 s.
  - resident registration + warp: 9.454468900337815 s.
  - resident integration: 0.31271969992667437 s.
- Deterministic catalog mode reported by artifact:
  - `deterministic_serial_per_cell`.

## CUDA Availability

- CUDA available: yes.
- Device 0:
  - NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
  - Compute capability: 12.0.
  - VRAM: 97886 MiB.
  - Driver: 596.21.
  - Native backend: true.

## Known Limitations

- Deterministic grid top-k is opt-in. The default lock-based path remains
  available for throughput comparisons.
- Deterministic serial-per-cell top-k removes catalog scheduling drift, but it
  is not yet the final high-throughput resident registration design.
- Registration component timing still includes cumulative native timing terms;
  wall-time totals remain the authoritative benchmark numbers.

## Next Step

- Continue with the next Phase 2 gate by optimizing resident registration
  throughput now that repeated real-data catalog, descriptor, fit, registration,
  and frame-accounting outputs are reproducible.

## Clean-Room Compliance

- No PixInsight or WBPP/PJSR source was read or used.
- Only GLASS source, tests, generated artifacts, and local benchmark outputs
  were inspected or modified.
- Input image directories were treated as read-only.
