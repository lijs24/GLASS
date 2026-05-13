# Gate 10 Resident Global LN Partial Status

## Gate

Gate 10 partial capability checkpoint.

This is not a full Local Normalization gate completion. It validates an early resident CUDA global mean/std normalization path and records the remaining tile/window LN gap.

## Completed Content

- Verified the resident high-VRAM CUDA path can enable local normalization with `--local-normalization on`.
- The current implementation computes per-frame global mean/std statistics on resident GPU frames and applies per-frame scale/offset in VRAM.
- The run records `local_norm_results.json`, `resident_local_normalization` artifact state, timing, warnings, and report output.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8_fixed350\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_global_ln" --backend cuda --memory-mode resident --until-stage integration --local-normalization on --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.30
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_global_ln" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_global_ln\report.html"
```

## Test Results

- Latest validation before this artifact-only checkpoint:
  - Ruff: passed.
  - Targeted compare tests: `8 passed in 0.29s`.
  - Full test suite: `163 passed in 7.87s`.

## Real-data Results

- Output directory: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_global_ln`.
- Total elapsed: `18.510745999985375 s`.
- Local normalization mode: `resident_global_mean_std`.
- Local normalization enabled: true.
- Local normalization timing: `0.04855509998742491 s`.
- Local normalization frame statuses: 11 ok, 1 reference.
- Registration statuses: 11 ok, 1 reference.
- Report: `C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_lanczos3_global_ln\report.html`.

## CUDA Availability

- CUDA available: yes.
- Native backend: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- This is global per-frame mean/std normalization, not full WBPP-like tile/window Local Normalization.
- No crop box is produced because this capability does not crop.
- Background masks, local windows, outlier-resistant local models, and per-tile coefficient interpolation remain incomplete.
- This checkpoint is intentionally partial and should not be treated as Gate 10 complete.

## Next Step

- Implement a true tile/window LN model with CPU baseline and GPU apply/stats kernels, then validate on synthetic gradients and real-data subsets.

## Clean-room Compliance

- Compliant. The implementation uses general image normalization formulas and project-owned CUDA code.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or used as implementation input.
