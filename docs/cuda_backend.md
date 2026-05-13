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
- `triangle_asterism_descriptors_f32(x, y, max_stars=80, neighbors=5, max_descriptors=1200)`
- `estimate_similarity_from_triangle_descriptors_f32(reference_x, reference_y, moving_x, moving_y, reference_descriptors, reference_indices, moving_descriptors, moving_indices, tolerance_px=2.0, descriptor_radius=0.1)`
- `estimate_similarity_from_catalogs_f32(reference_x, reference_y, moving_x, moving_y, tolerance_px=2.0, min_pair_distance=2.0)`
- `warp_translation_bilinear_f32(data, dx, dy, fill)`
- `star_local_max_mask_f32(tile, threshold)`
- `star_candidates_f32(tile, threshold, max_candidates)`
- `star_top_candidates_f32(tile, threshold, max_candidates)`
- `star_grid_candidates_f32(tile, threshold, grid_cols, grid_rows)`
- `ResidentCalibratedStack.integrate_sigma_clip(...)`
- `ResidentCalibratedStack.apply_translation_frame(...)`
- `ResidentCalibratedStack.apply_translation_bilinear_frame(...)`
- `ResidentCalibratedStack.apply_matrix_bilinear_frame(...)`
- `ResidentCalibratedStack.apply_matrix_lanczos3_frame(...)`
- `ResidentCalibratedStack.matrix_alignment_metrics_to_reference(...)`
- `ResidentCalibratedStack.estimate_translation_to_reference(...)`
- `ResidentCalibratedStack.estimate_translation_subpixel_to_reference(...)`
- `ResidentCalibratedStack.frame_global_stats(index)`
- `ResidentCalibratedStack.apply_global_normalization_frame(index, scale, offset)`
- `ResidentCalibratedStack.apply_grid_normalization_frame(index, scales, offsets, tile_height, tile_width)`
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
- GPU triangle asterism descriptor generation from compact star catalogs. The
  kernel computes local nearest-neighbor triangle side-ratio descriptors on the
  device and returns compact descriptor/index/area arrays. Host-side
  deduplication and ordering remain in the current wrapper while descriptor
  matching and hypothesis selection are still being migrated.
- GPU triangle-descriptor similarity scoring. The primitive filters descriptor
  pairs by radius on the device, tries both ordered-triangle orientations, fits
  moving-to-reference similarity matrices from triangle vertices, and scores
  compact catalogs with mutual nearest-neighbor inliers.
- GPU bounded-catalog similarity seed matching. The primitive forms ordered
  two-star pair candidates from compact reference and moving catalogs, fits a
  candidate similarity transform, scores transformed moving stars against the
  reference catalog, and returns the highest-inlier matrix with RMS diagnostics.
  This is intentionally scoped to compact catalogs and is not yet a full robust
  descriptor/RANSAC implementation.
- `gpwbpp.gpu.registration.register_similarity_from_star_catalogs_f32(...)`
  provides a Python orchestration helper for controlled tests: it extracts GPU
  star catalogs from two images, estimates the similarity seed on the GPU, and
  applies the resulting matrix with the CUDA bilinear warp.
- `gpwbpp.gpu.registration.register_triangle_descriptor_similarity_f32(...)`
  provides the triangle-descriptor orchestration helper: GPU star catalogs,
  CUDA triangle descriptors, CUDA descriptor-based similarity scoring, then
  CUDA matrix warp. It is currently validated on a controlled synthetic image
  pair and is wired into `benchmarks/compare_astroalign_gpu_alignment.py` as
  `gpwbpp_cuda_triangle_descriptor_similarity` for astroalign agreement and
  timing comparisons. The helper supports grid-top NMS catalog selection and
  defaults global top-NMS scanning to 4096 candidates when only a minimum
  separation is provided. This avoids the real-frame failure mode where NMS
  scans only the first `max_candidates` bright structures and leaves too sparse
  a descriptor catalog.
- `star_top_nms_candidates_f32(...)` adds a CUDA-side top-candidate selection
  plus minimum-distance suppression step. This reduces duplicated local maxima
  around saturated stars before catalog matching.
- `star_grid_top_nms_candidates_f32(...)` keeps the top-K local maxima per image
  grid cell on the GPU, then runs the same CUDA NMS compaction. It is a faster
  spatially distributed catalog prefilter for large real frames.
- `estimate_similarity_from_catalogs_f32(...)` now accepts optional priors for
  translation, scale, and rotation. The real M38 pair benchmark can run a
  fully GPWBPP-owned path (GPU star candidates -> GPU NMS catalog -> GPU
  constrained similarity seed -> GPU matrix warp) without astroalign control
  points. The global top-NMS path has produced an astroalign-close matrix on the
  recorded pair but is still slow. The new grid-top prefilter is much faster,
  but the current seed scorer can still choose an astroalign-disagreeing
  transform, so benchmark artifacts record both internal acceptance and external
  agreement checks.
