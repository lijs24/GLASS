# Registration Model

Registration starts from a CPU baseline: detect bright local maxima, measure
centroids, estimate translation, then extend to similarity and affine models.

Each frame produces a registration result with matched star count, inliers,
RMS, status, and warnings. Failed frames are never silently integrated.

The current pipeline registration path estimates translation with CPU phase
correlation on bounded previews. For large calibrated frames, GPWBPP builds the
preview with FITS tile reads and block means, records `preview_scale`,
`preview_shape`, `tile_size`, and `tile_count`, and multiplies the preview
translation back to source-image pixels. Small images stay at `preview_scale=1`
for synthetic baseline tests.
