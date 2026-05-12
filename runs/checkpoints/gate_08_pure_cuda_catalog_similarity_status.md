# Gate 08 pure CUDA catalog similarity checkpoint

Date: 2026-05-13

Status: completed incremental pure-GPWBPP GPU catalog-similarity path. This does not use astroalign control points for the catalog-similarity estimate.

## Completed work

- Added CUDA-side `star_top_nms_candidates_f32(...)`:
  - GPU local-maximum top candidate scan.
  - GPU minimum-distance suppression over the compact bright-star list.
  - Python wrapper with CPU fallback for importability.
- Extended `estimate_similarity_from_catalogs_f32(...)`:
  - optional prior translation constraint;
  - optional min/max scale constraint;
  - optional maximum absolute rotation constraint.
- Extended `gpwbpp.gpu.registration.register_similarity_from_star_catalogs_f32(...)` to pass NMS and transform-prior settings.
- Extended `benchmarks/compare_astroalign_gpu_alignment.py` to report:
  - `gpwbpp_cuda_catalog_similarity`;
  - direct output difference vs astroalign apply on common valid pixels;
  - `catalog_similarity_speedup_vs_astroalign`.
- Added tests for CUDA top-NMS candidates and constrained catalog similarity fields.
- Updated CUDA backend and registration model docs.

## Verification commands

```powershell
cmd /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda --config Release'
```

Result: native CUDA extension rebuilt successfully. CUDA Toolkit emitted C4819 warnings in NVIDIA headers under code page 936; build completed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_registration_search.py tests\test_benchmarks.py
```

Result: 17 passed in 1.45 s.

```powershell
.\.venv\Scripts\python.exe benchmarks\compare_astroalign_gpu_alignment.py --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000061.fits --moving C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\calib_cache\calibrated\calibrated_S000062.fits --out C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v6.json --max-shift 16 --catalog-stars 64 --catalog-nms-scan-stars 4096 --catalog-nms-min-separation 64 --catalog-prior-radius 4 --catalog-min-inliers 6 --catalog-similarity-min-pair-distance 128 --catalog-similarity-min-scale 0.995 --catalog-similarity-max-scale 1.005 --catalog-similarity-max-rotation-rad 0.01
```

Result: benchmark completed.

## Real pair result

- Output JSON: `C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v6.json`
- Image shape: 6422 x 9600.
- astroalign total: 9.7354587999871 s.
- astroalign find transform: 6.796644399990328 s.
- astroalign apply transform: 2.9388143999967724 s.
- Pure GPWBPP GPU catalog similarity:
  - model: `pure_cuda_catalog_similarity_seed_then_matrix_warp`;
  - elapsed: 29.245655699982308 s;
  - accepted: true;
  - inliers: 12;
  - scale: 0.9999985098838806;
  - rotation_rad: 0.00021702697267755866;
  - matrix translation: 1.38916015625, -0.4052734375;
  - fit RMS: 0.7662009596824646 px.
- Direct difference vs astroalign apply on common valid pixels:
  - valid pixels: 61,630,136;
  - median absolute difference: 12.787239074707031 ADU;
  - RMS difference: 51.29458937099368 ADU.

## CUDA availability

- CUDA backend available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM reported by GPWBPP: 97,886 MiB.

## Known limitations

- Correctness is now demonstrated for a real full-frame pair without astroalign control points, but speed is not yet acceptable: the current NMS/top candidate path and brute-force catalog similarity search are still too slow.
- The 4096-scan NMS setting is required for this real pair to reach accepted status; smaller 512/1024 scans were faster but did not reach the inlier threshold.
- The fastest resident warp path still uses an external matrix in the comparison benchmark; that remains useful for isolating pixel-warp speed but is not the pure catalog-solving path.
- Star coordinates are still local maxima, not subpixel centroids.

## Next step

Optimize pure GPU registration by replacing the global-lock top-N scan and serial best-candidate selection with a parallel per-tile/per-cell candidate prefilter and parallel reduction. Then retest the same M38 pair until the pure GPWBPP GPU catalog path is both accepted and faster than astroalign find+apply.

## Clean-room compliance

Compliant. The new code uses GPWBPP-owned CUDA kernels and generic geometric registration formulas. No official WBPP/PJSR source was read or copied.
