# Gate 12 Increment: Real M38 200-Light Resident CUDA NCC Stride 4

Date: 2026-05-13

## Gate

Gate 12 / end-to-end resident CUDA WBPP-like pipeline increment.

## Completed Content

- Ran the existing M38 H-alpha 200-light plan with resident CUDA calibration, resident NCC subpixel translation registration, resident bilinear warp, and resident winsorized sigma integration.
- Used the new `--resident-ncc-sample-stride 4` option to reduce full-frame NCC scoring work.
- Compared the output master against:
  - PixInsight/WBPP black-box FastIntegration output.
  - The previous GPWBPP resident NCC stride-1 200-light run.

## Commands Run

```powershell
$base='C:\gpwbpp_runs\final_m38_h_200'
$src=Join-Path $base 'gpwbpp_resident_ncc_winsorized_allcal_200'
$run=Join-Path $base 'gpwbpp_resident_ncc_stride4_winsorized_allcal_200'
New-Item -ItemType Directory -Force -Path $run | Out-Null
.\.venv\Scripts\gpwbpp.exe run --plan (Join-Path $src 'processing_plan.json') --out $run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_ncc_subpixel --resident-registration-max-shift 64 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 2 --resident-subpixel-step 0.5
```

```powershell
$base='C:\gpwbpp_runs\final_m38_h_200'
$run=Join-Path $base 'gpwbpp_resident_ncc_stride4_winsorized_allcal_200'
$ref='C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf'
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp (Join-Path $run 'integration\resident_master_H.fits') --reference $ref --out (Join-Path $run 'resident_stride4_vs_wbpp_fastintegration_scaled_compare.html') --gpwbpp-time-seconds 110.08566179999616 --reference-time-seconds 1092.541 --gpwbpp-label "GPWBPP resident NCC stride4 200 scaled" --reference-label "PixInsight WBPP FastIntegration" --gpwbpp-scale 1.5259021896696422e-05 --clip-low 0 --clip-high 1
.\.venv\Scripts\gpwbpp.exe compare --gpwbpp (Join-Path $run 'integration\resident_master_H.fits') --reference (Join-Path $base 'gpwbpp_resident_ncc_winsorized_allcal_200\integration\resident_master_H.fits') --out (Join-Path $run 'resident_stride4_vs_stride1_compare.html') --gpwbpp-time-seconds 110.08566179999616 --reference-time-seconds 363.1756594000035 --gpwbpp-label "GPWBPP resident NCC stride4 200" --reference-label "GPWBPP resident NCC stride1 200"
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result: `110 passed in 5.95s`

## Real M38 Run Result

- Run directory: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_stride4_winsorized_allcal_200`
- Input plan: `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_winsorized_allcal_200\processing_plan.json`
- Data scale:
  - 200 light frames.
  - 20 bias frames.
  - 20 dark frames.
  - 20 flat frames.
  - Image shape: `9600 x 6422`.
- Resident registration:
  - mode: `translation_ncc_subpixel`
  - max shift: `64`
  - subpixel radius steps: `2`
  - subpixel step: `0.5`
  - `ncc_sample_stride`: `4`
  - failed frames: `0`
- Timing:
  - total elapsed: `110.08566179999616 s`
  - master build/load: `17.33021479996387 s`
  - light read/upload/calibrate: `38.70692520000739 s`
  - per-frame registration mean: `0.2502626805042382 s`
  - resident winsorized integration: `0.3073842999874614 s`
  - output write: `0.8998308000154793 s`
- Memory estimate:
  - calibrated stack: `45.93372344970703 GiB`
  - estimated peak: `47.3117358982563 GiB`

## Comparison to PixInsight/WBPP FastIntegration

- Report:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_stride4_winsorized_allcal_200\resident_stride4_vs_wbpp_fastintegration_scaled_compare.html`
- JSON:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_stride4_winsorized_allcal_200\resident_stride4_vs_wbpp_fastintegration_scaled_compare.json`
- WBPP black-box elapsed: `1092.541 s`
- GPWBPP resident stride-4 elapsed: `110.08566179999616 s`
- Speedup vs WBPP: `9.924462297232955x`
- Shape match: true
- Scaled direct diff:
  - median absolute diff: `8.22610454633832e-05`
  - p90 absolute diff: `0.0002710371045395732`
  - p99 absolute diff: `0.007692309803096503`
  - RMS diff: `0.013449985090962263`
- Robust fit-pixel stats:
  - fit fraction: `0.9834148727032077`
  - fit-pixel RMS diff: `0.0018023733283998135`
  - fit-pixel p99 absolute diff: `0.0015271070722244543`

## Comparison to GPWBPP Resident NCC Stride 1

- Report:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_stride4_winsorized_allcal_200\resident_stride4_vs_stride1_compare.html`
- JSON:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_ncc_stride4_winsorized_allcal_200\resident_stride4_vs_stride1_compare.json`
- Previous stride-1 elapsed: `363.1756594000035 s`
- Speedup vs stride 1: `3.299027806725836x`
- Master diff vs stride 1:
  - median absolute diff: `1.2679443359375`
  - p90 absolute diff: `3.333892822265625`
  - p99 absolute diff: `12.421020889282147`
  - robust fit-pixel RMS diff: `2.7061233331140526`
- Registration shift comparison vs stride 1:
  - compared frames: `200`
  - changed frames: `122`
  - mean delta: `5.311152554285667 px`
  - median delta: `0.7071067811865476 px`
  - p90 delta: `16.194134740701646 px`
  - p99 delta: `103.4238850556292 px`
  - max delta: `110.78131611422569 px`

## CUDA Availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Native backend: true

## Known Limitations

- This run proves that `sample_stride=4` can deliver a large speedup on the 200-light M38 workload and still produce a WBPP-comparable integrated master.
- However, stride 4 also changes many per-frame translations relative to stride 1, including a small number of very large disagreements on low-NCC frames. It should not be promoted to the default without a stronger registration acceptance rule or a star/affine prior.
- Resident registration remains translation-only.
- Local Normalization remains disabled in this resident path.
- Winsorized sigma remains the project approximation, not a byte-identical PixInsight FastIntegration reproduction.

## Next Step

Add a registration confidence policy for resident NCC:

- reject or fall back when the best NCC score is very low;
- optionally use stride 4 for a fast coarse estimate, then verify/refine around that estimate with stride 1;
- prefer star/affine GPU registration as the long-term default once the open-source registration path is integrated.

## Clean-Room Compliance

Compliant. This increment used project code, user-provided input data, and user-generated PixInsight/WBPP black-box output artifacts. No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
