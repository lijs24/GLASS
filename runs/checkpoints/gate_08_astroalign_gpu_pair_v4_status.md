# Gate 08 astroalign vs GLASS CUDA pair alignment v4

Date: 2026-05-13

Status: completed real two-frame alignment comparison on the same calibrated M38 pair.

## Input frames

- Reference: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits`
- Moving: `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits`
- Image shape: 6422 x 9600.

## Command

```powershell
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits --moving C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits --out C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v4.json --max-shift 16 --catalog-grid-cols 4 --catalog-grid-rows 4 --catalog-prior-radius 4
```

## Results

- Output JSON: `C:\glass_runs\final_m38_h_200\astroalign_vs_glass_gpu_pair_S000061_S000062_full_benchmark_v4.json`
- astroalign total: 9.86234389996389 s.
- astroalign find transform: 6.980349899968132 s.
- astroalign apply transform: 2.881993999995757 s.
- astroalign control points: 50.
- astroalign transform dx/dy: 1.2970099199183096, -0.35989808818067104.
- GLASS CUDA matrix warp from astroalign matrix: 0.1637462999788113 s.
- GLASS CUDA matched-pair similarity fit plus warp: 0.09432769997511059 s.
- GLASS CUDA matched-pair fit RMS: 0.13409212231636047 px.
- GLASS CUDA resident matrix warp device time: 0.006662600033450872 s.
- GLASS CUDA resident matrix warp upload plus device: 0.04589850001502782 s.
- GLASS CUDA resident NCC subpixel device time: 0.2057871999568306 s.
- Resident matrix device speedup vs astroalign apply: 432.56x.
- Resident matrix upload-plus-device speedup vs astroalign apply: 62.79x.
- CUDA matched-pair similarity fit plus warp speedup vs astroalign apply: 30.55x.
- Full astroalign total vs resident NCC subpixel device speedup: 47.92x.

## Output agreement

- Common valid pixels for matrix-warp comparison: 61,632,460.
- GPU matrix warp minus astroalign apply:
  - mean diff: 0.0006378466236690087 ADU.
  - median abs diff: 3.9832916259765625 ADU.
  - p95 abs diff: 12.982681274414062 ADU.
  - RMS diff: 12.0167125226894 ADU.
- GPU matched-pair similarity matrix max absolute delta vs astroalign matrix: 0.016526604854334437.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by GLASS: 97,886 MiB.

## Known limitations

- The fastest resident matrix-warp comparison uses the transform already found by astroalign; it isolates warp/apply speed and interpolation agreement.
- The matched-pair CUDA similarity path uses astroalign's matched control points as input pairs, so it validates GPU fit and warp, not independent full star matching.
- The independent catalog translation path on the full real frame remains not accepted for this pair; it selected too few reliable mutual inliers. This is expected until robust GPU descriptor matching or improved star catalog filtering is wired in.

## Clean-room compliance

Compliant. This comparison uses the open-source astroalign package and GLASS-owned CUDA code. No official WBPP/PJSR source was read or copied.
