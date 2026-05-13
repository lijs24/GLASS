# Registration Model

Registration starts from a CPU baseline: detect bright local maxima, measure
centroids, match stars, estimate translation/similarity/affine transforms, and
record the accepted model.

Each frame produces a registration result with matched star count, inliers,
RMS, status, and warnings. Failed frames are never silently integrated.

## Clean-room StarAlignment reference

The PixInsight StarAlignment reference for GPWBPP is limited to public
documentation, public forum discussion, user-generated logs, process settings,
and black-box output artifacts. PixInsight/WBPP/PJSR source code is not used.

Public PixInsight material describes StarAlignment as a star-reference image
registration process built around detected stars, geometrical descriptors,
robust match rejection, and optional local distortion correction. The relevant
clean-room observations are:

- Older StarAlignment versions used triangle-similarity matching, which is
  invariant to translation, rotation, and uniform scale but is weaker for
  projective or locally distorted data.
- Newer StarAlignment material describes polygonal descriptors: quads,
  pentagons, hexagons, heptagons, and octagons, with pentagons as the default.
  The two most distant stars define a local coordinate system; the remaining
  polygon stars form a compact coordinate hash. This lowers descriptor
  ambiguity relative to single triangles and reduces false putative matches.
- RANSAC is used to reject false star-pair matches and optimize the
  registration model. User-visible failures such as "unable to find a valid set
  of star pair matches" are treated in GPWBPP as failed registration rows, not
  silent integration inputs.
- Distortion correction is described as an iterative predictor-corrector model:
  an initial projective/linear model predicts putative matches, RANSAC validates
  and corrects the model, and two-dimensional surface splines/thin plates can
  model local residual distortion.
- Public forum guidance notes that default polygonal descriptors do not support
  specular mirror transformations. For GPWBPP this is separate from a meridian
  flip that is represented as a 180-degree rotation with positive determinant.

Sources:

- https://www.pixinsight.com/tutorials/sa-distortion/index.html
- https://pixinsight.com/forum/index.php?threads%2Fstaralignment-of-dissimilar-images.17826%2F=
- https://pixinsight.com/forum/index.php?threads%2Fstaralignment-confusion.17047%2F=

The implementation implication is that GPWBPP should not keep extending simple
pair-offset voting as the final registration model. The next robust path is a
bounded GPU star catalog, quad/pentagon-style descriptor generation, batched
GPU hypothesis scoring, CPU-orchestrated RANSAC as an interim step, and resident
CUDA matrix/homography/thin-plate warp application.

## Open-source astroalign bridge

GPWBPP also keeps `astroalign` as an open-source correctness bridge for
asterism matching. The installed local package inspected during Gate 08 was
`astroalign 2.6.2`, with MIT license metadata. Its implementation is small
enough to serve as a clear migration target:

- `sep.Background` and `sep.extract` detect source centroids, sorted by flux.
- At most `max_control_points` sources are kept for matching.
- For each source, a KD-tree query keeps a local nearest-neighbor set. The
  implementation's default is five neighbors including the source.
- All 3-point combinations from that local neighborhood form triangle
  asterisms. Each triangle is ordered consistently by side lengths.
- A triangle invariant is the ratio of the longest to middle side and the
  middle to shortest side. These two numbers are matched with a KD-tree radius.
- Matched triangle pairs are fed to a RANSAC loop. A candidate similarity
  transform is fitted from one triangle pair, other triangle pairs are accepted
  when their maximum vertex residual is below the pixel tolerance, and the
  transform is refit from inliers.
- Duplicate source-to-target point assignments are reduced by keeping the pair
  with the lowest reprojection error.

This is less general than PixInsight's public polygonal descriptor model, but
it is a practical bridge because the code is open, compact, and already passes
our tile-mode real-data registration tests. The GPU migration should happen in
three explicit stages:

1. Keep astroalign/SEP as the CPU baseline and write golden star-pair and matrix
   artifacts for representative real frames.
