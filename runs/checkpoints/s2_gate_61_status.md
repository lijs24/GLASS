# S2-Gate 61 Status: Resident Descriptor Fit Timing Ledger

## Gate

- Gate: S2-Gate 61
- Status: green
- Completed at: 2026-06-01 Asia/Shanghai

## Completed Work

- Added native timing fields to the resident CUDA triangle descriptor batch-fit
  path.
- The batch-fit ledger now reports:
  - host batch preparation time
  - reference allocation and upload time
  - reusable workspace allocation time
  - moving-frame upload time
  - descriptor-fit kernel synchronization time
  - output download time
  - per-frame native fit total time
- Surfaced the timing model as `per_frame_reused_buffers_sync_timed`.
- Passed the ledger through `src/glass_cuda.py`, resident artifacts, fine timing
  components, and per-frame registration warnings.
- Added tests for native batch-result timing fields and resident artifact timing
  fields.
- Updated Phase 2 planning and algorithm-source documentation.

## Commands Run

- Native CUDA build:
  - `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe" --build build\native-cuda-glass --target _glass_cuda_native'`
- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py::test_gpu_triangle_descriptor_similarity_batch_matches_single_fits tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- Lint:
  - `.\.venv\Scripts\python.exe -m ruff check .`
- Real 200-light resident CUDA run A:
  - `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_61_200\descriptor_timing_a_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158`
- Real 200-light resident CUDA run B:
  - same command as run A, with `--out C:\glass_runs\phase2_s2_gate_61_200\descriptor_timing_b_20260601`
- Resident determinism and output-pixel audit:
  - `.\.venv\Scripts\glass.exe resident-determinism --baseline-run C:\glass_runs\phase2_s2_gate_61_200\descriptor_timing_a_20260601 --candidate-run C:\glass_runs\phase2_s2_gate_61_200\descriptor_timing_b_20260601 --out C:\glass_runs\phase2_s2_gate_61_200\resident_determinism_descriptor_timing_a_vs_b.json --markdown C:\glass_runs\phase2_s2_gate_61_200\resident_determinism_descriptor_timing_a_vs_b.md --fail-on-mismatch`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Native CUDA build: passed.
- Focused tests: passed, `2 passed in 0.30s`.
- Ruff: passed, `All checks passed!`.
- Full pytest: passed, `269 passed in 11.56s`.

## Real 200-Light Result

- Gate61 run A:
  - Run path: `C:\glass_runs\phase2_s2_gate_61_200\descriptor_timing_a_20260601`.
  - Total elapsed: 13.394699700176716 s.
  - `resident_registration_warp`: 2.5646675997413695 s.
  - `triangle_descriptor_fit`: 0.8226609001867473 s.
  - Native descriptor-fit total: 0.8175938 s.
  - Native descriptor-fit kernel sync: 0.7956327 s.
  - Native moving upload: 0.0043655 s.
  - Native output download: 0.0141039 s.
- Gate61 run B:
  - Run path: `C:\glass_runs\phase2_s2_gate_61_200\descriptor_timing_b_20260601`.
  - Total elapsed: 13.406309800222516 s.
  - `resident_registration_warp`: 2.5712160947732627 s.
  - `triangle_descriptor_fit`: 0.82279650028795 s.
  - Native descriptor-fit total: 0.8184078 s.
  - Native descriptor-fit kernel sync: 0.7972991 s.
  - Native moving upload: 0.0039732 s.
  - Native output download: 0.0137965 s.
- Descriptor-fit bottleneck conclusion:
  - Kernel synchronization dominates the descriptor-fit batch path.
  - Moving upload and output download are small compared with candidate scoring
    kernel time.
  - The next optimization should target candidate scoring kernels or true
    multi-frame device-side batch output before spending time on descriptor-fit
    transfer tweaks.

## Determinism Audit

- Audit JSON:
  - `C:\glass_runs\phase2_s2_gate_61_200\resident_determinism_descriptor_timing_a_vs_b.json`
- Audit Markdown:
  - `C:\glass_runs\phase2_s2_gate_61_200\resident_determinism_descriptor_timing_a_vs_b.md`
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

- Timing fields are host steady-clock measurements around synchronous CUDA
  calls. They are useful for bottleneck attribution but are not CUDA-event kernel
  timings.
- The descriptor-fit batch implementation still launches and synchronizes one
  fit per moving frame while reusing buffers.
- The 200-light validation used `--resident-output-maps minimal`, so optional
  maps absent from both runs were not written.

## Next Step

- Implement a true resident descriptor-fit batch output path or reduce the
  descriptor candidate scoring kernel cost. Gate61 shows this should matter more
  than transfer optimization inside descriptor fit.

## Clean-Room Compliance

- No PixInsight or WBPP/PJSR source was read or used.
- Only GLASS source, tests, generated artifacts, and local benchmark outputs
  were inspected or modified.
- Input image directories were treated as read-only.
