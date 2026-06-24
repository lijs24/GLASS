# Known Limitations

Current code is intentionally gated:

- XISF parsing is provisional and limited to the XML prefix.
- CPU registration currently estimates only simple translation from ordered
  star lists.
- Local normalization is a global helper placeholder until Gate 10.
- HTML reports include required sections but many stage-specific tables remain
  pending until their gates produce artifacts.
- The resident CUDA path keeps calibrated light frames in VRAM and is fast on
  large same-shape mono datasets. It currently performs calibration, resident
  similarity-triangle registration, Lanczos3 matrix warp, local normalization,
  and mean/sigma/winsorized integration for the default high-VRAM path.
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
  512-frame native prototype. The larger-frame segmented fallback is
  correctness-first, not the final high-throughput CUDA segmented reduction.
  Gate607 reduces Python/native round trips in that fallback and Gate608 covers
  260-frame groups natively, but groups above 512 still reduce on host through
  the GLASS CPUStackEngine. Richer robust rejection policies, cosmetic
  correction, and broader data-shape support remain future work.
- No full final-master equivalence with PixInsight/WBPP is claimed yet.

These limitations are capability flags, not hidden behavior. Later gates must
replace placeholders with tested implementations and checkpoint their status.