2. Port the triangle asterism pipeline to CUDA with resident star catalogs:
   local KNN, triangle invariant generation, invariant radius matching, batched
   similarity fit, and batched inlier scoring.
3. Extend the descriptor generator from triangles to quads/pentagons, then use
   the same batched GPU hypothesis scoring and resident matrix warp.

The short-term target is not source-level compatibility with astroalign, but
behavioral equivalence on a fixed set of star catalogs and a much faster
resident CUDA implementation for high-VRAM WBPP-like runs.

`gpwbpp.cpu.registration.estimate_triangle_asterism_transform` is the current
owned CPU bridge for that migration. It builds local nearest-neighbor triangle
descriptors from bounded star catalogs, matches scale-invariant side-ratio
descriptors, fits similarity or affine hypotheses, scores one-to-one inliers,
and refits from accepted pairs. Tests compare it against synthetic known
similarity transforms and against the optional MIT-licensed `astroalign`
backend on the same small star-field image pair. This keeps the GPU port target
auditable before the local-KNN, descriptor matching, and hypothesis scoring
steps move fully onto CUDA.

`gpwbpp_cuda.triangle_asterism_descriptors_f32(x, y, max_stars, neighbors,
max_descriptors)` is the first CUDA primitive for that bridge. It takes compact
catalog coordinates, computes local nearest-neighbor triangle descriptors on
the device, and returns deduplicated descriptor/index/area arrays for comparison
or downstream matching. The current host wrapper still performs deduplication
and area ordering after downloading compact descriptor arrays; descriptor
matching and RANSAC-style hypothesis selection remain follow-up CUDA work.

`gpwbpp_cuda.estimate_similarity_from_triangle_descriptors_f32(...)` adds the
next device-side step: descriptor-pair candidates are filtered by side-ratio
distance on the GPU, both triangle orientations are tried, similarity matrices
are fitted from the triangle vertices, and compact star catalogs are scored by
mutual nearest-neighbor inliers. The current test scope is a controlled
synthetic catalog with a known similarity transform; robust multi-hypothesis
selection on real M38 frames and resident pipeline wiring remain open.

`gpwbpp.gpu.registration.register_triangle_descriptor_similarity_f32(...)` wires
the controlled image-pair loop: CUDA star catalog extraction, CUDA triangle
descriptor generation, CUDA triangle-descriptor similarity scoring, and CUDA
matrix warp. The current unit test validates that this loop improves alignment
on a synthetic rotated/translated star field. The astroalign comparison
benchmark now records this path as
`gpwbpp_cuda_triangle_descriptor_similarity`, including descriptor counts,
candidate count, transform/output agreement versus astroalign, and speedup. A
small synthetic benchmark smoke artifact is written under
`runs/benchmarks/triangle_descriptor_synthetic_smoke.json`.

The first real M38 pair rerun exposed an important selector problem: applying
NMS after scanning only `max_candidates` brightest stars reduced the descriptor
catalog to 10/10 stars and selected an identity-like false match. The helper now
uses the same grid-top NMS selector as the catalog-similarity benchmark when
grid parameters are provided, and defaults top-NMS scanning to 4096 candidates
when no explicit scan count is provided. With the full calibrated M38
`S000061`/`S000062` pair, artifact
`C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v47_triangle_gridtop.json`
records `gpwbpp_cuda_triangle_descriptor_similarity` passing the agreement gate:
64/64 stored stars, 341/335 triangle descriptors, 47 inliers,
`translation_delta_px=0.295`, output RMS difference about 38.27 ADU, and
elapsed time about 0.327 s versus astroalign's 9.72 s. This is the first
accepted pure CUDA descriptor path on the representative real pair.

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

Tile-mode registration accepts `--reference-frame-id`, matching a frame id,
calibrated-cache file name/stem, or the original frame file name/stem from the
processing plan. This makes real-data comparisons reproducible when the quality
reference differs from the desired black-box or pairwise diagnostic reference.
`--registration-preview-max-dimension` controls the streaming preview scale.
When `--registration-method astroalign` is selected, a per-frame astroalign
failure is recorded as `status=failed` instead of aborting the whole registration
stage.

