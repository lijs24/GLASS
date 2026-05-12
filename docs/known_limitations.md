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
  or mean/std sigma-rejection integration. Its `winsorized_sigma` mode is an
  approximation based on winsorized mean/std thresholds followed by final
  rejection of original samples, not a verified PixInsight-equivalent robust
  Winsorized Sigma Clipping implementation.
- The resident CUDA path does not yet implement WBPP FastIntegration-equivalent
  internal alignment, Lanczos interpolation, cosmetic correction, or exact
  robust rejection. It can optionally run a preview-scale integer-translation
  alignment pass for diagnostics and high-VRAM experiments.
- No full final-master equivalence with PixInsight/WBPP is claimed yet.

These limitations are capability flags, not hidden behavior. Later gates must
replace placeholders with tested implementations and checkpoint their status.
