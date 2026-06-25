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

## M38 193-frame PixInsight/WBPP Black-box Compare

The current strongest real-data validation uses the M38 H-alpha input and
black-box reference root in `C:\gpwbpp_runs\final_m38_h_200`. New GLASS
resident validation runs are written under `C:\glass_runs`.

Input scale:

- 200 light frames were planned.
- PixInsight/WBPP FastIntegration integrated 193 of 200 frames.
- GLASS excludes the same 7 WBPP-failed frames for the parity comparison.
- Calibration groups come from the project processing plan; source data is read
  only from user-provided acquisition directories.

PixInsight/WBPP black-box reference:

- Reference master:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`
- External elapsed time: `1092.541 s`.
- WBPP reported time: `18:03.17`.
- Observed settings include FastIntegration, Lanczos3 interpolation,
  Winsorized Sigma Clipping, sigma low/high `3.0`, and weighting disabled.

GLASS resident CUDA reference run:

- Output directory:
  `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3`
- Master:
  `integration\resident_master_H.fits`
- Registration: resident CUDA triangle descriptors, 192 ok, 1 reference,
  7 excluded, 0 failed.
- Warp: resident CUDA Lanczos3 matrix warp with local clamping threshold `0.30`.
- Rejection: two-stage winsorized mean/std approximation.
- Local normalization: disabled for this parity run.
- Elapsed time: `111.94882199994754 s`.
- Speedup vs WBPP black-box elapsed time: `9.75928982978054x`.
- Estimated peak VRAM: about `47.31 GiB`.

Scaled full-frame compare:

- Scale: `8.764434957115609e-06`.
- Offset: `0.0006274500691899127`.
- Shape match: true.
- RMS difference: `0.012474273859075652`.
- Absolute difference p50: `7.260881830006838e-05`.
- Absolute difference p90: `0.00013712106738239527`.
- Absolute difference p99: `0.0021627108892425632`.
- Absolute difference p99.9: `0.20893197426822768`.

Coverage-masked compare:

- Coverage map:
  `integration\resident_coverage_map_H.fits`.
- Minimum coverage threshold: `190`.
- Compared pixels: `59264430`.
- Coverage fraction: `0.9612859117097478`.
- RMS difference: `0.0017183155193652361`.
- Absolute difference p50: `7.188005838543177e-05`.
- Absolute difference p90: `0.00013341044541448355`.
- Absolute difference p99: `0.00045279982034117025`.
- Absolute difference p99.9: `0.00448366389935935`.

Machine-readable speedup summary:

- JSON:
  `runs\benchmarks\m38_wbpp_speedup_summary.json`.
- Markdown:
  `runs\benchmarks\m38_wbpp_speedup_summary.md`.
- Reproduction command:

```powershell
.\.venv\Scripts\python.exe benchmarks\summarize_wbpp_speedup.py `
  --glass-run C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3 `
  --wbpp-result C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json `
  --compare-json C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.json `
  --out runs\benchmarks\m38_wbpp_speedup_summary.json `
  --markdown runs\benchmarks\m38_wbpp_speedup_summary.md `
  --min-speedup 2.0
