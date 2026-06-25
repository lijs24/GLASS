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
  overrides remain available for profiling. S2-Gate 617 tested an opt-in
  pipelined/multi-stream resident matrix-warp dispatch, but the real 200-light
  audit/science route showed tiny output-map drift and no native warp speedup.
  That route is therefore guarded: default audit/science output maps remain on
  deterministic `chunked` warp, and `pipelined` requires no warp coverage
  tracking plus `resident-output-maps minimal`.
  Resident `winsorized_sigma` defaults to an `auto` resolver: supported
  stack-dispatch audit/science groups with at most 512 frames use the hardened
  median/IQR CUDA path that matches the GLASS CPU baseline. For large default
  auto groups above 64 frames, GLASS applies the Gate600/603
  coverage-preserving `rejection_max_fraction=0.015` guard unless the plan or
  CLI explicitly supplies a guard. Groups above the native 512-frame CUDA
  prototype normally use a segmented CPUStackEngine parity fallback that
  downloads resident calibrated tiles to host and records the route. S2-Gate 624
  admits a subset of over-limit groups back to native CUDA when the final finite
  positive-weight sample count is at most 512, even if total input frame count
  is higher. S2-Gate 625 adds an explicit opt-in CUDA radix-select correctness
  prototype for groups above 512 positive-weight samples, but that path is not
  yet the default because it trades the local-array limit for repeated frame-axis
  scans. Current CUDA builds use a batch tile-download surface for the remaining
  default fallback when available, with a single-frame tile loop retained as a
  compatibility escape hatch. S2-Gate 623 filters this fallback to finite
  positive integration weights before download, so zero-weight quality/mask
  rejects are not replayed on host. Minimal-output runs, unsupported dispatch,
  or builds missing the required resident tile-download support can still fall
  back to the faster mean/std approximation and record the fallback reason.
- The resident CUDA hardened winsorized path is still a one-iteration,
  512-frame native prototype with separate 256-frame and 512-frame kernel
  variants. Gate609 ensures default 200-light groups use the smaller variant,
  and Gate611 replaces the percentile full-sort prototype with quickselect
  order statistics plus input-frame-order winsorized accumulation, but this
  remains a bounded local-array implementation. The larger-frame
  segmented fallback is correctness-first, not the final high-throughput CUDA
  segmented reduction. Gate607 reduces Python/native round trips in that
  fallback, Gate608 covers 260-frame groups natively, Gate623 avoids
  downloading zero-weight inactive frames in the host fallback, and Gate624
  keeps over-512 total-frame groups native when active positive-weight count is
  at most 512. Gate625 can process groups above 512 positive-weight samples on
  the GPU when `GLASS_CUDA_RADIX_SELECT_WINSORIZED=1` is set, but this is still
  an opt-in correctness prototype pending large-active-count performance
  validation. NaN-containing over-512 stacks can still show rare one-sample
  rejection-boundary drift when a sample lies exactly on a CPU/GPU threshold;
  this is tracked as parity-hardening work rather than hidden with a tolerance
  guard. Richer robust rejection policies, cosmetic correction, and broader
  data-shape support remain future work.
- No full final-master equivalence with PixInsight/WBPP is claimed yet.

These limitations are capability flags, not hidden behavior. Later gates must
replace placeholders with tested implementations and checkpoint their status.
