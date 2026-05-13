# Gate 08 astroalign-matches CUDA similarity bridge checkpoint

Date: 2026-05-13

Status: completed incremental registration bridge. This does not implement pure-GPU star matching yet; it reduces the external astroalign dependency in the pair benchmark from "supply the final matrix" to "supply matched control points", with GLASS CUDA fitting and applying the similarity transform.

## Completed work

- Extended `benchmarks/compare_astroalign_gpu_alignment.py` to keep astroalign matched control points.
- Added benchmark path:
  - astroalign finds matched moving/reference control points
  - `glass_cuda.estimate_similarity_from_pairs_f32` fits the matrix
  - `glass_cuda.warp_matrix_bilinear_f32` applies the fitted matrix
- Added JSON fields for:
  - CUDA similarity fit timing
  - CUDA warp timing after the fit
  - fitted scale/rotation/matrix
  - valid/input matched-pair counts
  - fit RMS
  - image difference versus astroalign apply on common valid pixels
  - max matrix delta versus astroalign's own final matrix
- Updated benchmark tests to assert the CUDA fit path is exercised and remains subpixel-consistent with astroalign on a synthetic pair.
- Updated `docs/registration_model.md` with the full-frame M38 pair v3 artifact and numbers.

## Verification commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_compare_astroalign_gpu_alignment_records_direct_diff tests\test_gpu_registration_search.py::test_gpu_estimate_similarity_from_matched_pairs
```

Result: 2 passed in 0.61 s.

```powershell
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits --moving C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits --out C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v3.json --max-shift 16 --catalog-grid-cols 4 --catalog-grid-rows 4 --catalog-prior-radius 4
```

Result artifact:

- `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v3.json`

Observed key metrics:

- Astroalign total: 9.5026 s.
- Astroalign find transform: 6.6377 s.
- Astroalign apply transform: 2.8649 s.
- Astroalign matched control points: 50.
- GLASS CUDA similarity fit from those points: 0.00122 s.
- GLASS CUDA similarity fit plus standalone matrix warp: 0.0920 s.
- GLASS CUDA fit RMS: 0.1341 px.
- Matrix max absolute delta vs astroalign final matrix: 0.0165 px in matrix components, dominated by translation.
- GPU similarity-fit output versus astroalign apply:
  - common valid pixels: 61,632,242
  - median absolute difference: 3.9795 ADU
  - p99 absolute difference: 22.9444 ADU
  - RMS difference: 12.0049 ADU
- Speedup of GPU fit plus standalone warp vs astroalign apply: 31.13x.
- Resident matrix warp from astroalign matrix remains available as the pixel-warp upper bound: 0.0071 s device-only.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 125 passed in 7.07 s.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by GLASS: 97,886 MiB.

## Known limitations

- Astroalign still supplies the matched control points in this benchmark path.
- The GLASS-owned GPU catalog path is still translation-only and does not yet supply robust similarity/affine inliers.
- The CUDA similarity fit is least-squares over provided pairs; robust outlier rejection/RANSAC remains future work.
- Full resident fitting from device-resident control-point buffers is not wired yet; the current wrapper uploads compact coordinate arrays.

## Next step

Port or implement the descriptor matching and robust inlier-selection stage on GPU, using this CUDA similarity-fit primitive as the final matrix-estimation step once candidate pairs are available.

## Clean-room compliance

Compliant. Astroalign is used as an open-source external reference for matched control points; GLASS CUDA performs the matrix fit and warp. No official WBPP/PJSR source was read or copied.