Tile-mode registration can also use the optional open-source `astroalign`
backend with `gpwbpp run --registration-method astroalign`. This path calls
`astroalign.find_transform` on the same streaming preview images and records the
resulting similarity matrix, matched control-point count, preview-scale RMS, and
MIT-license provenance in `registration_results.json`. It is the current
open-source CPU correctness baseline for star/asterism matching and a bridge
toward GPWBPP-owned GPU descriptor registration. The tile warp stage now uses a
streaming bilinear matrix warp for fractional translation, similarity, and
affine matrices, so astroalign's similarity matrix can flow into downstream
integration without loading a full frame into memory.

Tile-mode registration now also exposes the clean-room GPU path with
`gpwbpp run --registration-method cuda_catalog` or
`gpwbpp audit --registration-method cuda_catalog`. It builds the same bounded
streaming previews, requires the native CUDA backend, selects compact star
catalogs on the GPU, estimates a similarity matrix with the CUDA mutual
catalog scorer, optionally constrains the search with a CUDA NCC prior, and
refines only the matrix translation terms with CUDA pixel metrics. The preview
matrix translation is scaled back to source-image pixels before it is written
to `registration_results.json`, so the existing streaming matrix warp can
consume it. Each row records `cuda_catalog` diagnostics including candidate
counts, thresholds, prior details, preview RMS, pixel metric RMS/NCC, and
refit status.

Tile-mode registration also exposes the GPU triangle-descriptor path with
`gpwbpp run --registration-method cuda_triangle` or
`gpwbpp audit --registration-method cuda_triangle`. This method uses bounded
streaming previews, GPU top-N or grid-top NMS star selection, GPU triangle
asterism descriptor construction, and CUDA descriptor matching to estimate a
similarity matrix. The matrix translation is scaled from preview pixels back to
source pixels before `registration_results.json` is written. Each non-reference
row records `cuda_triangle` diagnostics including star counts, descriptor
counts, descriptor radius, neighbor count, candidate count, preview RMS, and the
selector used. This is the first formal pipeline entry for the pure-GPU
descriptor route that was validated against astroalign on the representative
full-size M38 pair.

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

`--resident-ncc-fallback-score-threshold` can be used with a sampling stride
greater than one. When the sampled NCC subpixel score is at or below the
threshold, the frame is re-estimated with full stride `1` and the fallback is
recorded in the registration warnings. The default `0` disables fallback and
preserves the exact requested stride behavior.

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

`estimate_similarity_from_pairs_f32(reference_x, reference_y, moving_x,
moving_y)` is the first CUDA transform-estimation primitive beyond pure
translation. It assumes a one-to-one matched star catalog has already been
produced, then fits the moving-to-reference 2D similarity transform on the GPU
with finite-pair filtering and returns the 3x3 matrix, scale, rotation, valid
pair count, and RMS. This is deliberately a lower-level building block: the
remaining hard problem is GPU descriptor matching and robust inlier selection,
not the closed-form similarity fit once trustworthy pairs exist.
The astroalign comparison benchmark now exercises this bridge by using
astroalign only for matched control points, then fitting the similarity matrix
with `estimate_similarity_from_pairs_f32` and applying it with CUDA matrix warp.
On the full calibrated M38 `S000061`/`S000062` pair, that path fit 50 matched
pairs with 0.134 px fit RMS; GPU fit plus standalone CUDA warp took about
0.092 s versus astroalign's 2.865 s apply stage, while the resulting image had
about 3.98 ADU median absolute difference and 12.00 ADU RMS difference against
astroalign apply on common valid pixels.

