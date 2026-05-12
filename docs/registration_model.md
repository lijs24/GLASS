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
subpixel refinement, similarity/affine transforms, or higher-order interpolation.

The next CUDA registration primitive is
`estimate_translation_from_catalogs_f32(reference_x, reference_y, moving_x,
moving_y, tolerance_px, max_abs_dx=None, max_abs_dy=None)`. It consumes bounded
star catalogs, forms all pair offsets on the GPU, filters offsets outside the
configured search window, scores offset clusters on the GPU, and returns the
highest-vote translation. This is the first device-side star-catalog transform
scorer; it is still translation-only and does not yet perform one-to-one
assignment as the primary score. A follow-up refinement pass now applies
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
cell for diagnostics, but real-data M38 tests still show that descriptor-level
matching is needed before catalog alignment should replace the fallback.
Similarity, affine, homography, Lanczos/resampling choices, and fully resident
frame-to-frame transform application remain future warp gates.

The clean-room astroalign comparison benchmark lives in
`benchmarks/compare_astroalign_gpu_alignment.py`. Astroalign is used as an
open-source external reference, not as GPWBPP runtime logic.