```

- This summary explicitly records `200` planned frames, `193` active weighted
  frames, and `7` zero-weight frames, matching the WBPP FastIntegration accepted
  frame set used for the parity comparison.

Current Phase 2 latest mainline acceptance:

- Gate: S2-Gate 647.
- Evidence root:
  `C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\candidate_reentry_from_scout`.
- GLASS elapsed time: `11.2256182001438 s`.
- Black-box reference elapsed time: `1092.541 s`.
- Speedup: `97.325686703473x`.
- Frame accounting: `200` planned lights, `193` active weighted frames, and
  `7` zero-weight frames.
- Calibration frame counts: `20` bias, `20` dark, `20` flat.
- Reference scout and health preserve the Gate636 default behavior:
  `auto` attempts CUDA, the official reference remains CPU-selected after the
  guard, and reference-health evidence is persisted for the CUDA-attempt path.
- Reference health now reuses the CPU fallback scout rows when the guarded
  scout has already fallen back to CPU. Latest evidence records
  `cpu_crosscheck.reuse.used=true` with `64` reused scout rows.
- Resident DQ lifecycle: passed. Source-DQ execution, resident frame masks, and
  pixel closure agree on `193` active frames, `7` masked frames, and
  `11898681600` active-frame input samples.
- Frame-accounting DQ lifecycle bridge: passed. The canonical
  `frame_accounting.json` ledger records `200` lifecycle rows, `193` active
  frames, `7` masked frames, and `11898681600` lifecycle source input samples.
- Phase 2 mainline audit: passed. The run satisfies the resident CUDA default
  route, required contract, DQ/mask lifecycle, output-map, timing, acceptance,
  and compare checks.
- Resident mainline framework postcondition: passed in strict mode. The run
  wrote `resident_mainline_framework.json`, included the stage in
  `run_timing.json`, and added it to `run_state.json` completed stages. Gate642
  also validates a synthetic positive source-DQ route where `1` invalid sample
  is applied through resident in-memory mask streaming and observed by
  integration provenance.
- Gate643 makes StackEngine default readiness and pipeline DQ ledger readiness
  resident strict-run postconditions. Latest evidence records
  `stack_engine.default_promotion_ready=true`,
  `stack_engine.pipeline_contract_dq_ledger_ready=true`,
  `stack_engine.phase2_stack_engine_default_gap_count=0`, and
  `stack_engine.surface_count=4`.
- Gate644 makes resident reference health reuse strided sampled light/bias/dark
  /flat inputs between CPU calibrated checks and CUDA calibrated diagnostics.
  Latest evidence records `sample_input_cache_hits=64`,
  `sample_input_cache_misses=64`, `sample_input_cache_stored_bytes=9437184`,
  and a resident reference-health stage time of `0.4174907000269741 s`.
- Gate645 adds resident-specific resume preflight for the same real 200-light
  run. `glass resume --run
  C:\glass_runs\phase2_s2_gate644_reference_health_sample_reuse\runs_20260625_172210\candidate_sample_reuse_strict`
  returned exit code `0` with `resume_action=noop_complete`, wrote
  `resident_resume_preflight.json`, checked `16` expected resident artifacts,
  found `0` missing artifacts, and did not repeat pipeline stages. Incomplete
  resident runs are now blocked from silently falling through to the legacy
  CPU/tile resume path.
- Gate646 centralizes resident stage/artifact expectations in
  `resident_stage_ledger.json` and makes resident resume consume that ledger.
  Gate646 evidence recorded `15` started stages, `15` complete stages, `23`
  expected artifact rows, `0` missing artifact rows, and
  `can_noop_resume=true`.
- Gate647 adds the first resident partial reentry path. A real 200-light partial
  run that had only `resident_reference_scout` completed resumed with
  `resume_action=reenter_from_run_invocation`, invoked the stored `glass run`
  argv, wrote `resident_resume_reentry.json` with exit code `0`, and finished
  with final `resume_action=noop_complete`. Latest ledger evidence again records
  `15` started stages, `15` complete stages, `23` expected artifact rows, `0`
  missing artifact rows, and `can_noop_resume=true`.
- Coverage-masked compare to the reference master with coverage >= `190`:
  shape match true, RMS `0.0056241382952344435`, p99 absolute difference
  `0.002143551869085057`, coverage fraction `0.9749333995120938`, compared
  pixels `60105814`.
- Pipeline contract: passed, including `resident_dq_lifecycle_contract` and
  `frame_accounting_resident_dq_lifecycle_contract`.
- StackEngine contract: passed.
- Warp quality contract: passed.
- Resident regression gate versus Gate646: passed with candidate/baseline
  elapsed ratio `0.8885626915461112` and no failed checks.
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_acceptance_audit.json`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate647_resident_reentry\runs_20260625_190000\gate647_mainline_audit.json`.

Historical Phase 2 hot-path validation:

- Run:
  `C:\glass_runs\phase2_s2_gate537_real_ab\runs_20260623_133539\current_head_default`.
- Shared master cache: `1` hit, `0` misses.
- Internal/shell elapsed time: `4.940610599995125 s` / `5.3052115 s`.
- WBPP black-box elapsed time: `1092.541 s`.
- Speedup: `221.13481277012156x` by internal `run_timing.json`, or
  `205.9373127725445x` by shell timing embedded in the compare report.
- Output parity: master, weight, coverage, low rejection, high rejection, and
  DQ maps are bit-identical to the S2-Gate 536 default rerun.
- Coverage-masked compare to WBPP FastIntegration: shape match true,
  RMS `0.0004279821839256963`, p99 absolute difference
  `0.0001313822576776147`, coverage fraction `0.9892770479074376`, compared
  pixels `56997300`.
- Machine-readable summary:
  `runs\benchmarks\m38_wbpp_speedup_summary_gate537_current.json`.

Residual diagnostics:

- Embedded compare report:
  `compare_vs_wbpp_fastintegration_scaled_diagnostics_embedded.html`.
- Coverage-masked report:
  `compare_vs_wbpp_fastintegration_scaled_coverage190.html`.
- Diagnostic previews show most high residuals along low-coverage edge regions,
  especially the lower image edge. Interior and high-coverage statistics are
  substantially tighter than the full-frame statistics.

Interpretation:

- The current evidence supports a clear speedup on this data set.
- The high-percentile full-frame residuals are dominated by coverage/boundary
  policy differences rather than a full-frame registration failure.
- GLASS does not claim PixInsight-equivalent algorithms. Known remaining
  differences include star matching, boundary/crop policy, exact interpolation
  and clamping behavior, local normalization, rejection details, and output
  scaling.
