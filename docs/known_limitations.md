# Known Limitations

Current code is intentionally gated:

- XISF parsing is provisional and limited to the XML prefix.
- CPU registration currently estimates only simple translation from ordered
  star lists.
- Local normalization is a global helper placeholder until Gate 10.
- HTML reports include required sections but many stage-specific tables remain
  pending until their gates produce artifacts.
- The resident CUDA path keeps calibrated light frames in VRAM and is fast on
  large same-shape mono datasets. It currently performs calibration plus mean
  or sigma-rejection integration. Resident `winsorized_sigma` defaults to an
  `auto` resolver: supported small stack-dispatch audit/science groups with at
  most 64 frames use the hardened median/IQR CUDA path that matches the GLASS
  CPU baseline; minimal-output runs, larger groups, unsupported dispatch, or
  older CUDA builds fall back to the faster mean/std approximation and record
  the fallback reason. Explicit `hardened_cpu_parity` remains available up to
  the native 256-frame prototype limit for diagnostics.
- The resident CUDA path does not yet implement WBPP FastIntegration-equivalent
  internal alignment, Lanczos interpolation, cosmetic correction, or exact
  robust rejection. It can optionally run a preview-scale integer-translation
  alignment pass for diagnostics and high-VRAM experiments.
- No full final-master equivalence with PixInsight/WBPP is claimed yet.

These limitations are capability flags, not hidden behavior. Later gates must
replace placeholders with tested implementations and checkpoint their status.
