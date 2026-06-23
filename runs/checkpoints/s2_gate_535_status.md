# S2-Gate 535 Status: Resident FITS Header Spec Cache Reuse

## Gate

S2-Gate 535

## Completed

- Continued the Phase 2 mainline I/O + upload + calibration optimization.
- Added `native_u16_gpu_fits_eligibility_with_spec()` so guarded auto mode can
  keep the FITS `SimpleFitsImageSpec` parsed during eligibility checks.
- Reused that spec cache in `_LightPrefetcher` and `_read_light_timed()` for
  the `native_u16_gpu` resident path, avoiding a second FITS primary-header
  parse for every light frame.
- Reused pre-parsed specs in the resident master raw-u16 cache builder.
- Recorded `fits_header_spec_cache_enabled`,
  `fits_header_spec_cache_frame_count`, and
  `fits_header_spec_cache_hit_count` in resident I/O artifacts.

## Commands Run

- `python -m compileall -q src\glass\io\fits_fast.py src\glass\engine\resident_cuda.py`
- `.venv\Scripts\python.exe -m pytest -q tests/test_fits_io.py::test_native_u16_raw_fits_reader_reads_into_pinned_output tests/test_resident_cuda_run.py::test_light_prefetcher_counts_pinned_ring_inflight_slots tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto`
- `.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate535_header_spec_cache\runs_20260623_131656\gate535_spec_cache_timed --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_master_stack_engine.py::test_resident_matching_master_cache_prefers_raw_u16_gpu_decode tests/test_fits_io.py::test_native_u16_raw_fits_reader_reads_into_pinned_output tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_selects_native_u16_gpu_for_compatible_group tests/test_resident_cuda_run.py::test_cli_resident_cuda_default_fits_read_mode_is_guarded_auto`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Initial full pytest exposed one stale monkeypatch signature in
  `tests/test_resident_master_stack_engine.py`; the fake raw reader was updated
  to accept the new optional `spec=` parameter.
- Focused regression after the fix: `4 passed in 0.56s`.
- Full pytest after the fix: `1175 passed in 42.58s`.

## Real 200-Light Results

- Baseline Gate534:
  `C:\glass_runs\phase2_s2_gate534_parallel_dq_final\runs_20260623_142500\parallel_dq_final_default`.
- Gate535 final:
  `C:\glass_runs\phase2_s2_gate535_header_spec_cache\runs_20260623_131656\gate535_spec_cache_timed`.
- Gate535 shell/internal: `5.264231 s` / `4.92039439996006 s`.
- External reference runtime retained from the accepted black-box benchmark:
  `1092.541 s`.
- Speedup: about `207.5x` by shell time and `222.0x` by internal GLASS timing.
- Header spec cache: enabled, `200/200` light frames hit the cache.
- Worker FITS open cumulative time: Gate534 `0.19557570023507698 s` to
  Gate535 `0.0202783 s`.
- Consumer read wait wall time: Gate534 `0.6459383995970711 s` to Gate535
  `0.6400352999917232 s`.

## Numerical Validation

- Compared Gate535 outputs against Gate534 outputs:
  - `resident_master_H.fits`: bitwise identical;
  - `resident_weight_map_H.fits`: bitwise identical;
  - `resident_coverage_map_H.fits`: bitwise identical;
  - `resident_low_rejection_map_H.fits`: bitwise identical;
  - `resident_high_rejection_map_H.fits`: bitwise identical;
  - `resident_dq_map_H.fits`: bitwise identical.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Disk/Cleanup

- C: had about 337 GB free before the gate.
- Removed the first temporary Gate535 trial run after the clean timed run was
  captured.

## Known Limits

- The spec cache is intentionally used only for the resident `native_u16_gpu`
  path selected by guarded auto. Explicit non-auto paths keep their prior
  behavior.
- The end-to-end timing change is small because the eliminated header work was
  already overlapped by prefetch. It still removes avoidable repeated metadata
  work and improves the I/O pipeline accounting.
- The next major gains remain deeper resident registration/warp batching and
  more aggressive read/decode/H2D overlap.

## Next

- Target resident registration/warp batching and Python orchestration in the
  light loop, using the same 200-light A/B and bitwise output checks.

## Clean-Room

- Compliant. This gate uses GLASS code, GLASS-generated artifacts, user-owned
  benchmark images, and prior user-generated black-box benchmark evidence only.
  It does not inspect or copy PixInsight/WBPP/PJSR source or modify input
  directories.
