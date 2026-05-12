# Gates

Gate 0: engineering skeleton and clean-room constraints. The repository is
installable, testable, documented, and has CUDA as an optional future backend.

Gate 1: metadata scan, planning, report, and audit. FITS/XISF headers are read
without loading full images. Plans record matching and mismatch warnings.

Gate 2: synthetic FITS data and CPU calibration baseline. Master bias, dark,
flat, and light calibration are validated on small controlled data.

Gate 3: CUDA extension skeleton. `gpwbpp_cuda` imports when built, reports
devices, and passes smoke tests. Missing CUDA skips tests.

Gate 4: CUDA tile calibration. Calibration kernels match CPU results within
tolerance.

Gate 5: CUDA streaming master frames. Bias, dark, and flat masters are built by
tile/slab processing.

Gate 6: light calibration streaming. Light frames calibrate by tile with cache
and resume state.

Gate 7: star detection and quality metrics. Frame quality JSON and reference
selection are produced.

Gate 8: registration. Translation, similarity, and affine results are recorded
with inliers, RMS, status, and warnings.

Gate 9: warp streaming. Registered tiles and coverage/valid masks are produced.

Gate 10: local normalization. Tile/window background and scale matching are
recorded and can be disabled.

Gate 11: weighted integration and rejection. Master, weight, coverage, and
low/high rejection maps are produced.

Gate 12: end-to-end CUDA WBPP-like pipeline. Audit runs through final master on
CUDA with CPU comparison on small data.

Gate 13: PixInsight/WBPP black-box comparison. User-generated references are
compared without using official source.

Gate 14: optional PixInsight front-end. A separate GUI may call the open GPWBPP
CLI without modifying or copying official WBPP.

Phase B gates are advanced features such as drizzle, OSC CFA workflows, mosaic,
comet alignment, astrometric integration, and richer front-ends.

