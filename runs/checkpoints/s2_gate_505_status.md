# S2-Gate 505 Status: Unclamped Lanczos3 Warp Fast Path

## Gate

S2-Gate 505

## Completed Content

- Added an unclamped Lanczos3 CUDA warp fast path by skipping local min/max
  tracking when `clamping_threshold < 0`.
- Added native timing/artifact field `lanczos3_clamping_enabled`.
- Propagated the native Lanczos3 clamping flag into
  `resident_artifacts.json` as
  `triangle_warp_batch_native_lanczos3_clamping_enabled`.
- Added CUDA warp and resident CLI tests for clamped and unclamped Lanczos3
  contracts.
- Ran a negative fused-Lanczos3 probe and kept the conservative stack dispatch
  for non-bilinear matrix registration/integration.
- Ran a real 200-light A/B on the M38 H dataset and compared the output with
  Gate 504 and the user-generated external reference master.
- Checked C-drive/project cleanup state before the real A/B:
  C: had about `430.78 GB` free; the repo itself was about `2.4 GB`, while
  historical generated runs under `C:\glass_runs` and `C:\gpwbpp_runs` were the
  large space consumers. No destructive cleanup was required or performed.

## Changed Files

- `cpp/cuda/warp_kernels.cu`
- `cpp/src/native_bindings.cpp`
- `src/glass/engine/resident_cuda.py`
- `tests/test_gpu_warp_vs_cpu.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`

## Commands Run

- `python -m ruff check src\glass\engine\resident_cuda.py tests\test_gpu_warp_vs_cpu.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests/test_gpu_warp_vs_cpu.py tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_dispatch_keeps_lanczos_rejection_on_stack`
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
  --glass C:\glass_runs\phase2_s2_gate505_lanczos_unclamped_warp_ab_real\runs_20260623_055211\repeat\integration\resident_master_H.fits `
  --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf `
  --out C:\glass_runs\phase2_s2_gate505_lanczos_unclamped_warp_ab_real\runs_20260623_055211\compare_vs_wbpp_fastintegration_scaled_coverage190.html `
  --glass-time-seconds 6.707604100054596 `
  --reference-time-seconds 1092.541 `
  --glass-label GLASS-Gate505-resident-minimal `
  --reference-label PixInsight-WBPP-fastIntegration `
  --glass-scale 8.764434957115609e-06 `
  --glass-offset 0.0006274500691899127 `
  --glass-coverage-map C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_coverage_map_H.fits `
  --min-coverage 190
```

## Test Results

- Ruff: passed.
- Focused CUDA/resident tests: `16 passed in 0.63 s`.
- Full pytest: `1152 passed in 41.58 s`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Real 200-Light Results

Run root:

`C:\glass_runs\phase2_s2_gate505_lanczos_unclamped_warp_ab_real\runs_20260623_055211`

Runtime:

- Gate 505 candidate: `6.618832700012717 s`.
- Gate 505 repeat: `6.707604100054596 s`.
- Gate 504 repeat baseline: `6.615711500053294 s`.

Kernel/component timing:

- Gate 504 repeat native Lanczos3 batch: `0.4781858 s`.
- Gate 505 repeat native Lanczos3 batch: `0.4683928 s`.
- Gate 504 repeat native Lanczos3 sync: `0.4615893 s`.
- Gate 505 repeat native Lanczos3 sync: `0.4519578 s`.
- Gate 505 repeat artifact:
  `triangle_warp_batch_native_lanczos3_clamping_enabled=false`.

Numerical agreement:

- Gate 505 candidate vs Gate 504 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate 505 repeat vs Gate 504 repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.
- Gate 505 candidate vs repeat: bitwise equal,
  `RMS=0`, `p99=0`, `max_abs=0`.

External-reference comparison:

- Report:
  `C:\glass_runs\phase2_s2_gate505_lanczos_unclamped_warp_ab_real\runs_20260623_055211\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate505_lanczos_unclamped_warp_ab_real\runs_20260623_055211\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- Speedup vs external fastIntegration reference:
  `162.880960728x`.
- RMS difference: `0.0017794216505176163`.
- P99 absolute difference: `0.00042621337808668863`.
- Compared pixels with `min_coverage=190`: `59217988`.

## Known Limits

- End-to-end runtime did not improve monotonically because the total remains
  dominated by overlapped FITS read/decode/upload/orchestration variance.
- The promoted change improves the Lanczos3 native warp kernel path only.
- Fused Lanczos3 integration is not promoted. A probe with explicit fused
  Lanczos3 was slower and changed output pixels, so the conservative stack route
  remains required for non-bilinear matrix registration/integration.
- Gate 505 does not change registration scoring, frame admission, calibration,
  local normalization, or rejection semantics.

## Next Step

Continue Phase 2 mainline optimization on the remaining large components:

- Reduce resident registration/catalog native sync and output-download time.
- Reduce read/decode/upload orchestration variance through tighter resident
  batching and pinned-ring scheduling.
- Preserve the Gate 504/505 bitwise output baseline while optimizing.

## Clean-Room Compliance

Compliant. This gate changed GLASS-owned CUDA kernel control flow and artifact
reporting only. It used GLASS tests, GLASS real-run artifacts, and a
user-generated external reference output for black-box comparison. No official
PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
