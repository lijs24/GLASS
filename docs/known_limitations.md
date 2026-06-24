# Known Limitations

Current code is intentionally gated:

- XISF parsing is provisional and limited to the XML prefix.
- CPU registration currently estimates only simple translation from ordered
  star lists.
- Local normalization has resident CUDA global/grid mean-std support and is part
  of the default high-VRAM path. S2-Gate 612 applies the per-frame LN transform
  in place in VRAM, and S2-Gate 613 batches resident grid-LN statistics across
  all active non-reference source frames. S2-Gate 615 also batches resident
  grid-LN apply across all active non-reference source frames with one
  coefficient upload and one batch synchronization. The remaining LN throughput
  target is to move coefficient construction closer to native/CUDA code and
  reduce the Python result-row orchestration that still surrounds the in-VRAM
  stats/apply calls.
- HTML reports include required sections but many stage-specific tables remain
  pending until their gates produce artifacts.
- The resident CUDA path keeps calibrated light frames in VRAM and is fast on
  large same-shape mono datasets. It currently performs calibration, resident
  similarity-triangle registration, Lanczos3 matrix warp, local normalization,
  and mean/sigma/winsorized integration for the default high-VRAM path.
  S2-Gate 616 sets the default resident matrix-warp chunk capacity to `8`
  frames after real 200-light probes showed larger chunks used much more VRAM
  and slowed the current Lanczos3 batch kernel; explicit chunk-capacity
  overrides remain available for profiling.
  Resident `winsorized_sigma` defaults to an `auto` resolver: supported
  stack-dispatch audit/science groups with at most 512 frames use the hardened
  median/IQR CUDA path that matches the GLASS CPU baseline. For large default
  auto groups above 64 frames, GLASS applies the Gate600/603
  coverage-preserving `rejection_max_fraction=0.015` guard unless the plan or
  CLI explicitly supplies a guard. Groups above the native 512-frame CUDA
  prototype use a segmented CPUStackEngine parity fallback that downloads
  resident calibrated tiles to host and records the route. Current CUDA builds
  use a batch tile-download surface for that fallback when available, with a
  single-frame tile loop retained as a compatibility escape hatch. Minimal-output
  runs, unsupported dispatch, or builds missing the required resident
  tile-download support can still fall back to the faster mean/std approximation
  and record the fallback reason.
- The resident CUDA hardened winsorized path is still a one-iteration,
  512-frame native prototype with separate 256-frame and 512-frame kernel
  variants. Gate609 ensures default 200-light groups use the smaller variant,
  and Gate611 replaces the percentile full-sort prototype with quickselect
  order statistics plus input-frame-order winsorized accumulation, but this
  remains a bounded local-array implementation. The larger-frame
  segmented fallback is correctness-first, not the final high-throughput CUDA
  segmented reduction. Gate607 reduces Python/native round trips in that
  fallback and Gate608 covers 260-frame groups natively, but groups above 512
  still reduce on host through the GLASS CPUStackEngine. Richer robust
  rejection policies, cosmetic correction, and broader data-shape support
  remain future work.
- No full final-master equivalence with PixInsight/WBPP is claimed yet.

These limitations are capability flags, not hidden behavior. Later gates must
replace placeholders with tested implementations and checkpoint their status.
