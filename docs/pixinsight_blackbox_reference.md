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

On this workstation, `PixInsight.exe` was not found in PATH or common
`Program Files` locations during Gate 13 preparation. GPWBPP real-data timing
was completed on a small M5/Lum subset, but the PixInsight/WBPP black-box timing
comparison is blocked until a local PixInsight executable or a user-generated
WBPP output/log for the same subset is available.
