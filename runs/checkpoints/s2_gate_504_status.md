# S2-Gate 504 Status: Chunked Direct FITS Output Writer

## Gate

- Gate: S2-Gate 504
- Scope: output-stage performance and memory-pressure reduction for resident
  CUDA runs.
- Status: passed
- Date: 2026-06-23

## Completed

- Reworked the direct simple-primary FITS writer to stream eligible 2D outputs
  in bounded big-endian row chunks instead of writing one whole-image byte view.
- Added `fits_write_profile()` so resident artifacts record writer strategy,
  chunk count, rows per chunk, source dtype/shape/contiguity, target dtype, and
  estimated payload bytes.
- Recorded the profile in resident output storage artifacts.
- Added FITS chunk/profile tests and resident storage-profile assertions.
- Per user request, checked C: space and safely removed only regenerable project
  caches (`build`, `.pytest_cache`, `__pycache__`), freeing about 68.6 MB.
  `runs/`, checkpoints, real A/B artifacts, and the virtual environment were
  preserved.

## Commands Run

```powershell
Get-PSDrive -Name C
Get-ChildItem -Force
git status --short --branch
.\.venv\Scripts\python.exe -m pytest -q tests/test_fits_io.py
.\.venv\Scripts\python.exe -m ruff check src\glass\io\fits_io.py src\glass\engine\resident_cuda.py tests\test_fits_io.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate504_chunked_fits_writer_ab_real\runs_20260623_053419\candidate --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate504_chunked_fits_writer_ab_real\runs_20260623_053419\repeat --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate504_chunked_fits_writer_ab_real\runs_20260623_053419\repeat\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate504_chunked_fits_writer_ab_real\runs_20260623_053419\compare_vs_wbpp_fastintegration_scaled_coverage190.html --glass-time-seconds 6.615711500053294 --reference-time-seconds 1092.541 --glass-label GLASS-Gate504-resident-minimal --reference-label PixInsight-WBPP-fastIntegration --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_ab_200_wbpp_parity_20260622_223410\integration\resident_coverage_map_H.fits --min-coverage 190
```

## Test Results

- Focused FITS tests: `15 passed in 0.41s`
- Ruff focused check: passed
- Full pytest: `1151 passed in 46.71s`

## CUDA

- CUDA available: yes
- Native extension loaded: yes
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97,886 MiB
- Driver: 596.21

## Real 200-Light A/B

- Dataset: M38 H-alpha 200 lights, calibration frames from the staged
  `C:\gpwbpp_runs\final_m38_h_200` plan.
- Candidate run root:
  `C:\glass_runs\phase2_s2_gate504_chunked_fits_writer_ab_real\runs_20260623_053419`
- Gate503 baseline:
  `C:\glass_runs\phase2_s2_gate503_descriptor_batch_ab_real\runs_20260623_052608\default_descriptor_batch`
- Gate503 totals: `7.1556646000244655 s` and `7.309961199993268 s`
- Gate503 master output writes: `0.6129282000474632 s` and
  `0.7726107999915257 s`
- Gate504 totals: `6.634346000035293 s` and `6.615711500053294 s`
- Gate504 master output writes: `0.08645619999151677 s` and
  `0.08730260003358126 s`
- Gate504 writer profile: `direct_simple_primary_chunked_big_endian`,
  `15` chunks, `436` rows per chunk, `246604800` estimated data bytes.

## Numerical Result

- Gate504 candidate vs Gate503 baseline: bitwise equal, RMS `0.0`, p99 `0.0`,
  max `0.0`.
- Gate504 repeat vs Gate503 baseline: bitwise equal, RMS `0.0`, p99 `0.0`,
  max `0.0`.

## WBPP Black-Box Compare

- Report:
  `C:\glass_runs\phase2_s2_gate504_chunked_fits_writer_ab_real\runs_20260623_053419\compare_vs_wbpp_fastintegration_scaled_coverage190.html`
- JSON:
  `C:\glass_runs\phase2_s2_gate504_chunked_fits_writer_ab_real\runs_20260623_053419\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- WBPP black-box elapsed: `1092.541 s`
- Gate504 repeat elapsed: `6.615711500053294 s`
- Speedup: `165.1433863147144x`
- Coverage>=190 region fraction: `0.960532609259836`
- RMS difference: `0.0017794216505176163`
- p99 absolute difference: `0.00042621337808668863`

## Known Limits

- This gate changes output serialization only; it does not improve registration,
  warp, rejection, local normalization, or DQ science semantics.
- Minimal output mode does not emit a fresh coverage map, so the WBPP
  coverage>=190 comparison reused the established same-shape GLASS coverage map
  from the previous validation artifact. Pixel equality to Gate503 verifies the
  master image itself did not change.
- The direct writer still falls back to Astropy for unsupported primary-image
  shapes or unsupported dtypes.

## Next Step

- Return to resident registration/warp optimization: reduce native warp sync and
  Python orchestration time, then rerun the same 200-light A/B with WBPP compare.

## Clean-Room Compliance

- Compliant.
- This gate uses public FITS layout rules, GLASS-owned output arrays, GLASS test
  fixtures, current GLASS 200-light artifacts, and user-generated WBPP
  black-box outputs/log summaries.
- No official PixInsight/WBPP/PJSR source was opened, copied, summarized, or
  used as implementation input.
- Input image directories were treated as read-only.
