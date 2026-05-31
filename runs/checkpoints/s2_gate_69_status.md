# S2-Gate 69 Status: Native Batch Matrix Warp Dispatch

## Gate

S2-Gate 69 - Native Batch Matrix Warp Dispatch.

## Completed

- Added native resident CUDA batch dispatch methods for matrix bilinear and Lanczos3 warp:
  - `ResidentCalibratedStack.apply_matrix_bilinear_frames(...)`
  - `ResidentCalibratedStack.apply_matrix_lanczos3_frames(...)`
- Added Python wrapper methods in `glass_cuda.ResidentCalibratedStack`.
- Updated resident triangle registration post-processing to batch non-translation refined matrices while keeping translation-only frames on the existing per-frame fast path.
- Added resident artifact fields for batch warp capability, frame counts, fallback counts, timing model, inverse upload, kernel enqueue, device copy enqueue, sync, and native total time.
- Added per-frame registration warnings that distinguish batch matrix warp from translation fallback.
- Added CUDA/CPU reference tests for native batch bilinear and Lanczos3 resident warp.
- Updated Phase 2 plan with S2-Gate 69.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m py_compile src\glass_cuda.py src\glass\engine\resident_cuda.py
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests\test_cuda_smoke.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_69_200\native_batch_matrix_warp_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_69_200\native_batch_matrix_warp_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_64_200\fast_coarse_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_69_200\compare_gate69_vs_gate64.html --glass-time-seconds 12.512505700346082 --reference-time-seconds 12.162676699925214 --glass-label Gate69_native_batch --reference-label Gate64_fast_coarse --ignore-border-px 16
```

## Test Results

- Ruff: `All checks passed!`.
- Focused CUDA/resident tests: `11 passed in 0.32s`.
- Full pytest: `273 passed in 11.55s`.
- Native CUDA build: succeeded; latest rebuild reported `ninja: no work to do`.
- 200-light real M38 H-alpha resident CUDA run: succeeded through integration.

## 200-Light Result

- Run output: `C:\glass_runs\phase2_s2_gate_69_200\native_batch_matrix_warp_20260601`
- Total elapsed: `12.512505700346082 s`.
- Completed stages: `master_calibration`, `resident_light_calibration`, `resident_registration`, `resident_integration`.
- Native batch warp mode: `native_matrix_lanczos3_frames`.
- Native batch timing model: `native_loop_single_scratch_one_sync`.
- Native batch warp frames: `189`.
- Translation/per-frame fallback frames: `3`.
- Native batch warp total: `0.4398755 s`.
- Native batch warp sync: `0.0022872 s`.
- Registration component accounted time: `2.3787037036321403 s`.
- Resident registration warp time: `1.409740699455142 s`.
- I/O + upload + calibration path: `6.212004499975592 s`.
- Integration time: `0.2946762996725738 s`.

## Comparison

- Compared Gate69 master against Gate64 fast-coarse master:
  - Report: `C:\glass_runs\phase2_s2_gate_69_200\compare_gate69_vs_gate64.html`
  - Shape match: true.
  - Ignored border: 16 px.
  - RMS difference: `0`.
  - Max absolute difference: `0`.
  - Gate69 vs Gate64 timing ratio: `0.972041651065x` relative to Gate64, so this gate is correctness/evidence plumbing rather than a net runtime win.

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- The native batch method still loops over frames inside C++ with one shared scratch buffer and one final synchronization. It removes Python per-frame orchestration from matrix warp application, but it does not yet launch a single multi-frame CUDA kernel.
- Real 200-light timing remained essentially flat versus Gate64 because the dominant costs are still I/O/upload/calibration and earlier registration components, not the final matrix warp dispatch alone.
- Translation-only matrices intentionally remain on the existing translation fallback path because that path is already specialized.
- The batch timing model is now auditable, but further optimization needs multi-frame kernels or stream/CUDA Graph scheduling.

## Next Step

S2-Gate 70 should target the real bottleneck: multi-buffer I/O + pinned H2D + calibration overlap and/or a true multi-frame registration kernel path. The 200-light profile says the most important remaining wall-clock target is the `light_read_upload_calibrate` path at about `6.21 s`, followed by registration catalog/refine work.

## Clean-Room

Compliant. This gate only changes GLASS native CUDA and resident scheduling code, tests against GLASS CPU references, and uses GLASS-generated artifacts plus user-provided image data as black-box inputs. It does not read, copy, summarize, or rework PixInsight/WBPP implementation source.
