# S2-Gate 509 Status: Specialized Unclamped Lanczos3 Batch Warp

## Gate

S2-Gate 509

## Completed Content

- Continued the Phase 2 mainline resident registration/warp optimization path.
- Added a dedicated batch Lanczos3 CUDA warp kernel for the default unclamped
  path (`clamping_threshold < 0`):
  - clamped Lanczos3 continues to use the generic runtime-clamp kernel;
  - unclamped Lanczos3 omits runtime clamp branching and local min/max state;
  - interpolation weight calculation order, fill behavior, scatter, matrices,
    rejection, integration, and master pixels are unchanged.
- Added native/resident artifact fields:
  - `lanczos3_clamp_path`;
  - `triangle_warp_batch_native_lanczos3_clamp_path`.
- Added focused CUDA and CLI tests proving clamped and unclamped dispatch
  contracts.
- Ran native build, ruff, focused tests, full pytest, CUDA doctor, and a real
  200-light candidate/repeat A/B.

## Changed Files

- `cpp/cuda/warp_kernels.cu`
- `cpp/src/native_bindings.cpp`
- `src/glass/engine/resident_cuda.py`
- `tests/test_gpu_warp_vs_cpu.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `runs/checkpoints/s2_gate_509_status.md`

## Commands Run

- `cmd /c "VsDevCmd.bat -arch=x64 && cmake --build build --config Release -j 1"`
- `python -m ruff check src\glass\engine\resident_cuda.py tests\test_gpu_warp_vs_cpu.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_warp_matches_cpu_reference tests/test_gpu_warp_vs_cpu.py::test_resident_stack_matrix_lanczos3_batch_records_unclamped_fast_path tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack`
- `python -m pytest -q`
- `glass doctor`
- Real 200-light run command, executed for `candidate` and `repeat`:

```powershell
glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --backend cuda --memory-mode resident --until-stage integration `
  --local-normalization off --integration-rejection winsorized_sigma `
  --integration-weighting none --flat-floor 0.05 `
  --resident-registration similarity_cuda_triangle `
  --resident-star-threshold 350 --resident-star-max-candidates 48 `
  --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 `
  --resident-warp-interpolation lanczos3 `
  --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal `
  --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache `
  --out <candidate-or-repeat>
```

- External-reference compare:

```powershell
glass compare `
  --glass C:\glass_runs\phase2_s2_gate509_lanczos_unclamped_specialized_ab_real\runs_20260623_062926\repeat\integration\resident_master_H.fits `
  --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf `
  --out C:\glass_runs\phase2_s2_gate509_lanczos_unclamped_specialized_ab_real\runs_20260623_062926\compare_vs_wbpp_fastintegration_scaled_coverage190.html `
  --glass-time-seconds 6.619877799996175 `
  --reference-time-seconds 1092.541 `
  --glass-label GLASS-Gate509-resident-minimal `
  --reference-label PixInsight-WBPP-fastIntegration `
  --glass-scale 8.764434957115609e-06 `
  --glass-offset 0.0006274500691899127 `
  --glass-coverage-map C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_coverage_map_H.fits `
  --min-coverage 190
```

## Test Results

- Native build: passed.
- Ruff: passed.
- Focused CUDA/resident tests: `3 passed in 1.10 s`.
- Full pytest: `1153 passed in 42.05 s`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`.

## Real 200-Light Results

Run root:

`C:\glass_runs\phase2_s2_gate509_lanczos_unclamped_specialized_ab_real\runs_20260623_062926`

Runtime:

- Gate509 candidate: `6.640441200055648 s`.
- Gate509 repeat: `6.619877799996175 s`.
- Gate508 repeat baseline: `6.605046200042125 s`.
- WBPP black-box fastIntegration reference: `1092.541 s`.

Artifact contract:

- `triangle_warp_batch_native_lanczos3_clamping_enabled=false`.
- `triangle_warp_batch_native_lanczos3_clamp_path=unclamped_specialized`.
- `triangle_warp_batch_native_warp_kernel_launches=24`.
- `triangle_warp_batch_native_chunk_count=24`.
- `triangle_warp_batch_native_chunk_frames=8`.
- Existing Gate508 catalog contract remains:
  `triangle_catalog_timing_model=batch_multistream_bulk_download_centroid_global_mean_fused_sync`,
  `triangle_catalog_sync_phase_count=2`.

Component timing:

- Gate509 candidate `triangle_warp_native_batch`: `0.4619148 s`.
- Gate509 candidate `triangle_warp_native_sync`: `0.4454765 s`.
- Gate509 repeat `triangle_warp_native_batch`: `0.4622479 s`.
- Gate509 repeat `triangle_warp_native_sync`: `0.4458116 s`.
- Gate508 repeat `triangle_warp_native_batch`: `0.466583 s`.
- Gate508 repeat `triangle_warp_native_sync`: `0.4500857 s`.

Numerical agreement:

- Gate509 candidate vs Gate509 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate509 candidate vs Gate508 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate509 repeat vs Gate508 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.

External-reference comparison:

- Report:
  `C:\glass_runs\phase2_s2_gate509_lanczos_unclamped_specialized_ab_real\runs_20260623_062926\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate509_lanczos_unclamped_specialized_ab_real\runs_20260623_062926\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Speedup vs external fastIntegration reference:
  `165.03945133256556x`.
- RMS difference: `0.0017794216505176163`.
- P99 absolute difference: `0.00042621337808668863`.
- Compared pixels with `min_coverage=190`: `59217988`.

## Known Limits

- This is a native CUDA control-flow specialization, not a scientific
  algorithm change.
- The real 200-light master remains bit-identical to Gate508. The warp sync
  component improves slightly, while end-to-end runtime remains dominated by
  I/O/decode/upload overlap and broader registration/warp orchestration.
- The next substantive gate should target larger resident registration/warp
  batching or I/O pipeline overlap rather than more report-only evidence gates.

## Next Step

Continue the real 200-light A/B mainline:

- reduce resident registration/warp orchestration beyond single-kernel
  specialization;
- explore keeping more descriptor/scoring/refinement state resident across the
  batch;
- preserve Gate508/Gate509 bitwise master output unless a deliberate science
  change is introduced and validated.

## Clean-Room Compliance

Compliant. This gate changed GLASS-owned CUDA warp kernels, native CUDA binding
dispatch, resident artifact aggregation, tests, and documentation. It used
GLASS tests, GLASS real-run artifacts, and a user-generated external reference
output for black-box comparison. No official PixInsight/WBPP/PJSR source code
was read, copied, summarized, or reworked.
