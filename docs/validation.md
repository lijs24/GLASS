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

- Gate: S2-Gate 659.
- Evidence root:
  `C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate659_conservative_cosmetic_cuda\runs_20260625_220000\inline_cosmetic_cuda_conservative_policy_strict`.
- GLASS elapsed time: `18.47093429986853 s`.
- Black-box reference elapsed time: `1092.541 s`.
- Speedup: about `59.15x`.
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
- Gate648 adds the next resident reentry boundary inside the calibration/cache
  surface. A real 200-light run writes `resident_reentry_boundary.json`, records
  a timed `resident_reentry_boundary` stage, and exposes `pre_integration`,
  `resident_master_cache`, and `resident_calibration` boundary readiness to
  `glass resume`.
- Gate649 makes that calibration boundary executable. A real 200-light
  incomplete skeleton with ready master-cache and calibration evidence resumed
  with `resume_action=reenter_from_calibration_boundary`, wrote
  `resident_resume_reentry.json` with `reentry_key=boundary_reentry`,
  `boundary_name=resident_calibration`, and `exit_code=0`, then finished with
  final `resume_action=noop_complete`. Latest ledger evidence records `16`
  started stages, `16` complete stages, `24` expected artifact rows, `0`
  missing artifact rows, and `can_noop_resume=true`.
- Gate650 fixes the resident component-stage ledger used by resume and future
  checkpoint boundaries. The Gate649 real run had contradictory ledger evidence:
  `resident_calibration=not_started` while `run_state.json` contained
  `resident_light_calibration` and resident calibration artifacts. The Gate650
  replay canonicalizes `resident_light_calibration` to `resident_calibration`,
  suppresses auxiliary artifact stages such as
  `resident_calibration_contract`, and records `resident_calibration=complete`,
  `18` complete stages, `27` expected artifact rows, `0` missing artifact rows,
  and `can_noop_resume=true`. The new `glass resident-stage-ledger` command
  returned exit code `0` with `--fail-on-missing`, and `glass resume` on the
  replay bundle returned `resume_action=noop_complete`.
- Gate651 promotes that component ledger into the Phase 2 mainline hard gate.
  `glass phase2-mainline-audit` now requires `resident_stage_ledger.json` and
  adds `resident_stage_ledger_component_contract`. The latest real 200-light
  audit records this check as passed with `resident_calibration`,
  `resident_registration`, `resident_local_normalization`, and
  `resident_integration` all `complete`, `18` complete stages, `27` expected
  artifact rows, `0` missing artifacts, and `can_noop_resume=true`.
- Gate652 promotes the resident component timing breakdown into the Phase 2
  mainline hard gate. Resident run/audit now write
  `resident_component_timing.json` and materialize `resident_component_stages`
  into `run_timing.json`. The latest real 200-light audit requires this
  artifact and records `timing_components_available=passed` with required
  components present: `light_read_upload_calibrate=3.5132379999849945 s`,
  `resident_registration_warp=0.26844110037200153 s`, and
  `resident_integration=3.2337921999860555 s`. Optional measured components
  include `resident_local_normalization=0.3582464000210166 s` and
  `output_write=0.23136649990919977 s`.
- Gate653 fixes resident strict-run state synchronization before
  `resident_mainline_framework` invokes the Phase 2 mainline audit. Without the
  fix, a just-finished resident run could have complete in-memory stages but a
  stale `run_state.json`, causing the recomputed stage ledger to mark
  `resident_calibration`, `resident_registration`,
  `resident_local_normalization`, and `resident_integration` as `not_started`.
  The real 200-light validation under
  `C:\glass_runs\phase2_s2_gate653_runtime_state_wavefill\runs_20260626_013000`
  completed strict default and 10us wave-fill candidate runs, both passed
  `phase2-mainline-audit --fail-on-not-green`, and the candidate-vs-default
  regression gate passed with elapsed ratio `0.9981548371313056`. The 10us
  wave-fill candidate was not promoted because the total-time improvement was
  only about `0.18%`.
- Gate654 adds `resident_registration_runtime_contract.json` as a required
  default-run artifact. Gate654 evidence proves `200` registration rows,
  `193/7` active/masked frames, `192` warped non-reference frames,
  `triangle_warp_batch_fallback_frame_count=0`, `24` native warp chunks of
  `8` frames, and `warp_frames_per_s=731.4935008091869`. The explicit
  `phase2-mainline-audit --fail-on-not-green` run passed, and regression
  versus Gate653 default 25us passed with
  `elapsed_ratio=1.027729761074061`.
- Gate655 bridges source-DQ execution into the resident registration runtime
  contract. If `resident_source_dq_execution.json` exists, the registration
  runtime contract now records source-DQ execution status, invalid/applied
  sample closure, and whether catalog-required non-inline source-DQ samples
  were visible before resident registration catalog construction. The focused
  synthetic CUDA strict-positive route applied `1` source-DQ sidecar sample and
  observed it as pre-registration catalog visible. The latest real 200-light
  run has no nonzero source-DQ sidecars, so it records
  `source_dq_exists=true`, `source_dq_positive=false`,
  `source_dq_input_invalid_samples_before_rejection=0`, and
  `source_dq_required_invalid_samples_not_visible_to_registration_catalog=0`.
  Its explicit `phase2-mainline-audit --fail-on-not-green` run passed, and
  regression versus Gate654 default strict passed with
  `elapsed_ratio=1.0138660524354346`.
