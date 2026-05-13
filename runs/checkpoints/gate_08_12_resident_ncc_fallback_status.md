# Gate 08/12 Increment: Resident NCC Fallback Verification

Date: 2026-05-13

## Gates

- Gate 08: registration reliability increment.
- Gate 12: real 200-light resident CUDA validation increment.

## Completed Content

- Added `--resident-ncc-fallback-score-threshold`.
- Default is `0.0`, which disables fallback and preserves previous behavior.
- When `--resident-ncc-sample-stride > 1` and the sampled subpixel NCC score is at or below the threshold, GLASS re-estimates that frame at full stride `1`.
- Per-frame registration warnings record fallback details:
  - `ncc_fallback_stride=1`
  - fallback reason
  - original sampled shift/score
  - full-stride coarse and subpixel scores
- Resident artifacts record `ncc_fallback_score_threshold`.
- Documentation updated in `docs/registration_model.md` and `docs/cuda_backend.md`.
- Added/updated resident CUDA smoke test coverage for forced fallback.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py
```

Result: `All checks passed!`

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_gpu_registration_search.py tests\test_cuda_resident_stack.py
```

Result: `28 passed in 0.47s`

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: `110 passed in 5.93s`

## Real M38 Fallback Run

Command:

```powershell
$base='C:\glass_runs\final_m38_h_200'
$src=Join-Path $base 'glass_resident_ncc_winsorized_allcal_200'
$run=Join-Path $base 'glass_resident_ncc_stride4_fallback002_winsorized_allcal_200'
New-Item -ItemType Directory -Force -Path $run | Out-Null
.\.venv\Scripts\glass.exe run --plan (Join-Path $src 'processing_plan.json') --out $run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_ncc_subpixel --resident-registration-max-shift 64 --resident-ncc-sample-stride 4 --resident-ncc-fallback-score-threshold 0.02 --resident-subpixel-radius-steps 2 --resident-subpixel-step 0.5
```

Result:

- Run directory: `C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_fallback002_winsorized_allcal_200`
- Input scale: 200 light, 20 bias, 20 dark, 20 flat.
- Total elapsed: `280.15153769997414 s`
- `ncc_sample_stride`: `4`
- `ncc_fallback_score_threshold`: `0.02`
- Fallback count: `110`
- Failed registration frames: `0`
- Per-frame registration mean: `1.1012002794982982 s`
- Estimated peak VRAM: unchanged from resident 200-light stack, about `47.31 GiB`.

## Registration Comparison vs Stride 1

Compared against:
`C:\glass_runs\final_m38_h_200\glass_resident_ncc_winsorized_allcal_200`

- Compared frames: `200`
- Changed frames: `19`
- Mean shift delta: `0.09664213562373096 px`
- Median shift delta: `0.0 px`
- p90 shift delta: `0.0 px`
- p99 shift delta: `1.0 px`
- Max shift delta: `1.4142135623730951 px`

This is a large improvement over pure stride 4, which had max shift delta above `100 px` on a few low-score frames.

## Compare Reports

WBPP FastIntegration compare:

- HTML: `C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_fallback002_winsorized_allcal_200\resident_stride4_fallback002_vs_wbpp_fastintegration_scaled_compare.html`
- JSON: `C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_fallback002_winsorized_allcal_200\resident_stride4_fallback002_vs_wbpp_fastintegration_scaled_compare.json`
- Speedup vs WBPP: `3.899821535764859x`
- Direct scaled median absolute diff: `8.1482226960361e-05`
- Direct scaled p90 absolute diff: `0.0002704000798985362`
- Direct scaled p99 absolute diff: `0.007525513715227096`
- Direct scaled RMS diff: `0.013439388820945046`
- Robust fit-pixel RMS diff: `0.001810779780514216`

Stride-1 GLASS compare:

- HTML: `C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_fallback002_winsorized_allcal_200\resident_stride4_fallback002_vs_stride1_compare.html`
- JSON: `C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_fallback002_winsorized_allcal_200\resident_stride4_fallback002_vs_stride1_compare.json`
- Speedup vs stride 1: `1.2963543315937225x`
- Direct median absolute diff: `0.310211181640625`
- Direct p90 absolute diff: `0.8171463012695312`
- Direct p99 absolute diff: `2.8027725982665856`
- Robust fit-pixel RMS diff: `0.5962947348657361`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Native backend: true

## Known Limitations

- The fallback threshold is heuristic. `0.02` worked well for this M38 run, but should not be treated as universally optimal.
- Fallback makes stride 4 safer but reduces the speedup relative to pure stride 4.
- Resident registration is still translation-only.
- Local Normalization remains disabled in the resident 200-light comparison path.
- The long-term registration target remains GPU star/descriptor similarity or affine registration using an open-source approach.

## Next Step

Use `--resident-ncc-sample-stride 4 --resident-ncc-fallback-score-threshold 0.02` as the current conservative high-speed NCC setting for M38-style resident timing runs, while implementing the open-source star/affine registration path for broader correctness.

## Clean-Room Compliance

Compliant. This work used project code, project-generated artifacts, user-provided input data, and user-generated PixInsight/WBPP black-box output. No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
