# Gate 09 External Matrix Real Subset Status

Gate: 09 - resident matrix warp validation on real subset

Date: 2026-05-13

## Completed content

- Added `--registration-preview-max-dimension` for tile-mode registration.
- Added a guard that rejects non-positive registration preview dimensions.
- Changed tile-mode `--registration-method astroalign` so a single astroalign failure records that frame as `failed` instead of aborting the whole registration stage.
- Added a regression test for astroalign failure handling.
- Ran a real M38 subset diagnostic through tile-mode astroalign registration.
- Ran a real resident CUDA `external_matrix` integration using a two-frame M38 astroalign similarity matrix artifact.

## Commands run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\engine\registration.py tests\test_cpu_registration.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_resident_cuda_run.py
```

Result: 15 passed.

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\registration.py tests\test_cpu_registration.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_cpu_registration.py tests\test_cli_smoke.py
```

Result: 12 passed.

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_subset12\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_external_bridge --backend cuda --until-stage registration --registration-method astroalign --tile-size 1024 --flat-floor 0.05
```

Initial result before fix: failed because astroalign raised `MaxIterError`. This led to the failure-handling fix.

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_subset12\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_external_bridge --backend cuda --until-stage registration --registration-method astroalign --tile-size 1024 --flat-floor 0.05
```

Result after fix: completed through registration in 112.61 s. The stage reported 1 reference and 11 failed frames instead of aborting.

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_subset12\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_external_bridge_3072 --backend cuda --until-stage registration --registration-method astroalign --registration-preview-max-dimension 3072 --tile-size 1024 --flat-floor 0.05
```

Result: completed through registration in 119.33 s. The larger preview still reported 1 reference and 11 failed frames, so it did not provide accepted matrices for this subset.

```powershell
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\final_m38_h_200\glass_resident_ncc_stride4_subset12\processing_plan.json --out C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_light0001_0003_subset12 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration external_matrix --resident-registration-results C:\glass_runs\final_m38_h_200\external_astroalign_matrix_light0001_0003_subset12.json
```

Result: completed through integration in 15.43 s.

Real resident external-matrix result:

- input plan: 12 light frames
- accepted frames: 1 reference, 1 ok similarity matrix, 10 failed/zero-weight frames
- moving accepted frame: `S000023` / `LIGHT_H_0003`
- application warning: `external_registration_application=matrix_bilinear`
- resident registration mean per frame: 0.000686 s
- resident integration: 0.0694 s
- output master: `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_light0001_0003_subset12\integration\resident_master_H.fits`

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: 118 passed.

## CUDA availability

CUDA was available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB

## Artifacts

- `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_external_bridge\registration_results.json`
- `C:\glass_runs\final_m38_h_200\glass_tile_astroalign_subset12_external_bridge_3072\registration_results.json`
- `C:\glass_runs\final_m38_h_200\external_astroalign_matrix_light0001_0003_subset12.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_light0001_0003_subset12\registration_results.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_light0001_0003_subset12\integration_results.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_external_matrix_light0001_0003_subset12\resident_artifacts.json`

## Known limitations

- Tile-mode astroalign on the 12-frame M38 subset still failed to find acceptable transforms even with a 3072 preview; it now fails safely per frame.
- The successful resident external-matrix validation used the known two-frame astroalign matrix from the prior GLASS diagnostic, not a complete tile-mode accepted-matrix set.
- The main GPU-owned similarity/affine matcher remains future work.

## Next step

Improve the owned GPU star/descriptor matcher or expose a more robust preview/crop strategy for astroalign-style matrix generation, then run resident `external_matrix` on a multi-frame accepted matrix set.

## Clean-room compliance

This work used GLASS-owned code, user-provided M38 image data, and open-source astroalign behavior as a black-box/open-source reference. No PixInsight/WBPP/PJSR official source code was read, copied, summarized, or modified.
