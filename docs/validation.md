# Validation

Validation is gate-driven:

- Synthetic FITS data verifies scan, plan, master frames, calibration, star
  detection, registration, and integration.
- CUDA kernels are compared against CPU references with explicit tolerances.
- PixInsight/WBPP comparison is black-box only and uses user-generated outputs.
- Real-data matrix-warp validation now includes an M38 12-light subset where
  tile-mode astroalign generates similarity matrices, tile-mode CPU/tile warp
  integrates those matrices, and resident CUDA `external_matrix` applies the
  same matrices in VRAM before integration. The current reference artifact is
  `resident_external_matrix_vs_tile_astroalign_subset12_compare.json`, with
  shape match, median absolute difference around 0.0018 ADU, p99 around 0.0146
  ADU, and relative RMS around 1.67e-4.
