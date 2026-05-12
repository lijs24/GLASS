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
- The same validation has been scaled to a 50-light M38 subset with matched
  planner calibration groups in resident mode. The reference artifact is
  `resident_external_matrix_matchedmasters_vs_tile_astroalign_subset50_compare.json`;
  it reports shape match, median absolute difference around 0.00137 ADU, p99
  around 0.01164 ADU, relative RMS around 9.43e-5, and a 35.1x speedup over
  tile-mode astroalign registration plus tile warp/integration.
