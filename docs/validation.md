# Validation

Validation is gate-driven:

- Synthetic FITS data verifies scan, plan, master frames, calibration, star
  detection, registration, and integration.
- CUDA kernels are compared against CPU references with explicit tolerances.
- PixInsight/WBPP comparison is black-box only and uses user-generated outputs.

