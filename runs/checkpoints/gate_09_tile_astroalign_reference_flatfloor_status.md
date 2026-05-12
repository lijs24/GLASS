# Gate 09 Tile Astroalign Reference And Flat Floor Status

Gate: 09 - real-data registration matrix generation for resident CUDA warp

Date: 2026-05-13

## Completed content

- Added tile-mode `--reference-frame-id` support for `gpwbpp run`.
  - It can match a frame id, calibrated-cache file name/stem, or original frame file name/stem from the processing plan.
- Added `--registration-preview-max-dimension` for tile-mode streaming registration.
- Fixed non-resident tile-mode `--flat-floor`; it now overrides the calibration policy just like resident mode.
- Added validation that flat-floor overrides must be positive.
- Added tests for:
  - tile-mode reference override through original frame stem;
  - tile-mode flat-floor propagation into `calibration_artifacts.json`;
  - safe per-frame astroalign failure recording.
- Documented the calibration and registration implications.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\registration.py src\gpwbpp\cli.py tests\test_cpu_registration.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_cli_smoke.py
```

Result: 13 passed.

```powershell
.\.venv\Scripts\python.exe -m ruff check src\gpwbpp\engine\pipeline.py src\gpwbpp\engine\registration.py src\gpwbpp\cli.py tests\test_cpu_registration.py tests\test_pipeline_fixture.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_pipeline_fixture.py tests\test_cli_smoke.py
```

Result: 25 passed.

```powershell
.\.venv\Scripts\gpwbpp.exe run --plan C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_stride4_subset12\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset12_ref_light001_flat005 --backend cuda --until-stage registration --registration-method astroalign --registration-preview-max-dimension 9600 --tile-size 1024 --flat-floor 0.05 --reference-frame-id LIGHT_H_0001
```

Result: completed through registration in 177.74 s.

Key real-data result:

- reference: `S000021` / `LIGHT_H_0001`
- quality-selected reference before override: `S000025`
- requested reference: `LIGHT_H_0001`
- preview scale: 1
- flat floor recorded in calibration artifacts: 0.05
- registration status counts: 1 reference, 11 ok
- matched stars: 48 to 50 on accepted moving frames
- RMS range: about 0.124 px to 0.452 px

```powershell
.\.venv\Scripts\gpwbpp.exe run --plan C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_stride4_subset12\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset12_flat005 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration external_matrix --resident-registration-results C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset12_ref_light001_flat005\registration_results.json
```

Result: completed through integration in 14.47 s.

Key resident CUDA external-matrix result:

- registration status counts: 1 reference, 11 ok
- non-reference matrix applications: 11 `matrix_bilinear`
- resident registration mean per frame: 0.00711 s
- resident integration: 0.0753 s
- output master: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset12_flat005\integration\resident_master_H.fits`

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 119 passed.

## CUDA availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset12_ref_light001_flat005\registration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_tile_astroalign_subset12_ref_light001_flat005\calibration_artifacts.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset12_flat005\registration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset12_flat005\integration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_external_matrix_astroalign_subset12_flat005\resident_artifacts.json`

## Known limitations

- Full-resolution astroalign preview is expensive: registration took 142.58 s for 12 frames.
- The transform source is still open-source astroalign, not GPWBPP-owned GPU asterism matching.
- Resident external-matrix mode currently trusts accepted matrices and does not recompute residuals on GPU.
- The next scaling step needs a faster matrix-generation path before applying this to 200 lights.

## Next step

Use the successful 12-frame matrix set as a correctness anchor, then optimize matrix generation: either crop/preview more intelligently for astroalign or implement/port a GPU star-descriptor matcher that produces similarity/affine matrices directly.

## Clean-room compliance

This work used GPWBPP-owned code, user-provided M38 data, and open-source astroalign as an external reference. No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
