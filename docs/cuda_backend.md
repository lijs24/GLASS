# CUDA Backend

The CUDA backend is optional. CPU-only installation must remain functional even
when CUDA, NVCC, or a compatible NVIDIA driver is not present.

Until the native extension is built, `src/gpwbpp_cuda.py` provides a compatibility
API. It can import, report devices visible through `nvidia-smi`, and run CPU
fallback smoke helpers. It deliberately reports `cuda_available() == false` so
tests and reports do not confuse fallback helpers with real CUDA kernels.

Gate 3 introduces the `gpwbpp_cuda` Python extension with:

- `cuda_available()`
- `list_devices()`
- `get_device_info(device_id)`
- `smoke_add_f32(a, b)`
- `reduce_mean_tile_f32(tile)`
- `calibrate_tile_f32(...)`
- `integrate_accumulate_mean_tile_f32(...)`
- `estimate_translation_search_f32(reference, moving, max_shift_x, max_shift_y)`
- `estimate_translation_subpixel_ncc_f32(reference, moving, center_dx, center_dy, radius_steps, step)`
- `estimate_translation_from_catalogs_f32(reference_x, reference_y, moving_x, moving_y, tolerance_px, max_abs_dx=None, max_abs_dy=None, prior_dx=None, prior_dy=None, prior_radius_px=None)`
- `estimate_similarity_from_pairs_f32(reference_x, reference_y, moving_x, moving_y)`
- `estimate_similarity_from_catalogs_f32(reference_x, reference_y, moving_x, moving_y, tolerance_px=2.0, min_pair_distance=2.0)`
- `warp_translation_bilinear_f32(data, dx, dy, fill)`
- `star_local_max_mask_f32(tile, threshold)`
- `star_candidates_f32(tile, threshold, max_candidates)`
- `star_top_candidates_f32(tile, threshold, max_candidates)`
- `star_grid_candidates_f32(tile, threshold, grid_cols, grid_rows)`
- `ResidentCalibratedStack.integrate_sigma_clip(...)`
- `ResidentCalibratedStack.apply_translation_frame(...)`
- `ResidentCalibratedStack.apply_translation_bilinear_frame(...)`
- `ResidentCalibratedStack.estimate_translation_to_reference(...)`
- `ResidentCalibratedStack.estimate_translation_subpixel_to_reference(...)`
- `ResidentCalibratedStack.frame_global_stats(index)`
- `ResidentCalibratedStack.apply_global_normalization_frame(index, scale, offset)`
- `ResidentCalibratedStack.star_local_max_mask(index, threshold)`
- `ResidentCalibratedStack.star_candidates(index, threshold, max_candidates)`
- `ResidentCalibratedStack.star_top_candidates(index, threshold, max_candidates)`
- `ResidentCalibratedStack.estimate_translation_from_stars_to_reference(...)`

Every CUDA operation will have a CPU reference test. If CUDA is not available,
CUDA tests skip rather than failing the whole project. Kernel launch failures
must become clear Python exceptions.

Local native build command used on Windows:

