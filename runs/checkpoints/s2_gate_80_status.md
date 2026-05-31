# S2 Gate 80 Status: Batched Resident Warp Matrix Upload

## Gate
- Gate: S2 Gate 80
- Name: Batched resident warp matrix upload
- Date: 2026-06-01
- Status: green

## Completed
- Replaced per-frame inverse-matrix host-to-device uploads in native resident
  matrix bilinear and Lanczos3 batch warp with one inverse preparation pass,
  one device inverse batch allocation, and one H2D upload per batch.
- Preserved the existing warp kernels, interpolation formulas, coverage
  accumulation, DQ semantics, accepted-frame decisions, and output pixels.
- Added native timing fields:
  - `inverse_upload_mode`
  - `inverse_prepare_s`
  - `inverse_batch_alloc_s`
  - `inverse_batch_bytes`
  - existing upload/enqueue/sync/total timings remain intact
- Surfaced the new inverse-batch timing and byte fields in
  `resident_artifacts.json` under `resident_registration`.
- Updated direct CUDA warp tests, resident CUDA artifact tests, Phase 2 gate
  documentation, and the algorithm source ledger.

## Commands Run
- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_warp_matches_cpu_reference tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_80_200\batched_inverse_warp_recipe_20260601 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-star-catalog-deterministic --resident-triangle-pixel-refine-coarse-stride 4 --resident-triangle-pixel-refine-final-stride 8 --resident-triangle-pixel-refine-fast-coarse --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps minimal --flat-floor 0.05 --exclude-frame-id LIGHT_H_0100 --exclude-frame-id LIGHT_H_0153 --exclude-frame-id LIGHT_H_0154 --exclude-frame-id LIGHT_H_0155 --exclude-frame-id LIGHT_H_0156 --exclude-frame-id LIGHT_H_0157 --exclude-frame-id LIGHT_H_0158 --resident-prefetch-frames 16 --resident-prefetch-workers 8 --resident-h2d-mode pinned_ring --resident-calibration-batch-frames 8 --resident-calibration-streams 4 --resident-calibration-wave-frames 2 --resident-calibration-release-mode callback_queue`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_80_200\batched_inverse_warp_recipe_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_80_200\compare_gate80_vs_gate70b.html --glass-time-seconds 12.181721900124103 --reference-time-seconds 12.200752399861813 --glass-label Gate80_batched_inverse_warp --reference-label Gate70_event_reuse_b --ignore-border-px 16`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_80_200\batched_inverse_warp_recipe_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_78_200\prefetch_sweep_20260601\pf16_pw8_b8_s4_w2_callback_queue\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_80_200\compare_gate80_vs_gate78_best.html --glass-time-seconds 12.181721900124103 --reference-time-seconds 12.229778400156647 --glass-label Gate80_batched_inverse_warp --reference-label Gate78_best --ignore-border-px 16`
- `.\.venv\Scripts\python.exe -c "import glass_cuda, json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices()}, indent=2))"`

## Test Results
- Focused CUDA warp/resident tests: 3 passed.
- Ruff: passed.
- Full pytest: 282 passed in 13.38 s.

## CUDA
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.
- CUDA Toolkit used for this build: 13.2.

## 200-Light Real Dataset Run
- Run path:
  `C:\glass_runs\phase2_s2_gate_80_200\batched_inverse_warp_recipe_20260601`
- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Recipe: same M38 H-alpha 200-light resident CUDA recipe used by Gate78 best:
  resident CUDA, pinned-ring H2D, similarity CUDA triangle registration,
  Lanczos3 resident warp, winsorized sigma rejection, no local normalization,
  minimal output maps, shared resident master cache, and seven known excluded
  light frames.
- Total elapsed: 12.181721900124103 s.
- Speed vs Gate70B 12.200752399861813 s: 1.0015622175496812x.
- Speed vs Gate78 best 12.229778400156647 s: 1.0039449677497608x.
- Light read/upload/calibration: 6.175733299925923 s.
- Light read wait wall time: 2.603307191748172 s.
- H2D/calibration/store: 2.7242223005741835 s.
- Native calibration total: 2.7130603000000004 s.
- Resident registration/warp: 1.4336228957399726 s.
- Resident integration: 0.3031716998666525 s.
- Input light frames: 200.
- Active frames: 193.
- Zero-weight frames: 7.

## Native Warp Timing
- Batch warp mode: `native_matrix_lanczos3_frames`.
- Batch warp timing model: `native_loop_batched_inverse_one_sync`.
- Batch warp frame count: 189.
- Batch warp fallback frame count: 3.
- Inverse upload mode: `single_device_batch`.
- Inverse prepare time: 0.0000583 s.
- Inverse batch allocation time: 0.000008 s.
- Inverse batch bytes: 6804.
- Inverse upload time: 0.0000147 s.
- Kernel enqueue time: 0.0007949 s.
- Device-copy enqueue time: 0.0014808 s.
- Final sync time: 0.4342982 s.
- Native batch total: 0.4367115 s.

## Result Comparison
- Gate80 vs Gate70B compare report:
  `C:\glass_runs\phase2_s2_gate_80_200\compare_gate80_vs_gate70b.html`
- Gate80 vs Gate70B JSON:
  `C:\glass_runs\phase2_s2_gate_80_200\compare_gate80_vs_gate70b.json`
- Gate80 vs Gate78 best compare report:
  `C:\glass_runs\phase2_s2_gate_80_200\compare_gate80_vs_gate78_best.html`
- Gate80 vs Gate78 best JSON:
  `C:\glass_runs\phase2_s2_gate_80_200\compare_gate80_vs_gate78_best.json`
- Shape match: true.
- Compared pixels after 16 px border ignore: 61139520.
- RMS diff: 0.0.
- Max absolute diff: 0.0.
- P99 absolute diff: 0.0.

## Interpretation
- The previous native batch warp ledger showed per-frame inverse upload as the
  apparent hotspot. Gate80 proves that the upload itself can be made
  negligible: 0.0000147 s for the whole batch.
- Most of the same wall time is now correctly attributed to the final warp
  synchronization, so the next meaningful optimization is not another matrix
  upload tweak. It should target multi-frame warp dispatch, stream scheduling,
  or a fused resident warp kernel that reduces per-frame kernel/copy
  serialization.
- The end-to-end improvement is small but positive on this dataset, and output
  identity is exact against Gate70B and Gate78 best.

## Known Limitations
- Gate80 still launches one warp kernel per frame and copies one reusable warp
  scratch buffer back into the resident frame stack per warped frame.
- The inverse batch is allocated per batch; this is small here, but a future
  resident scratch workspace can make it reusable.
- A first invalid benchmark command without the full resident-registration
  recipe produced a registration-off run at
  `C:\glass_runs\phase2_s2_gate_80_200\batched_inverse_warp_20260601`; it was
  not used for acceptance.

## Next Step
- S2-Gate 81 should target resident warp kernel/stream structure: either a
  true multi-frame matrix warp kernel, a reusable inverse-batch workspace, or a
  stream/CUDA-graph schedule that reduces per-frame launch/copy serialization.

## Clean-Room Compliance
- Compliant.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or
  reworked.
- The implementation uses GLASS-owned CUDA scheduling around GLASS warp kernels
  and GLASS-generated timing/compare artifacts only.
- Input image directories remain read-only.
