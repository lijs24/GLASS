# Registration Model

Registration starts from a CPU baseline: detect bright local maxima, measure
centroids, match stars, estimate translation/similarity/affine transforms, and
record the accepted model.

Each frame produces a registration result with matched star count, inliers,
RMS, status, and warnings. Failed frames are never silently integrated.

The current pipeline registration path first uses GPWBPP's own streaming star
detector and a clean-room matcher. Translation candidates come from star-pair
offsets; similarity/affine candidates come from simple triangle descriptors and
least-squares refinement. Candidate transforms are scored by greedy one-to-one
matches within a pixel tolerance, then refined from the inlier set.

If the star model cannot meet `min_inliers`, `method=auto` falls back to phase
correlation on bounded previews and records that fallback in the warnings. For
large calibrated frames, GPWBPP builds previews with FITS tile reads and block
means, records `preview_scale`, `preview_shape`, `tile_size`, and `tile_count`,
and multiplies preview translations back to source-image pixels. Small images
stay at `preview_scale=1` for synthetic baseline tests.

Warp skips non-reference frames with failed registration status and writes them
to `warp_results.json` under `skipped_frames`; they do not enter local
normalization or integration.

CUDA registration now has a narrow pure-GPU translation baseline:
`estimate_translation_search_f32(reference, moving, max_shift_x, max_shift_y)`
scores every integer shift with normalized cross-correlation and selects the
best shift on the device. The returned shift is directly compatible with
`warp_translation_f32`. This path is useful for controlled tests, diagnostics,
and high-VRAM resident timing, but it is intentionally labeled as
`translation_integer_ncc`; it does not yet replace star-asterism matching,
similarity/affine transforms, or higher-order interpolation.

`estimate_translation_subpixel_ncc_f32(reference, moving, center_dx, center_dy,
radius_steps, step)` refines a coarse translation on the GPU by scoring a
bounded fractional-offset grid with bilinear sampling and normalized
cross-correlation. The benchmark records both the refinement-only timing and the
fair end-to-end `translation_integer_ncc_then_subpixel_ncc` timing, which is the
integer NCC search plus the subpixel refinement. On a 1024x1024 M38 crop pair,
that combined path measured about 0.131 s versus astroalign's 0.310 s, with
pixel RMS 63.80 versus astroalign's 72.35 for this translation-only diagnostic.

The resident high-VRAM path now exposes the same integer NCC plus subpixel NCC
operations as `ResidentCalibratedStack.estimate_translation_to_reference(...)`
and `ResidentCalibratedStack.estimate_translation_subpixel_to_reference(...)`.
`ResidentCalibratedStack.apply_translation_bilinear_frame(...)` then applies
the floating-point translation in place on the resident frame. In the same M38
1024x1024 crop comparison, the resident device-only path measured about 0.070 s
with the same 63.80 pixel RMS; including one-time upload of the two crop frames
measured about 0.071 s. This is the timing model closest to the planned
96GB-VRAM resident pipeline, where calibrated frames remain on the GPU between
calibration, registration, warp, and integration.

Resident mode also exposes `translation_star_catalog`. This path runs top-N
star candidate selection for the reference and moving resident frames on the
GPU, keeps the compact catalogs on device for pair-offset voting and
mutual-nearest refinement, then downloads only the final translation diagnostics.
It is still translation-only, but unlike NCC mode its `matched_stars`,
`inliers`, and `rms_px` fields come from GPU star-catalog evidence rather than
placeholders. This is the first resident bridge from the astroalign-style idea
of star matching toward a GPWBPP-owned GPU implementation.

`translation_star_catalog` can use either global top-N flux candidates or a
grid-distributed brightest-per-cell catalog. The grid mode is controlled by
`--resident-star-grid-cols` and `--resident-star-grid-rows`. On the calibrated
M38 pair used for the astroalign/NCC comparison, a 16x8 grid with a p99.9-like
threshold returned `dx=9.0`, `dy=0.6875`, close to astroalign's center
displacement `dx=8.887`, `dy=0.715`, with the resident device-side estimate
taking about 0.0021 s. This is diagnostic evidence, not a complete replacement
for similarity/affine matching.

For resident star-catalog runs, `--resident-star-threshold 0` enables an
auto-threshold mode. The pipeline reads compact GPU global mean/std statistics
for the reference and moving frames, derives several mean-plus-sigma threshold
trials, scores each resulting catalog alignment on the GPU, and selects the
trial with the most mutual inliers and lowest RMS. This avoids hand-tuning a
single threshold for every real dataset while keeping full-frame pixels resident
on the device.

`--resident-star-prior ncc` adds an optional resident GPU NCC prior before
catalog scoring. The pipeline estimates a coarse/subpixel translation with the
resident NCC kernels, then constrains catalog pair-offset voting to a configured
radius around that prior. This reduces false zero-shift catalog clusters in
repeated star fields while still using the catalog inlier/RMS result as the
registration diagnostic.

Resident NCC registration accepts `--resident-ncc-sample-stride`. The default
`1` preserves full-frame scoring; larger values score a regular pixel grid on
the GPU to reduce registration cost on large frames. This is a speed/accuracy
control for the current translation-only model, not a substitute for future
star-descriptor similarity/affine registration.

The next CUDA registration primitive is
`estimate_translation_from_catalogs_f32(reference_x, reference_y, moving_x,
moving_y, tolerance_px, max_abs_dx=None, max_abs_dy=None, prior_dx=None,
prior_dy=None, prior_radius_px=None)`. It consumes bounded star catalogs, forms
all pair offsets on the GPU, filters offsets outside the configured search
window and optional NCC-prior radius, scores offset clusters on the GPU, and
returns the highest-vote translation. This is the first device-side star-catalog
transform scorer; it is still translation-only and does not yet perform
one-to-one assignment as the primary score. A follow-up refinement pass now applies
mutual-nearest matching around that highest-vote translation, reports
`mutual_inliers`, averages matched catalog deltas into `refined_dx/refined_dy`,
and computes `rms_px`. It still depends on the input catalog coordinates; true
subpixel centroid measurement is not yet implemented on the GPU.

The refined catalog translation can now drive
`warp_translation_bilinear_f32`, a CUDA bilinear subpixel translation warp that
returns both the aligned image and a valid-pixel coverage mask. The current
validated scope is translation-only. Benchmark output now marks catalog
alignment as accepted only when the mutual-inlier count reaches the configured
minimum and the pixel RMS is not worse than the integer-NCC fallback. A
grid-distributed GPU star selector can keep one bright local maximum per image
cell for diagnostics. Real-data M38 tests with an NCC prior can improve pixel
RMS, but the inlier evidence is still too weak to replace the fallback without
descriptor-level matching.

Similarity, affine, homography, Lanczos/resampling choices, and fully resident
frame-to-frame transform application remain future warp gates.

The clean-room astroalign comparison benchmark lives in
`benchmarks/compare_astroalign_gpu_alignment.py`. Astroalign is used as an
open-source external reference, not as GPWBPP runtime logic.
