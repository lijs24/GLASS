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
- The portable CPU/tile integration path now streams StackEngine output tiles
  directly to FITS maps and no longer materializes the full integration result
  in the outer integration sink. Direct `CPUStackEngine.stack(...)` API calls
  and some calibration/master-frame surfaces can still return full result
  arrays by design; future gates should extend the same sink pattern to any
  remaining large StackEngine surfaces before claiming universal out-of-core
  StackEngine execution.
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
  validation. Gate626 resolves the mixed-valid/NaN radix-select parity edge by
  making the CPU winsorized baseline deterministic instead of adding a
  rejection-threshold tolerance. Gate627 adds a reusable
  `resident-winsorized-overlimit-benchmark` command and benchmark script so
  over-512 radix-select parity/performance can be measured against tiled
  CPUStackEngine, but this is still an evidence surface rather than a
  default-path promotion. Gate629 adds an opt-in
  `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN=1` path for the default 0/1-weight case; it
  preserves output determinism on the real 200-light A/B and improves the
  measured run, but the integration-only gain is modest in a single run. Gate630
  ran repeat evidence and rejected treating mask-scan as a large kernel
  optimization: mask-scan won total elapsed time in three paired runs, but
  hardened integration and kernel-sync timings were consistently slower, so the
  total gain was attributed to surrounding runtime variance. Gate668 later
  promotes mask-scan as a narrow default admission for unit-positive 0/1 weights
  because a current-HEAD real 200-light A/B and a post-change default run both
  passed regression with zero output drift, no total-time regression, and a
  trivial one-byte-per-frame mask. `GLASS_CUDA_UNIT_WEIGHT_MASK_SCAN=0` remains
  the diagnostic escape hatch, and invalid values such as `auto` are still
  ignored. Gate633
  removes the unconditional fallback std pass from the bounded CUDA reducer and
  computes it lazily only for IQR-degenerate pixels; real 200-light kernel-sync
  time improved slightly in both paired runs, but total runtime did not move
  materially because the gain is smaller than surrounding I/O and registration
  variance. Richer robust rejection policies, cosmetic correction, and broader
  data-shape support remain future work.
- The default native-completion calibration schedule still uses 4 lanes. Gate631
  tested 8/12/16-lane real 200-light variants and rejected default promotion:
  8-lane preserved output but did not deliver a stable native H2D/calibration
  win, while 12/16 lanes increased native calibration time in the first matrix.
  `resident_light_pipeline_profile.native_completion` now records lane-fill,
  queue-buffer, worker, wave-fill, and slot-reuse metrics so the next
  substantive improvement can target wave-fill/overlap instead of blindly
  increasing lane count. Gate632 keeps the 4-lane default but changes the
  default wave-fill mode to `single_wait`, reducing repeated completion-queue
  condition-variable waits on the real 200-light benchmark while preserving
  output parity. The previous `multi_wait` behavior remains available through
  `--resident-native-completion-wave-fill-mode multi_wait` for hardware or disk
  configurations where repeated fill waits are beneficial.
- No full final-master equivalence with PixInsight/WBPP is claimed yet.

These limitations are capability flags, not hidden behavior. Later gates must
replace placeholders with tested implementations and checkpoint their status.