- Catalog similarity now performs a guarded GPU refit from the best seed's
  nearest-neighbor star inliers. The refit is applied only if its star-catalog
  residual does not worsen; diagnostics report `refined_inliers`,
  `refit_status`, and `refit_rms_px`.
- Catalog similarity seed scoring now uses mutual nearest-neighbor star matches
  under the candidate transform instead of one-way nearest-reference hits. This
  reduces duplicate-match false positives in compact catalogs.
- `gpwbpp.gpu.registration.refine_matrix_translation_with_metrics_f32(...)`
  uses CUDA matrix metrics to search a small translation correction around an
  existing matrix. It is a diagnostic bridge toward pixel-evidence transform
  scoring. The native implementation now batches a whole coarse or fine
  candidate grid into one CUDA launch after uploading the reference/moving
  images once; CPU fallback keeps the per-candidate metric loop only when the
  native extension is unavailable.
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
- Resident grid local-normalization support. `ResidentCalibratedStack.frame_pair_grid_stats`
  computes per-tile paired source/reference mean and standard deviation on the
  GPU, and `ResidentCalibratedStack.apply_grid_normalization_frame` applies the
  resulting coefficient table directly to the loaded frame in VRAM. CLI resident
  runs select this with `--resident-local-normalization-mode grid_mean_std`.
- GPU bilinear subpixel translation warp, returning a warped frame and
  coverage mask. This is the first CUDA warp primitive that can consume the
  refined floating-point catalog translation directly.
- GPU bilinear matrix warp, returning a warped frame and coverage mask for an
  invertible 3x3 source-to-destination transform matrix. Resident stacks expose
  the same primitive as an in-place frame warp, which is the first CUDA bridge
  toward consuming similarity/affine registration matrices.
- GPU Lanczos3 matrix warp, returning the same warped-frame and coverage-map
  contract as the bilinear matrix warp. Resident stacks expose it as
  `apply_matrix_lanczos3_frame`; resident runs select it with
  `--resident-warp-interpolation lanczos3`. The optional
  `--resident-warp-clamping-threshold` applies a clean-room local overshoot
  limiter around the Lanczos support window. This is a WBPP-like interpolation
  control for black-box comparisons, not a claim of PixInsight-internal
  equivalence.
- `matrix_alignment_metrics_f32(reference, moving, matrix, sample_stride=1)`
  scores a moving-to-reference matrix directly on the GPU without downloading a
  full warped image. It returns valid-pixel count, RMS, mean absolute difference,
  and normalized cross-correlation. This is the first pixel-metric validation
  primitive for rejecting fast but incorrect catalog transforms.
- `ResidentCalibratedStack.matrix_alignment_metrics_to_reference(...)` runs the
  same matrix score directly between two already-loaded resident frames. It
  downloads only compact metric totals, so high-VRAM alignment experiments can
  validate candidate matrices without re-uploading or materializing a warped
  image on the host.
- Resident runs can consume a prior `registration_results.json` with
  `--resident-registration external_matrix` and
  `--resident-registration-results`. Accepted translation matrices keep the
  resident translation bilinear path by default; accepted similarity/affine
  matrices use the selected resident CUDA matrix warp before local normalization
  and integration. The default remains bilinear for continuity, while Lanczos3
  can be enabled explicitly for WBPP-like comparison runs.
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
- Tile-mode `--registration-method cuda_triangle` is now a first-class pipeline
  entry. It uses the native CUDA star candidate selector, triangle descriptor
  construction, descriptor matching, and bilinear matrix warp on bounded
  streaming previews, then writes the source-pixel similarity matrix and compact
  descriptor diagnostics to `registration_results.json`.
- Resident `--resident-registration similarity_cuda_triangle` keeps calibrated
  frames in the high-VRAM `ResidentCalibratedStack`, reuses resident GPU star
  catalog detection, runs CUDA triangle descriptor construction/matching on the
  compact catalogs, and applies the selected similarity matrix with resident
  matrix bilinear warp. The current bridge still returns compact catalogs to
  host-side Python orchestration; a later native primitive should keep descriptor
  assembly and matching fully resident.
- Resident similarity registration can use `--resident-star-prior auto_pierside`.
  This reads only `PIERSIDE` metadata from `header_summary` or FITS headers: same
  pier side uses the fast NCC-constrained prior, while opposite pier side disables
  that prior and widens the rotation search for meridian-flip frames.

The current resident rejection kernel is an engineering baseline for the
high-VRAM path. It is not yet a byte-for-byte reproduction of PixInsight
FastIntegration's robust rejection and alignment internals. The resident
translation path is useful for diagnosis and high-VRAM timing, but it does not
replace the star-based registration/Lanczos warp gates.

For registration, the next CUDA step is to extend the current triangle
asterism matcher toward quad/pentagon descriptors and resident-stack execution,
so similarity/affine scoring and transform application stay on the device from
bounded star catalogs. CPU should only orchestrate and receive compact
diagnostics.
