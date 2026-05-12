# Gate 09 Resident Matching Masters Subset50 Status

Gate: 09 - resident calibration correctness for matrix warp scaling

Date: 2026-05-13

## Completed content

- Replaced the resident CUDA aggregate-same-shape calibration shortcut with
  planner matching-group master selection.
- Resident calibration now uses each light frame's `LightPlan.matching_bias_group`,
  `matching_dark_group`, and `matching_flat_group`.
- Master sets are cached under `calib_cache/resident_masters` and uploaded to
  `ResidentCalibratedStack` when the current light's matching groups change.
- `resident_artifacts.json` now records `calibration_group_policy=planner_matching_groups_per_light`
  and the master set metadata.
- Added a resident regression test with two dark groups to ensure multiple
  planner-matched master sets are used.
- Re-ran the M38 50-light external-matrix validation and confirmed the resident
  output now matches tile-mode output closely.
- Updated calibration and validation docs.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\resident_cuda.py tests\test_resident_cuda_run.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py tests\test_cuda_resident_stack.py
```

Result: 20 passed.

```powershell
.\.venv\Scripts\gpwbpp.exe run --plan C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_subset50_allcal_probe\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset50_flat005_preview3072_matchedmasters --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration external_matrix --resident-registration-results C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\registration_results.json
```

Result: completed through integration in 24.8587 s.

Resident result:

- frame count: 50
- registration status counts: 1 reference, 49 ok
- matrix bilinear applications: 49
- calibration group policy: `planner_matching_groups_per_light`
- master set count: 1 for this H subset
- resident registration mean per frame: 0.00794 s
- resident integration: 0.0813 s

```powershell
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset50_flat005_preview3072_matchedmasters\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset50_ref_light001_flat005_preview3072\integration\master_H.fits --out C:\gpwbpp_runs\final_m38_h_200\resident_external_matrix_matchedmasters_vs_tile_astroalign_subset50_compare.html --gpwbpp-label resident_cuda_external_matrix_50_matchedmasters --reference-label tile_astroalign_cpu_warp_50 --gpwbpp-time-seconds 24.858685999992304 --reference-time-seconds 871.9394945999375
```

Result: passed.

Matched-master compare metrics:

- shape match: true
- median absolute difference: 0.001373 ADU
- p90 absolute difference: 0.004318 ADU
- p99 absolute difference: 0.011642 ADU
- p99.9 absolute difference: 0.058594 ADU
- RMS difference: 0.033920 ADU
- relative RMS difference: 0.0000943
- robust fit scale: 0.99999918
- robust fit offset: 0.0000915
- resident CUDA speedup vs tile reference: 35.076x

For comparison, the prior aggregate-master resident run on the same 50-light
matrix set had median absolute difference 0.444 ADU and relative RMS 0.00622.
The improvement confirms that resident calibration grouping, not CUDA matrix
warp, was the dominant mismatch.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 120 passed.

## CUDA availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset50_flat005_preview3072_matchedmasters\resident_artifacts.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset50_flat005_preview3072_matchedmasters\registration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset50_flat005_preview3072_matchedmasters\integration\resident_master_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\resident_external_matrix_matchedmasters_vs_tile_astroalign_subset50_compare.json`
- `C:\gpwbpp_runs\final_m38_h_200\resident_external_matrix_matchedmasters_vs_tile_astroalign_subset50_compare.html`

## Known limitations

- This validates 50 lights, not the final 200-light benchmark.
- Matrix generation still uses open-source astroalign on CPU previews.
- Local Normalization and rejection were disabled for this focused warp/calibration correctness comparison.
- The resident master cache currently stores NumPy arrays, not FITS master artifacts with full metadata.

## Next step

Run the same matched-master resident external-matrix path on the 200-light plan, then compare against the tile/WBPP reference outputs. If matrix generation is too slow at 200, optimize the registration preview strategy before the final benchmark.

## Clean-room compliance

This work used GPWBPP-owned code, user-provided M38 data, and open-source astroalign as an external reference. No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
