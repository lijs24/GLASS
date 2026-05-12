# Registration Model

Registration starts from a CPU baseline: detect bright local maxima, measure
centroids, estimate translation, then extend to similarity and affine models.

Each frame produces a registration result with matched star count, inliers,
RMS, status, and warnings. Failed frames are never silently integrated.

