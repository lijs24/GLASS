# PixInsight/WBPP Black-Box Reference

This project does not read or copy official PixInsight WBPP/PJSR source code.

Allowed reference material:

- User-generated WBPP logs.
- User-generated WBPP output directories.
- User-exported process settings.
- File names, statistics, and image outputs created by the user's own runs.

Disallowed material:

- Official WBPP/PJSR source files.
- Official script function names, class names, comments, UI text, or structure.

Gate 13 will compare GPWBPP outputs with user-generated reference masters and
record differences from calibration policy, registration, local normalization,
rejection, weighting, and crop/coverage handling.

## Timing protocol

The project timing comparison must use the same selected input frames for both
systems:

1. Build a small, same-target subset with matching bias, dark, flat, and light
   frames.
2. Run GPWBPP into a clean output directory and record wall-clock time.
3. Run PixInsight/WBPP as a black box into a separate output directory and
   record wall-clock time from user-visible logs or an external timer.
4. Compare final masters with `gpwbpp compare`.
5. Record input frame count, image dimensions, backend, selected WBPP settings,
   output master paths, elapsed seconds, and difference metrics.

`gpwbpp compare` can record timing fields directly:

```powershell
gpwbpp compare --gpwbpp runs/gpwbpp/integration/master_Lum.fits --reference P:\WBPP\master_Lum.fits --out runs/compare.html --gpwbpp-time-seconds 64.061 --reference-time-seconds 180 --reference-label "PixInsight WBPP"
```

Allowed PixInsight evidence remains limited to user-generated WBPP logs,
user-generated WBPP outputs, user-exported process settings, and measured
runtime. Official WBPP/PJSR source remains off limits.

## Current local status

A clean-room PixInsight/WBPP black-box run has been completed on the workstation
for the M38 H dataset staged under:

```text
C:\gpwbpp_runs\final_m38_h_200\input
```

The selected dataset contains 200 light frames and 20 each of bias, dark, and
flat frames. Input, temporary, and output data were placed on the internal
`C:` SSD for this timing run.

Black-box WBPP output:

```text
C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox
```

Timing summary:

- WBPP elapsed time: 1092.541 s.
- WBPP log line: `* WeightedBatchPreprocessing: 18:03.17`.
- GPWBPP resident CUDA calibration plus mean integration elapsed time:
  58.9810051000095 s, a raw timing speedup of 18.52x.
- GPWBPP resident CUDA calibration plus winsorized mean/std rejection
  integration with `flat_floor=0.05` elapsed time: 64.94495560001815 s, a raw
  timing speedup of 16.82x.

WBPP fast-integration settings observed from user-generated logs:

- Inputs: calibrated `Light` XISF files, Float32.
- Reference frame: `LIGHT_H_0136_c.xisf`.
- Full alignment: enabled.
- Pixel interpolation: Lanczos3.
- Weighting: disabled.
- Rejection: enabled, Winsorized Sigma Clipping, sigma low/high 3.0.
- Rejection maps: enabled.
- Output: 193 of 200 light frames integrated.
- Autocrop was also generated as a separate master.

Stage comparison status:

- GPWBPP and WBPP master bias/dark/flat agree closely after the expected FITS
  integer-to-Float32 scale is accounted for.
- A single calibrated light agrees in the central 98%+ of pixels after applying
  the WBPP calibrated-light pedestal/normalization convention.
- Remaining full-image differences are dominated by low-flat/out-of-range
  pixels, WBPP cosmetic correction, WBPP fast-integration alignment, rejection,
  and the seven frames not integrated by WBPP.

Current artifacts:

```text
C:\gpwbpp_runs\final_m38_h_200\stage_compare_light_0001_v2.json
C:\gpwbpp_runs\final_m38_h_200\resident_vs_wbpp_pedestal_scaled_compare.json
C:\gpwbpp_runs\final_m38_h_200\resident_vs_wbpp_pedestal_scaled_compare.html
C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_winsorized_flatfloor005_run
C:\gpwbpp_runs\final_m38_h_200\winsorized_flatfloor005_scaled_resident_vs_wbpp_compare.json
C:\gpwbpp_runs\final_m38_h_200\winsorized_flatfloor005_scaled_resident_vs_wbpp_compare.html
```

The current result proves a high-VRAM GPWBPP calibration/integration speed
advantage for this dataset, but it does not yet prove full WBPP-equivalent final
master parity. Full parity requires implementing or matching WBPP's
fast-integration alignment, rejection, cosmetic correction, output
normalization, and failed-frame policy.
