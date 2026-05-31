# S2 Gate 81 Status

## Gate

S2-Gate 81: Opt-in chunked multi-frame resident matrix warp dispatch.

## Completed

- Added native CUDA batch matrix warp kernels that process a chunk of frames through a temporary output workspace, per-frame coverage bytes, a coverage reduction kernel, and a scatter kernel back into the resident stack.
- Added native Python bindings for chunked batch dispatch while preserving the Gate80 loop path as the default.
- Added `--resident-warp-batch-dispatch {loop,chunked}` for `glass run` and `glass audit`.
- Added resident artifact fields for dispatch mode, chunk count, workspace bytes, coverage bytes, output bytes, and kernel launch counts.
- Added focused CUDA tests for chunked bilinear and Lanczos batch warp numerical agreement, plus a default-dispatch regression test that keeps the loop path active by default.
- Updated Phase 2 hardening notes and algorithm source provenance.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m ruff check .`
- `git diff --check`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_warp_matches_cpu_reference tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_bilinear_batch_default_dispatch_is_loop tests\test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `.\.venv\Scripts\glass.exe run ... --resident-warp-batch-dispatch loop`
- `.\.venv\Scripts\glass.exe run ... --resident-warp-batch-dispatch chunked`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_81_200\default_loop_recipe_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_70_200\reused_calibration_events_b_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_81_200\compare_gate81_default_vs_gate70b.html --glass-time-seconds 12.323173000011593 --reference-time-seconds 12.200752399861813 --glass-label Gate81_default_loop --reference-label Gate70_event_reuse_b --ignore-border-px 16`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_81_200\chunked_dispatch_recipe_20260601\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_81_200\default_loop_recipe_20260601\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_81_200\compare_gate81_chunked_vs_default.html --glass-time-seconds 12.35075050033629 --reference-time-seconds 12.323173000011593 --glass-label Gate81_chunked --reference-label Gate81_default_loop --ignore-border-px 16`

## Test Results

- Native CUDA build: passed; target already up to date.
- Ruff: passed.
- Diff whitespace check: passed; only Git LF/CRLF warnings were reported.
- Focused CUDA/resident tests: `4 passed in 2.15s`.
- Full pytest: `283 passed in 12.06s`.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native backend: available.

## 200-Light Regression

Dataset: existing Phase 2 200-light recipe with 193 active H frames after registration/frame-accounting filtering.

Default Gate81 loop dispatch:

- Run: `C:\glass_runs\phase2_s2_gate_81_200\default_loop_recipe_20260601`
- Total elapsed: 12.323173000011593 s.
- `light_read_upload_calibrate`: 6.253033900167793 s.
- `light_read_wait_wall`: 2.75809090025723 s.
- `light_h2d_calibrate_store`: 2.6275920001789927 s.
- `resident_registration_warp`: 1.411145300604403 s.
- `resident_integration`: 0.3189507997594774 s.
- Dispatch: `loop`.
- Timing model: `native_loop_batched_inverse_one_sync`.
- Native warp total: 0.4348477 s.
- Native warp sync: 0.4317236 s.

Opt-in chunked dispatch:

- Run: `C:\glass_runs\phase2_s2_gate_81_200\chunked_dispatch_recipe_20260601`
- Total elapsed: 12.35075050033629 s.
- `light_read_upload_calibrate`: 6.258864399977028 s.
- `light_read_wait_wall`: 2.6149155981838703 s.
- `light_h2d_calibrate_store`: 2.7421818994916975 s.
- `resident_registration_warp`: 1.4732130039483309 s.
- `resident_integration`: 0.29404939990490675 s.
- Dispatch: `chunked`.
- Timing model: `native_chunked_batch_warp_scatter_one_sync`.
- Native warp total: 0.4924215 s.
- Native warp sync: 0.4885095 s.
- Chunk frames: 8.
- Chunk count: 24.
- Workspace bytes: 2466048352.
- Output bytes: 1972838400.
- Coverage bytes: 493209600.

Numerical comparisons:

- Gate81 default loop vs Gate70B: shape match true, compared pixels 61139520, RMS 0.0, max abs diff 0.0, p99 abs diff 0.0.
- Gate81 chunked vs Gate81 default loop: shape match true, compared pixels 61139520, RMS 0.0, max abs diff 0.0, p99 abs diff 0.0.

## Interpretation

The chunked path is numerically exact against the default loop path, but it is slower on the 200-light benchmark because the temporary output workspace, per-frame coverage storage, coverage reduction, and scatter step cost more than the saved launch/orchestration work. Therefore this gate keeps `loop` as the default dispatch and exposes `chunked` as an opt-in experimental mode for future fused warp/integration work.

## Known Limits

- Chunked dispatch currently writes temporary warped images and scatters them back; it is not the desired final fused resident warp/integration design.
- The 200-light benchmark total time has normal run-to-run variance, so Gate81 is judged by exact output agreement and keeping the default Gate80 dispatch unchanged.
- The invalid earlier Gate81 run without the common recipe is not used for acceptance.

## Next Step

Prefer a fused resident warp plus integration path, reusable batch workspace, or CUDA Graph/stream batching. Avoid making chunked scatter the default unless a future benchmark shows a clear speedup.

## Clean-Room Compliance

Compliant. This gate used only GLASS code, synthetic/focused tests, and user-generated GLASS benchmark artifacts. It did not read or copy official PixInsight/WBPP/PJSR source code and did not modify input image directories.