```powershell
$pybind = (& .\.venv\Scripts\python -m pybind11 --cmakedir).Trim()
cmd /c "call `"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat`" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe -S . -B build\native-cuda -G Ninja -DGPWBPP_BUILD_PYTHON_CUDA=ON -DGPWBPP_BUILD_CUDA=OFF -Dpybind11_DIR=`"$pybind`" -DCMAKE_MAKE_PROGRAM=`"$((Resolve-Path .\.venv\Scripts\ninja.exe))`" -DCMAKE_CUDA_COMPILER=`"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\nvcc.exe`" -DCMAKE_CUDA_ARCHITECTURES=120 && .\.venv\Scripts\cmake.exe --build build\native-cuda --config Release"
```

The command writes `_gpwbpp_cuda_native*.pyd` into `src/` for local testing. The
binary is ignored by git; source, CMake configuration, and tests are tracked.

Resident CUDA integration now supports:

- weighted mean for already resident calibrated frames;
- two-pass mean/std sigma clipping;
- two-stage winsorized mean/std sigma rejection approximation;
- output weight, coverage, low rejection, and high rejection maps.
- optional preview-scale phase-correlation translation registration followed by
  integer-pixel CUDA warp with NaN edge fill.
- GPU local-maximum star candidate masking on standalone tiles and directly on
  resident calibrated frames.
- GPU compaction of local maxima into bounded `(x, y, flux)` star catalogs on
  standalone tiles and directly on resident calibrated frames.
- GPU top-N selection and descending flux sorting for bounded star catalogs,
  available on standalone tiles and directly on resident calibrated frames.
- GPU grid-distributed star selection that keeps the brightest local maximum in
  each image grid cell, reducing global-brightness bias in diagnostic catalogs.
- GPU integer-translation search with per-shift normalized cross-correlation,
  followed by device-side best-shift selection and CUDA translation warp.
- GPU star-catalog pair-offset voting for translation estimation from bounded
  top-N catalogs.
- GPU mutual-nearest refinement for catalog translations, returning
  `refined_dx`, `refined_dy`, `mutual_inliers`, and `rms_px`.
- Optional GPU catalog translation search bounds (`max_abs_dx/max_abs_dy`) so
  bright outliers cannot vote for physically implausible offsets outside the
  registration search window.
- Optional NCC-prior catalog windowing so catalog votes can be restricted to a
  radius around a coarse GPU translation estimate before subpixel refinement.
- GPU similarity fitting from already matched star pairs. The primitive computes
  the moving-to-reference scale, rotation, translation matrix, valid-pair count,
  and RMS on the device. It is a building block for the planned pure-GPU
  descriptor matcher; it does not by itself solve star matching.
- GPU bounded-catalog similarity seed matching. The primitive forms ordered
  two-star pair candidates from compact reference and moving catalogs, fits a
  candidate similarity transform, scores transformed moving stars against the
  reference catalog, and returns the highest-inlier matrix with RMS diagnostics.
  This is intentionally scoped to compact catalogs and is not yet a full robust
  descriptor/RANSAC implementation.
- GPU subpixel translation refinement around a coarse NCC estimate. It evaluates
  a bounded fractional-offset grid with bilinear sampling and normalized
  cross-correlation, returning `dx`, `dy`, `score`, and candidate-count
  diagnostics.
- Resident GPU NCC supports an optional sampling stride. A stride greater than
  one scores a regular pixel grid while frames remain in VRAM, reducing
  full-frame registration cost for high-resolution timing experiments.
- Resident GPU NCC can optionally fall back to full stride `1` when the sampled
  subpixel NCC score is below a configured threshold, recording the fallback in
  per-frame registration warnings.
- Resident frame-to-frame NCC and subpixel NCC estimation, so calibrated frames
  already stored in `ResidentCalibratedStack` can be registered and warped
  without re-uploading the two images through standalone wrappers.
- Resident global mean/std local-normalization diagnostics and apply kernels,
  allowing high-VRAM runs to normalize calibrated/registered frames before
  integration without downloading full frames to the host. This is a global
  baseline, not the full tile/window LN model.
- GPU bilinear subpixel translation warp, returning a warped frame and
  coverage mask. This is the first CUDA warp primitive that can consume the
  refined floating-point catalog translation directly.
- GPU bilinear matrix warp, returning a warped frame and coverage mask for an
  invertible 3x3 source-to-destination transform matrix. Resident stacks expose
  the same primitive as an in-place frame warp, which is the first CUDA bridge
  toward consuming similarity/affine registration matrices.
- Resident runs can consume a prior `registration_results.json` with
  `--resident-registration external_matrix` and
  `--resident-registration-results`. Accepted translation matrices keep the
  resident translation bilinear path; accepted similarity/affine matrices use
  the resident CUDA matrix bilinear warp before local normalization and
  integration.
- Resident star-catalog translation registration. The resident stack detects
  top-N stars for the reference and moving frames on the GPU, scores pair-offset
  translations and mutual-nearest refinement on the GPU, then returns compact
  diagnostics before applying the translation warp in place.
- Resident star-catalog registration can optionally use the same grid-distributed
  brightest-per-cell selector, which improves real-frame evidence when global
  top-N candidates are dominated by bright outliers or clustered structure.
- Resident star-catalog registration can also run auto-threshold trials. Passing
  `--resident-star-threshold 0` derives several mean-plus-sigma thresholds from
  GPU global frame statistics, scores each candidate on the GPU, and keeps the
  result with the strongest mutual-inlier support.
- Resident star-catalog voting can optionally be constrained by a GPU NCC prior
  with `--resident-star-prior ncc`. The prior is computed from resident
  integer/subpixel NCC kernels and passed to the catalog pair-offset scorer as a
  compact `(dx, dy, radius)` search window.

The current resident rejection kernel is an engineering baseline for the
high-VRAM path. It is not yet a byte-for-byte reproduction of PixInsight
FastIntegration's robust rejection and alignment internals. The resident
translation path is useful for diagnosis and high-VRAM timing, but it does not
replace the star-based registration/Lanczos warp gates.

For registration, the next CUDA step is to run asterism matching,
similarity/affine scoring, and transform application on the device from bounded
star catalogs. CPU should only orchestrate and receive compact diagnostics.