- Gate656 moves that bridge into `registration_results.json` itself. Resident
  registration rows now include `source_dq_registration_input`, and the
  top-level artifact includes `source_dq_registration_input_summary`.
  `resident_registration_runtime_contract.json` now requires positive
  source-DQ runs to carry this per-frame registration input audit and to match
  source-DQ execution totals. The focused synthetic CUDA strict-positive route
  applied `1` source-DQ sidecar sample, observed it on the `light_002`
  registration row, and passed the new runtime checks. The latest real
  200-light default run has zero source-DQ sidecar samples, records
  `registration_source_dq_input_available=false`,
  `registration_source_dq_input_row_count=200`, and
  `registration_source_dq_input_invalid_samples=0`, passed
  `phase2-mainline-audit --fail-on-not-green`, and passed regression versus
  Gate655 default strict with `elapsed_ratio=1.009718840829939`.
- Gate657 adds a real 200-light positive source-DQ validation path through
  `glass source-dq-probe-manifest`. The command generated a `uint8` sidecar
  mask for frame `F000061` at pixel `[3211, 4800]`, rebound the normal
  processing plan through `glass plan --source-dq-manifest`, and ran resident
  CUDA in strict `source_dq_positive` scope. Latest evidence records
  `source_dq_invalid=1`, `source_dq_applied=1`,
  `registration_source_dq_input_invalid_samples=1`, the `F000061`
  registration row carrying `source_dq_registration_input.invalid_samples=1`,
  integration provenance `input_invalid_samples_before_rejection=1`, and all
  source-DQ registration runtime checks passed. This run intentionally differs
  from the zero-DQ default route; the Gate657-vs-Gate656 compare records shape
  match true, coverage-masked p50/p90/p99 absolute differences
  `0.0` / `1.0081672668457031` / `5.743577690124511`, and RMS
  `2.1730066333730473`.
- Gate658 adds a real 200-light resident inline cosmetic CUDA positive
  source-DQ scope. The strict run used
  `--resident-inline-source-dq cosmetic_cuda` with
  `--resident-inline-source-dq-max-invalid-fraction 0.02`, passed
  `resident_mainline_framework.json` with
  `framework_scope=inline_cosmetic_cuda_positive`, and passed
  `phase2-mainline-audit --fail-on-not-green` with `200` lights, `193` active
  frames, and `7` masked frames. Evidence records active source-DQ invalid and
  applied samples `9532598`, all-frame invalid and applied samples `10258384`,
  source counts `resident_post_registration_pre_warp_cosmetic_cuda=192` and
  `resident_post_registration_pre_warp_cosmetic_cuda_flush=8`, and
  `registration_matches_all_frame_source_dq=true`. This is an opt-in policy
  impact run: compared with Gate656 default at coverage >= `190`, shape match
  is true, coverage fraction is `0.9749391414927853`, p50/p90/p99 absolute
  differences are `0.45581817626953125` / `2.0315895080566406` /
  `10.900529212951653`, and RMS is `4.465267226951517`. The drift is expected
  because the detector invalidated millions of hot/cold/cosmetic samples; the
  default science route remains unchanged until a star-aware source-DQ policy is
  validated.
- Gate659 adds `--resident-inline-source-dq-policy` and validates the
  conservative profile on the real 200-light M38 route. The conservative
  profile resolves to `max_invalid_fraction=0.0003` from policy defaults and is
  recorded in `run_timing.json`, `resident_source_dq_strategy.json`, and
  `resident_artifacts.json`. The green strict run applied source-DQ to `10`
  frames, skipped `190` high-fraction frames, recorded
  `input_invalid_samples_before_rejection=147180`, passed
  `framework_scope=inline_cosmetic_cuda_positive`, and passed
  `phase2-mainline-audit --fail-on-not-green`. Compared with Gate656 default at
  coverage >= `190`, shape match is true, coverage fraction is
  `0.9749355243693554`, p50/p90/p99 absolute differences are
  `0.0345001220703125` / `0.17724990844726562` /
  `1.2427406311035156`, and RMS is `0.5331775153760971`. This keeps positive
  real-data source-DQ execution while reducing Gate658 policy drift
  substantially; it is still opt-in pending a star-aware detector.
- Coverage-masked compare to the reference master with coverage >= `190`:
  shape match true, RMS `0.005624135079195954`, p99 absolute difference
  `0.0021429822302888963`, coverage fraction `0.9749333995120938`, compared
  pixels `60105814`.
- Pipeline contract: passed, including `resident_dq_lifecycle_contract` and
  `frame_accounting_resident_dq_lifecycle_contract`.
- StackEngine contract: passed.
- Warp quality contract: passed.
- Resident regression gate versus Gate648: passed with candidate/baseline
  elapsed ratio `0.9899309067228078` and no failed checks.
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate649_cal_boundary_reentry\runs_20260625_210000\gate649_acceptance_audit.json`.
- Mainline audit:
  `C:\glass_runs\phase2_s2_gate652_component_timing_surface\runs_20260626_000000\gate652_phase2_mainline_audit.json`.

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
