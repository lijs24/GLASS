# Gate 08 resident CUDA triangle real subset12 status

Date: 2026-05-13 14:46:57 +08:00

## Gate

Gate 08: Registration

## Completed

- Ran resident CUDA `similarity_cuda_triangle` on a real M38 H subset.
- Input plan reused the existing curated subset:
  `C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8_fixed350\processing_plan.json`.
- Dataset subset:
  - Light: 12.
  - Bias: 6.
  - Dark: 10.
  - Flat: 4.
  - Image shape: 9600x6422.
- Generated integration outputs and an HTML report.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe run --plan "C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_subset12_starcore8_fixed350\processing_plan.json" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_fixed350" --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 96 --resident-star-tolerance-px 3 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --resident-ncc-sample-stride 4 --reference-frame-id LIGHT_H_0001
.\.venv\Scripts\glass.exe report --run "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_fixed350" --out "C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_fixed350\report.html"
```

## Test Results

- Run status: completed through resident integration.
- Total command timing: 17.084986299974844 s.
- Registration status counts: 11 ok, 1 reference.
- First non-reference row:
  - Frame: `S000022`.
  - Matched stars/inliers: 64.
  - Triangle candidate count: 611546.
  - Fit RMS: 0.9551883339881897 px.
  - Pixel metric RMS: 81.3776 ADU.
  - Pixel metric NCC: 0.973469.
- Resident timing:
  - Master build/load: 9.639485299994703 s.
  - Light read/upload/calibrate: 12.118596300017089 s.
  - Per-frame registration mean: 0.15105484166997485 s.
  - Resident integration: 0.07052519998978823 s.
  - Output write: 0.3417213999782689 s.
- Estimated peak resident memory: 4.134035155177116 GiB.
- Output master:
  `C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_fixed350\integration\resident_master_H.fits`.
- Report:
  `C:\glass_runs\final_m38_h_200\glass_resident_triangle_subset12_fixed350\report.html`.

## CUDA

- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: available.

## Known Limitations

- This real-data validation uses 12 lights, not the final 200-light benchmark.
- Integration used `rejection=none` and `local_normalization=off` for a focused
  registration/runtime validation.
- The mode is still a bridge: compact catalogs/descriptors pass through Python,
  though calibrated frames and matrix application remain resident in VRAM.
- Result consistency against WBPP has not been evaluated for this subset.

## Next Step

Use this successful subset to configure a larger resident triangle run, then
compare the final integrated master against the WBPP black-box output and
existing astroalign/external-matrix runs.

## Clean-room Compliance

Compliant. This run used user-provided real data and GLASS-owned code only.
No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
