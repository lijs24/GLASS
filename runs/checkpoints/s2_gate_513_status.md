# S2-Gate 513 Status: Resident Lanczos3 NaN Footprint Parity

Gate: S2-Gate 513

## Result

Passed.

This gate fixes a concrete resident CUDA semantic mismatch found while
continuing the Gate512 warp/integration handoff work. Single-frame Lanczos3 warp
and fused matrix-warped integration skipped non-finite source samples inside the
6x6 Lanczos footprint, but resident batch Lanczos3 warp did not. Gate513 aligns
the batch path with the single/fused semantics and proves the default 200-light
stack output remains bitwise stable.

## Completed

- Updated `cpp/cuda/warp_kernels.cu` so resident batch Lanczos3 warp skips
  non-finite footprint samples in both the generic and unclamped kernels.
- Kept `cpp/cuda/integration_kernels.cu` fused Lanczos3 sampling on the same
  skip-non-finite rule.
- Added `clamping_threshold` to fused matrix-warped integration native timing in
  `cpp/src/native_bindings.cpp`.
- Passed `clamping_threshold` through the Python wrapper timing in
  `src/glass_cuda.py`.
- Added a CUDA test that compares fused integration, resident batch
  warp-then-integrate, and single-warp reference behavior for unclamped
  Lanczos3 with NaNs inside the source footprint.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.
- Saved real-run summary at
  `runs/checkpoints/s2_gate_513_lanczos_nan_parity_summary.json`.

## Commands

- `cmake --build build --config Release -j 1` inside the VS BuildTools
  developer environment.
- `python -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_fused_and_batch_lanczos3_unclamped_skip_nan_footprint tests/test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_mean_lanczos3_matches_warp_then_integrate tests/test_cuda_resident_stack.py::test_resident_stack_fused_matrix_warped_winsorized_lanczos3_matches_warp_then_integrate tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_records_unclamped_fast_path`
- `python -m pytest -q tests/test_cuda_resident_stack.py tests/test_gpu_warp_vs_cpu.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `python -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_fused_matrix_matches_stack_dispatch tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_selects_verified_bilinear_fused_path tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_fused_matrix_dispatch_matches_external_stack tests/test_resident_cuda_run.py::test_cli_resident_cuda_fused_minimal_output_maps_skip_diagnostic_downloads`
- `python -m ruff check src\glass_cuda.py tests\test_cuda_resident_stack.py`
- `python -m pytest -q`
- `glass doctor`
- `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856\shared_master_cache --out C:\glass_runs\phase2_s2_gate513_lanczos_nan_parity\runs_20260623_070538\stack_default`
- `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856\shared_master_cache --resident-integration-dispatch fused_matrix --out C:\glass_runs\phase2_s2_gate513_lanczos_nan_parity\runs_20260623_070538\fused_matrix`

## Test Result

- Focused CUDA NaN/fused/warp tests: `5 passed`.
- Focused resident stack + warp tests: `64 passed`.
- Focused fused CLI tests: `4 passed`.
- Full test suite: `1156 passed in 41.75 s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- CUDA native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Real 200-Light Validation

Run root:

`C:\glass_runs\phase2_s2_gate513_lanczos_nan_parity\runs_20260623_070538`

Default stack:

- Runtime: `6.643055199994706 s`.
- Resident integration time: `0.17246229999000207 s`.
- Registration component: `1.9265035004998685 s`.
- Native warp total: `0.4686301 s`.
- Warp chunk frames/count: `8` / `24`.

Default stack vs Gate511:

- Bitwise equal: yes.
- RMS: `0.0`.
- Max abs: `0.0`.
- P99 abs: `0.0`.
- Pixels above `1e-6`: `0`.

Explicit fused_matrix probe:

- Runtime: `8.640848300012294 s`.
- Native fused integration total: `2.3826089 s`.
- `clamping_threshold=-1.0`.
- `interpolation=lanczos3`.
- `rejection=winsorized_sigma`.

Fused_matrix vs Gate513 stack:

- Bitwise equal: no.
- RMS: `0.46078309416770935`.
- Max abs: `562.0709228515625`.
- P99 abs: `0.0`.
- Pixels above `1e-6`: `151149`.

Decision:

- Keep default dispatch on `stack` for Lanczos3 + winsorized sigma.
- Do not promote `fused_matrix` for the real 200-light science path.
- Continue the next gate on the remaining fused-matrix parity gap or another
  bitwise-safe warp/integration handoff.

## Artifacts

- `runs/checkpoints/s2_gate_513_status.md`
- `runs/checkpoints/s2_gate_513_lanczos_nan_parity_summary.json`
- `C:\glass_runs\phase2_s2_gate513_lanczos_nan_parity\runs_20260623_070538\stack_default`
- `C:\glass_runs\phase2_s2_gate513_lanczos_nan_parity\runs_20260623_070538\fused_matrix`

## Known Limitations

- Gate513 does not make fused_matrix production-ready for Lanczos3 winsorized
  integration.
- The real-data fused_matrix mismatch is not explained by the NaN footprint
  mismatch fixed here; it remains a separate parity target.
- Default real 200-light runtime is within normal run-to-run variance and not a
  new speed improvement.

## Next Step

Investigate the remaining explicit fused_matrix parity gap by capturing a small
set of pixels that differ between fused and stack, then replaying their
per-frame warped samples and rejection decisions. The next gate should target
the exact fused/stack rejection or sampling divergence before considering any
fused_matrix promotion.

## Clean-Room Compliance

Passed. This gate uses only GLASS code, GLASS tests, GLASS-generated timing and
output artifacts, and user-provided benchmark data. It does not inspect,
summarize, copy, or rework external proprietary implementation source.