`estimate_similarity_from_catalogs_f32(reference_x, reference_y, moving_x,
moving_y, tolerance_px, min_pair_distance)` is the first pure-GPU seed matcher
for similarity transforms from compact catalogs. It forms ordered two-star pair
candidates directly on the device, fits a similarity transform for each
candidate, scores transformed moving stars against the reference catalog, and
returns the highest-inlier matrix with RMS diagnostics. The validated scope is
small bounded catalogs with outliers; it is a stepping stone toward descriptor
matching and robust RANSAC, not yet the final high-resolution registration
model.
`gpwbpp.gpu.registration.register_similarity_from_star_catalogs_f32` wires this
into the first controlled image-registration loop: GPU star-catalog extraction,
GPU catalog similarity seed, then GPU matrix warp. The synthetic test covers a
rotated/scaled star field and verifies that the closed loop improves image RMS
and recovers the expected similarity matrix within subpixel/catalog-detection
limits.

The catalog path now includes two guardrails for real frames. First,
`star_top_nms_candidates_f32` performs CUDA-side minimum-distance suppression
after bright local-maximum selection, which avoids filling compact catalogs with
multiple peaks from the same saturated star. Second,
`estimate_similarity_from_catalogs_f32` can constrain candidate two-star seeds
by a prior translation, scale range, and rotation range. The intended prior is
the GPU NCC coarse alignment, so the seed search remains clean-room and
GPWBPP-owned. On the recorded full-frame M38 pair, this pure GPWBPP GPU path
accepted 12 inliers and produced a matrix close to astroalign, but the current
brute-force implementation is still slower than astroalign because top-NMS and
best-candidate selection are not yet optimized.

`star_grid_top_nms_candidates_f32` adds a faster large-frame prefilter: each
grid cell keeps its top-K local maxima on the GPU, then a CUDA NMS pass compacts
the spatially distributed candidates into the bounded catalog. On the same full
M38 `S000061`/`S000062` pair, the grid-top pure GPU catalog-similarity path took
about 2.96 s versus astroalign's 9.57 s total, but the resulting transform did
not pass the benchmark agreement check against astroalign
(`translation_delta_px=1.56`, output RMS difference about 75.68 ADU), so the
benchmark now marks it `accepted=false`. This is a useful speed signal for the
final GPU matcher, not yet the accepted production registration path.

The catalog-similarity seed now has a guarded CUDA refit pass. After the best
two-star seed is selected, the GPU gathers nearest-neighbor star inliers for
that seed and fits a similarity matrix from the inlier sums. The refit only
replaces the seed when its star-catalog residual does not worsen; otherwise the
seed matrix is kept and `refit_status=rejected` is recorded. This prevents the
real M38 pair from regressing when the nearest-neighbor inliers are not clean
enough.

`refine_matrix_translation_with_metrics_f32(...)` adds a CUDA pixel-metric
translation refinement for an existing similarity/affine matrix. It scores a
small translation grid with `matrix_alignment_metrics_f32` and returns the
matrix with the lowest RMS/highest NCC. The native backend now batches each
coarse or fine candidate grid into a single CUDA launch after uploading the
two images once; CPU fallback keeps the older per-candidate loop for
installations without the native primitive. On the M38
grid-top benchmark artifact
`C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v20_gridtop_pixel_refine.json`,
pixel refinement improved the catalog-similarity output RMS difference versus
astroalign apply to about 58.89 ADU, but it still failed the current agreement
gate (`translation_delta_px=1.25`, limit 0.5; output RMS limit 55). The result
is therefore useful progress, not a completed replacement for astroalign's
asterism matcher.

The similarity seed scorer now counts mutual nearest-neighbor star matches
rather than one-way nearest-reference hits. This suppresses duplicate matches
from repeated or clustered stars before the guarded refit runs. With the same
M38 pair and grid-top parameters, artifact
`C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v22_mutual_score_pixel_refine_accept.json`
records the first accepted clean-room GPU catalog path for this pair:
`catalog_similarity_pixel_refined_agreement_vs_astroalign.passed=true`,
translation delta about 0.482 px, output RMS difference about 38.53 ADU, and
elapsed time about 6.42 s versus astroalign's 9.70 s total. After the fused
candidate-grid refine primitive, artifact
`C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v23_fused_pixel_refine.json`
reduced the pixel-refine search itself to about 0.235 s and the catalog
similarity plus refine plus warp path to about 0.328 s. That v23 run did not
pass the strict astroalign matrix-agreement threshold because the upstream
catalog seed selected a different near-solution, so the speed primitive is
validated but the robust catalog matcher still needs work before the full
200-frame benchmark.

GPU matrix bilinear warp is now available as both a standalone array function
and an in-place resident-frame operation. This validates the CUDA primitive
needed to apply similarity and affine matrices without falling back to CPU pixel
warping. Automatic resident pipeline wiring for non-translation registration
matrices, homography, Lanczos/resampling choices, and higher-level acceptance
policy remain future warp gates.

The clean-room astroalign comparison benchmark lives in
`benchmarks/compare_astroalign_gpu_alignment.py`. Astroalign is used as an
open-source external reference and, when `gpwbpp[align]` is installed, as an
optional tile-mode registration backend.
The benchmark now records astroalign's transform search and pixel application
timings separately, then applies the same astroalign similarity matrix with
GPWBPP's standalone CUDA matrix warp and resident in-place CUDA matrix warp.
This isolates star/asterism matching cost from pixel resampling cost while the
owned GPU matcher is still catching up.
It also records a direct common-valid-pixel difference between astroalign's
`apply_transform` output and GPWBPP's CUDA matrix-warp output. This keeps the
alignment timing claim tied to a numeric image-consistency check in the same
JSON artifact. In the full calibrated M38 pair
`S000061`/`S000062`, the refreshed artifact
`C:\gpwbpp_runs\final_m38_h_200\astroalign_vs_gpwbpp_gpu_pair_S000061_S000062_full_benchmark_v16_resident_matrix_metrics.json`
measured standalone CUDA matrix warp at about 0.146 s versus astroalign apply at
about 2.840 s, and resident device-only matrix warp at about 0.0069 s. On the
61,632,460 common valid pixels, the CUDA matrix output versus astroalign apply
had median absolute difference about 3.98 ADU and RMS difference about 12.02 ADU.
The same artifact also records `catalog_similarity_agreement_vs_astroalign` so a
fast owned-GPU matcher cannot be marked accepted unless its matrix and output
image agree with the open-source reference.

The benchmark also records `matrix_alignment_metrics_f32` results. For the
astroalign matrix, GPU matrix metrics reported RMS 76.35 ADU and NCC 0.9767 in
about 0.038 s, matching the full CUDA warp RMS without downloading the warped
image. Resident matrix metrics reported the same RMS/NCC in about 0.0015 s
device time after the two frames were already loaded on the GPU. For the current
grid-top catalog-similarity matrix, the same metric
reported RMS 97.07 ADU and NCC 0.9623, which is enough evidence to reject that
fast candidate before it enters integration.
The same metric is now exposed on `ResidentCalibratedStack` as
`matrix_alignment_metrics_to_reference`, so a 96GB-VRAM run can score a
candidate similarity/affine matrix against two resident calibrated frames and
download only compact RMS/NCC diagnostics.

Resident runs can also use `--resident-registration external_matrix` together
with `--resident-registration-results <registration_results.json>`. That mode
keeps the high-VRAM calibration/integration path but consumes a prior
registration artifact: accepted translation matrices use the resident
translation bilinear warp, and accepted similarity/affine matrices use the
resident CUDA matrix bilinear warp. This is intended for staged validation,
for example running tile-mode `--registration-method astroalign` first, then
using the resulting matrices to test pure GPU pixel resampling and integration.

Resident runs can now use `--resident-registration similarity_cuda_triangle` as
the first high-VRAM bridge for the triangle descriptor route. Calibrated frames
remain in the `ResidentCalibratedStack`; the stack detects compact star
catalogs on the GPU, GPWBPP builds/matches CUDA triangle descriptors from those
catalogs, and the selected similarity matrix is applied in place with resident
CUDA matrix bilinear warp. This still downloads compact catalogs/diagnostics,
so it is not the final fully resident descriptor primitive, but it avoids
materializing calibrated or registered full frames on the host.
