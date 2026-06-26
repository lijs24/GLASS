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

- Gate: S2-Gate 660.
- Evidence root:
  `C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412`.
- GLASS run:
  `C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict`.
- GLASS elapsed time: `18.553858600207604 s`.
- Black-box reference elapsed time: `1092.541 s`.
- Speedup: about `58.88x`.
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
- Gate660 adds `--resident-inline-source-dq-admission active_registered` and
  makes deferred inline cosmetic CUDA source-DQ respect the registration/current
  positive-weight frame set before native batch application. The real 200-light
  strict run used the Gate659 conservative profile plus active admission,
  passed `framework_scope=inline_cosmetic_cuda_positive`, and passed
  `phase2-mainline-audit --fail-on-not-green`. Evidence records `200`
  deferred candidates, `193` active targets, `7` skipped-admission masked
  frames, status counts `applied=10`, `skipped_high_invalid_fraction=183`, and
  `skipped_admission_policy=7`. Active/all-frame invalid and applied samples
  are `147179`, GLASS `total_elapsed_s=18.553858600207604`, speedup is about
  `58.88x` versus the `1092.541 s` black-box timing, and the Gate660-vs-Gate659
  conservative compare is bit-identical over the coverage-masked master
  (`RMS=0.0`, max absolute difference `0.0`).
- Gate661 adds the first star-protected inline cosmetic source-DQ CPU baseline
  and opt-in `--resident-inline-source-dq cosmetic_star`. Focused synthetic
  validation proves a compact PSF-like star core is protected while an isolated
  hot pixel remains masked, and strategy/CLI tests prove the audit surface is
  recorded. This is a science-contract baseline for the next resident CUDA
  source-DQ gate; the latest real 200-light mainline acceptance remains
  Gate660 until the GPU implementation is validated.
- Gate662 adds opt-in `--resident-inline-source-dq cosmetic_star_cuda`.
  Focused resident CUDA validation proves native star-protected isolated
  count/apply kernels, resident histogram threshold plus star-catalog artifact
  fields, CLI/strategy plumbing, and a small resident CUDA run using the new
  detector. The default route remains unchanged and real 200-light mainline
  acceptance is not re-promoted by this opt-in source-DQ gate.
- Gate663 runs the real M38 200-light A/B for `cosmetic_star_cuda` against the
  Gate660 conservative active-registered baseline. The candidate completes in
  `21.259431299986318 s`, remains `51.39088551257263x` faster than the
  `1092.541 s` black-box reference, and protects `194` cosmetic samples inside
  resident CUDA star footprints. Output differences are explained by that
  opt-in semantic change: master RMS versus Gate660 is `0.1315372868894881`,
  master p99 absolute difference is `0.14057159423828125`, and coverage/weight
  changes affect about `0.147%` of pixels. It is not promoted because it is
  `14.6%` slower than Gate660 and fails deterministic equality by design.
- Gate664 batches `cosmetic_star_cuda` resident count/apply with native
  `ResidentCalibratedStack.*_star_protected_isolated_cosmetic_threshold_mask_frames`
  methods. Focused CUDA validation includes batch-vs-single fuzz parity. The
  real 200-light run at
  `C:\glass_runs\phase2_s2_gate664_star_cuda_batch_real\runs_20260625_231500\star_cuda_batch_conservative_active_warn`
  completed in `20.791611200082116 s`, or `52.54720230607645x` versus the
  `1092.541 s` black-box timing. The source-DQ deferred apply substage improved
  from Gate663 `0.7322519001318142 s` to `0.6506714000133798 s`; total runtime
  improved by about `2.2%`. A repeat strict run completed in
  `20.913607999915257 s`, but repeat determinism still failed due to five
  source-DQ invalid-sample differences (`146987` versus `146992`) propagating
  into output maps. All required contracts and runtime checks passed; this
  opt-in source-DQ route remains unpromoted until threshold/catalog
  repeat-determinism or a tolerance-based diagnostic acceptance rule is added.
- Gate665 wires `--resident-star-catalog-deterministic` into the
  `cosmetic_star_cuda` source-DQ catalog path and records the deterministic
  source in resident artifacts and `resident_source_dq_strategy.json`. Two real
  200-light deterministic repeats at
  `C:\glass_runs\phase2_s2_gate665_star_cuda_deterministic_source_dq\runs_20260626_000500`
  recorded identical source-DQ totals (`147013` invalid samples,
  `98216` hot, `48797` cold), both passed strict
  `inline_cosmetic_cuda_positive`, and passed `resident-regression-gate` with
  `resident_determinism_passed=true`, zero output differences, zero numerical
  drift, and elapsed ratio `0.9935515642728923`. Run times were
  `19.866321900160983 s` and `19.738215200253762 s`, about `55x` faster than
  the `1092.541 s` black-box timing.
- Gate666 makes that deterministic catalog the default semantics of the
  opt-in `cosmetic_star_cuda` source-DQ route without promoting the global
  registration catalog flag. The real 200-light candidate omitted
  `--resident-star-catalog-deterministic` and still recorded
  `resident_source_dq_star_catalog_policy.source=cosmetic_star_cuda_default`,
  `global_resident_star_catalog_deterministic=false`,
  `resident_inline_source_dq_star_catalog_deterministic=true`, and
  `resident_cuda_star_grid_top_nms_candidates_deterministic`. The run at
  `C:\glass_runs\phase2_s2_gate666_star_cuda_default_deterministic\runs_20260626_010500\star_cuda_default_det`
  completed in `19.5065466001397 s` (`56.00894009563822x` versus
  `1092.541 s`), matched Gate665 source-DQ totals (`147013` invalid/applied,
  status counts `applied=10`, `skipped_high_invalid_fraction=183`,
  `skipped_admission_policy=7`), and passed regression versus Gate665 run A
  with elapsed ratio `0.9818901907545167`, zero artifact/frame/registration
  differences, zero output differences, and zero numerical drift.
- Gate667 makes `active_registered` the default admission semantics for opt-in
  CUDA inline source-DQ routes while preserving explicit
  `--resident-inline-source-dq-admission all` as a compatibility escape hatch.
  The real 200-light candidate omitted both
  `--resident-star-catalog-deterministic` and
  `--resident-inline-source-dq-admission`; it still recorded
  `resident_inline_source_dq_admission_effective.source=cuda_inline_default`,
  `requested=all`, `effective=active_registered`, `explicit=false`, and the
  Gate666 deterministic catalog policy. The run at
  `C:\glass_runs\phase2_s2_gate667_cuda_source_dq_active_default\runs_20260626_020000\star_cuda_default_admission`
  completed in `19.542332700220868 s` (`55.906376007386875x` versus
  `1092.541 s`), matched Gate666 source-DQ totals (`147013` invalid/applied,
  status counts `applied=10`, `skipped_high_invalid_fraction=183`,
  `skipped_admission_policy=7`), and passed regression versus Gate666 with
  elapsed ratio `1.001834568712481`, zero artifact/frame/registration
  differences, zero output differences, and zero numerical drift.
- Gate668 promotes the unit-positive 0/1 weight mask-scan reducer branch into
  the default resident CUDA hardened winsorized path. The current-HEAD
  environment-enabled A/B at
  `C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500`
  passed regression versus the old default with elapsed ratio
  `0.9952617617554094`, and the post-change no-env default run at
  `C:\glass_runs\phase2_s2_gate668_mask_scan_promotion_probe\runs_20260626_021500\default_promoted`
  passed regression versus the old default with elapsed ratio
  `0.9889873813782383`, zero failed checks, and zero output drift. The promoted
  run records
  `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`,
  `unit_positive_weight_mask_reason=default_unit_positive_weight_mask_scan`,
  `unit_positive_weight_mask_bytes=200`, and
  `unit_positive_weight_frame_count=193`. Runtime moved from
  `11.220837099594064 s` old default to `11.097266299999319 s` promoted
  default on this repeated 200-light comparison.
- Gate669 changes the CPU/tile StackEngine integration sink so output maps are
  written tile-by-tile instead of serializing a full `StackEngineResult` first.
  Focused validation passed integration default/variance-map tests and the
  StackEngine contract suite. The synthetic audit fixture generated a small
  FITS dataset, ran the full CPU audit path, produced integration maps and
  report artifacts, and verified
  `execution_path=stack_engine_streaming_tile_sink`,
  `full_output_arrays_materialized=false`, zero failed streaming tile
  contracts, and a passing `stack_engine_streaming_result_contract`. A real
  200-light resident guard at
  `C:\glass_runs\phase2_s2_gate669_stackengine_streaming_sink\runs_20260626_030000\resident_default_guard`
  passed regression against Gate668 promoted default with elapsed ratio
  `1.046346188895259`, no failed checks, and zero artifact/frame/registration
  or output differences. Full pytest passed with `1410 passed in 62.32 s`.
- Gate670 applies the same streaming-sink model to CPU/tile master calibration.
  Focused validation passed direct master legacy-parity and min/max rejection
  tests, a synthetic calibration run through `glass run --until-stage
  calibration`, and StackEngine contract acceptance. Calibration artifacts now
  prove `execution_path=stack_engine_master_streaming_tile_sink`,
  `full_output_arrays_materialized=false`, zero failed streaming tile
  contracts, and a passing
  `stack_engine_master_streaming_result_contract` for bias/dark/flat masters.
  The synthetic calibration artifact at
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\synthetic_cpu_calibration`
  recorded 3 streaming masters, each with 16 tile contracts and zero failed
  tile contracts. The real 200-light resident guard at
  `C:\glass_runs\phase2_s2_gate670_master_streaming_sink\runs_20260626_040000\resident_default_guard`
  passed regression against Gate669 with elapsed ratio `1.0081524547892338`,
  no failed checks, and zero artifact/frame/registration or output
  differences. Full pytest passed with `1410 passed in 62.66 s`.
- Gate671 writes explicit master DQ FITS artifacts for CPU/tile master bias,
  dark, and flat frames. The synthetic calibration run at
  `C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\synthetic_cpu_calibration`
  wrote three `dq_master_*.fits` files alongside four calibrated-light DQ
  files. Each master recorded `dq_summary={"valid": 1024}`, matching
  `stack_engine_dq_provenance.output_dq_summary`, and passed
  `stack_engine_master_streaming_result_contract`. The calibration-only
  StackEngine contract passed with `strict_native_stack_engine_ready=true`.
  The real 200-light resident guard at
  `C:\glass_runs\phase2_s2_gate671_master_dq_artifacts\runs_20260626_050000\resident_default_guard`
  passed regression against Gate670 with elapsed ratio `0.9480347464554004`,
  no failed checks, and zero artifact/frame/registration or output
  differences. Full pytest passed with `1410 passed in 63.10 s`.
- Gate672 extends master DQ artifacts to the resident CUDA calibration surface.
  The real 200-light default resident run at
  `C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\default_with_resident_master_dq`
  wrote three resident master DQ sidecars under `calib_cache\dq`, one each for
  bias, dark, and flat. Each sidecar recorded `dq_summary={"valid": 61651200}`
  and a passing `resident_master_dq_contract`. The resident regression against
  Gate671 passed with elapsed ratio `1.0533260571398728`, no failed checks, and
  zero artifact/frame/registration/output/numerical drift. The Phase 2
  mainline audit passed with `200` input lights and `193` active frames, and
  the StackEngine resident contract passed with
  `default_promotion_ready=true`. A high-VRAM deep-queue candidate at
  `C:\glass_runs\phase2_s2_gate672_high_vram_runtime\runs_20260626_060000\candidate_deep_queue`
  was rejected: it failed `runtime_within_threshold` at elapsed ratio
  `1.17939080551414`, mainly because light read/upload/calibrate increased to
  `4.3863005000166595 s`. Full pytest passed with `1411 passed in 64.01 s`.
- Gate673 adds a resident memory lifecycle artifact to the default resident
  CUDA path. The real 200-light run at
  `C:\glass_runs\phase2_s2_gate673_memory_lifecycle\runs_20260626_070000\default_with_lifecycle`
  wrote `resident_memory_lifecycle.json` and recorded one passing group with
  estimated calibrated-stack residency `45.93372344970703 GiB`, estimated peak
  `49.608429938554764 GiB`, `raw_all_frames_resident=false`,
  `calibrated_stack_resident=true`, and
  `registered_cache_materialized_on_disk=false`. The regression against Gate672
  passed with elapsed ratio `0.9911025449355981`, no failed checks, `193/7`
  active/masked frames, and zero artifact/frame/registration/output/numerical
  drift. The Phase 2 mainline audit and StackEngine resident contract both
  passed, and full pytest passed with `1414 passed in 64.50 s`.
- Gate674 promotes that memory lifecycle from evidence to a mainline runtime
  guard. `phase2-mainline-audit` now requires
  `resident_memory_lifecycle.json`, and `resident-regression-gate` requires the
  same contract by default. The real 200-light final run at
  `C:\glass_runs\phase2_s2_gate674_lifecycle_mainline\runs_20260626_080000\default_lifecycle_guard_final`
  passed with `200` input lights, `193/7` active/masked frames, total elapsed
  `12.066693499917164 s`, calibrated-stack residency
  `45.93372344970703 GiB`, estimated peak `49.608429938554764 GiB`, and the
  expected raw-stream/calibrated-resident/no-registered-cache lifecycle
  booleans. The final mainline audit passed with failed checks `[]`, and the
  regression against Gate673 passed with elapsed ratio `1.0415137090462976`.
  An active-index reducer A/B candidate passed determinism/regression but was
  slower on the paired default run: total ratio `1.0181637343039516` and
  integration ratio `1.0355348444807078`, so it was not promoted. Full pytest
  passed with `1418 passed in 64.75 s`.
- Gate675 removes the redundant device `float32` weight-map materialization
  from the default unit-positive resident hardened `uint16` count-map path and
  synthesizes the returned host weight map from the downloaded coverage map.
  The real 200-light run at
  `C:\glass_runs\phase2_s2_gate675_unit_weight_map_from_coverage\runs_20260626_090000\default_unit_weight_map_from_coverage`
  passed Phase 2 mainline audit with `200` input lights and `193` active
  frames. The native profile recorded `returned_arrays=5`,
  `downloaded_arrays=4`, `downloaded_bytes=616512000`,
  `host_synthesized_bytes=246604800`, and
  `weight_map_download_source=coverage_map_uint16_host_expand`. Regression
  against Gate674 passed with no artifact, frame-accounting, registration,
  output, or numerical drift. Total elapsed ratio was
  `1.0077329966094555`; the resident integration component improved from
  `3.323810000088997 s` to `3.2761442000046372 s`, and native kernel sync
  improved from `3.192917 s` to `3.1436261 s`.
- Gate676 changes sub-millisecond native completion wave-fill waits from
  `condition_variable.wait_for` to `micro_poll_yield` for waits up to `500 us`.
  The real 200-light default run at
  `C:\glass_runs\phase2_s2_gate676_micro_poll_wave_fill\runs_20260626_110000\default_micro_poll`
  passed Phase 2 mainline audit with `200` input lights and `193` active
  frames. The native completion profile recorded
  `native_completion_calibration_consumer_wave_fill_wait_strategy=micro_poll_yield`;
  wave-fill wait time dropped from Gate675 `0.19453819999999994 s` to
  `0.005880000000000006 s`; `light_read_upload_calibrate` dropped from
  `3.4165546000003815 s` to `3.0986569999950007 s`; and regression against
  Gate675 passed with elapsed ratio `0.9725103078340935` and failed checks
  `[]`.
- Gate677 removes the unused device float32 weight-buffer allocation/upload from
  default unit-positive resident hardened integration routes. The real
  200-light default run at
  `C:\glass_runs\phase2_s2_gate677_skip_unused_weights\runs_20260626_120000\default_skip_weights`
  passed Phase 2 mainline audit with `200` input lights and `193` active
  frames. The native profile recorded
  `sample_reuse_strategy=frame_mask_global_reread_unit_positive_weights`,
  `native_weight_buffer_required=false`,
  `native_weight_buffer_device_materialized=false`,
  `native_weight_buffer_upload_skipped=true`,
  `native_weight_buffer_uploaded_bytes=0`, and
  `unit_positive_weight_mask_bytes=200`. Regression against Gate676 passed with
  no output/artifact/frame-accounting/registration drift and elapsed ratio
  `1.0394643023337526`; the slowdown was in surrounding
  `light_read_upload_calibrate` variance, while resident integration stayed
  essentially flat at `3.3727147999452427 s`.
- Gate678 adds an opt-in selected-buffer reuse probe for the same resident
  hardened reducer family and rejects it with real evidence. The current-HEAD
  default run at
  `C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\default_head`
  passed regression against Gate677 with failed checks `[]` and elapsed ratio
  `0.9913605001863092`. The candidate run at
  `C:\glass_runs\phase2_s2_gate678_selected_reuse\runs_20260626_130000\selected_reuse`
  passed Phase 2 mainline audit with `200` lights and `193` active frames, but
  default-vs-candidate regression failed `resident_determinism_passed` and was
  slower: selected/default resident integration `3.4472310000564903 s` /
  `3.3610659999540076 s`, native kernel sync `3.3259804 s` / `3.2432453 s`,
  and total elapsed ratio `1.0094310426288307`. The coverage-masked master
  compare showed tiny numerical drift (`rms_diff=0.000560800848695079`,
  `relative_rms_diff=1.7645079997153338e-06`, p99 absolute difference
  `3.814697265625e-05`), so the branch remains opt-in only and is explicitly
  not promoted.
- Gate679 adds a native profile contract for the resident hardened reducer
  launch shape and rejects simple 128/512 block-size tuning on the real
  200-light benchmark. The fresh 256-thread control at
  `C:\glass_runs\phase2_s2_gate679_wave_fill_mode\runs_20260626_140000\single_wait_fresh`
  recorded resident integration `3.3787344000302255 s` and native kernel sync
  `3.2560789 s`. The 128-thread candidate at
  `C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads128_candidate`
  recorded `3.5057293999707326 s` and `3.3859033 s`; the 512-thread candidate at
  `C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads512_candidate`
  recorded `3.4998344000196084 s` and `3.3783218 s`. Both candidates were
  bitwise identical to the 256-thread control for all six integration FITS
  outputs, but slower. The final profiled 256-thread default at
  `C:\glass_runs\phase2_s2_gate679_hardened_threads\runs_20260626_143000\threads256_profile_default`
  recorded `hardened_kernel_threads_per_block=256`, passed Phase 2 mainline
  audit with `200` input lights and `193` active frames, and passed regression
  against the fresh 256-thread control with failed checks `[]` and elapsed
  ratio `1.0220616179844362`.
- Gate680 adds explicit native-completion raw-ring capacity control for the
  resident read/H2D/calibration pipeline. The current default run at
  `C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue32_default`
  recorded `native_completion_queue_buffer_policy_source=runtime_auto_base`,
  planned/effective raw buffers `32 / 32`, pinned raw bytes
  `3945676800 / 3945676800`, total elapsed `12.245715199969709 s`, and
  `light_read_upload_calibrate=3.391568800085224 s`. The explicit 64-buffer
  candidate at
  `C:\glass_runs\phase2_s2_gate680_completion_ring\runs_20260626_160000\queue64_candidate`
  recorded `policy_source=explicit_cli`, requested/planned/effective raw buffers
  `64 / 64 / 64`, pinned raw bytes `7891353600 / 7891353600`, total elapsed
  `12.695490699843504 s`, and `light_read_upload_calibrate=4.130420900066383 s`.
  The 64-buffer run passed Phase 2 mainline audit and resident regression
  against the 32-buffer control with failed checks `[]` and elapsed ratio
  `1.0367292144663716`, but runtime compare selected `queue32`, so 64 buffers
  are not promoted as default.
- Gate681 wires `--ram-budget-gb` into resident native-completion raw-ring
  planning. The real 200-light RAM-budget candidate at
  `C:\glass_runs\phase2_s2_gate681_ram_budget_ring\runs_20260626_170000\ram24_auto`
  used `--ram-budget-gb 24`, recorded
  `native_completion_queue_buffer_policy_source=ram_budget_auto`,
  `native_completion_queue_buffer_budget_reason=ram_budget_expanded`,
  raw frame bytes `123302400`, planned/effective raw buffers `52 / 52`, and
  estimated/effective pinned raw bytes `6411724800 / 6411724800`. Phase 2
  mainline audit passed with failed checks `[]`, input lights `200`, and
  active/masked frames `193 / 7`. Resident regression against the Gate680
  32-buffer default passed with failed checks `[]` and elapsed ratio
  `1.0156699953413586`. Direct FITS comparison against the 32-buffer default
  showed bitwise-identical master, weight, coverage, low-rejection,
  high-rejection, and DQ maps. Runtime compare still selected
  `queue32_default`, so RAM-budget expansion is an auditable option rather than
  a default promotion.
- Gate682 promotes the default native-completion wave-fill wait from `25us` to
  `250us` for `throughput-v4-native-completion`. The real 200-light promoted
  default run at
  `C:\glass_runs\phase2_s2_gate682_wave_fill_default\runs_20260626_183000\default_250us`
  was launched without an explicit wave-fill flag and recorded
  `native_completion_calibration_consumer_wave_fill_policy=single_wait_250us`.
  Compared with the Gate680 `single_wait_25us` baseline, total elapsed improved
  from `12.245715199969709 s` to `11.735124099999666 s`, elapsed ratio
  `0.9583045096482967`; `light_read_upload_calibrate` improved from
  `3.391568800085224 s` to `3.2267182000214234 s`; H2D/calibrate-store
  improved from `2.750575099955313 s` to `2.5775656999321654 s`; multi-frame
  native-completion waves increased from `17` to `40`. Phase 2 mainline audit
  and resident regression passed with failed checks `[]`, input lights `200`,
  and active/masked frames `193 / 7`. Direct FITS comparison showed
  bitwise-identical master, weight, coverage, low-rejection, high-rejection,
  and DQ maps.
- Gate683 routes Windows native raw-FITS payload reads through
  `CreateFileW + FILE_FLAG_SEQUENTIAL_SCAN` and records the selected read
  backend in resident artifacts and the light-pipeline profile. The real
  200-light run at
  `C:\glass_runs\phase2_s2_gate683_win32_sequential_read\runs_20260626_193000\win32_seq_default`
  recorded `native_path_calibration_read_backend=win32_sequential_scan`.
  Phase 2 mainline and regression gates passed with failed checks `[]`, input
  lights `200`, and active/masked frames `193 / 7`. Runtime compare kept
  Gate682 as the best observed run: Gate683 elapsed `11.860965099884197 s`
  versus Gate682 `11.735124099999666 s`, elapsed ratio
  `1.0107234485815566`. Direct SHA256 comparison showed bitwise-identical
  master, weight, coverage, low-rejection, high-rejection, and DQ maps.
- Gate684 formalizes the native read backend as a resident execution policy.
  `--resident-native-read-backend` accepts `auto`, `std_ifstream`, or
  `win32_sequential_scan`; the default throughput-v4 preset records `auto`,
  which resolves to `std_ifstream`. The real 200-light warm default run at
  `C:\glass_runs\phase2_s2_gate684_native_read_backend_policy\runs_20260626_211500\default_auto_std_warm`
  recorded `native_path_calibration_read_backend_policy=auto` and
  `native_path_calibration_read_backend=std_ifstream`. Phase 2 mainline and
  regression gates passed with failed checks `[]`, input lights `200`, and
  active/masked frames `193 / 7`. Runtime compare selected Gate684 as best
  observed: `11.66652269999031 s` versus Gate682 `11.735124099999666 s`,
  elapsed ratio `0.9941541819732985`. Direct SHA256 comparison showed
  bitwise-identical master, weight, coverage, low-rejection, high-rejection,
  and DQ maps.
- Gate685 fixes resident native-completion read-overlap telemetry. The real
  200-light run at
  `C:\glass_runs\phase2_s2_gate685_native_overlap_semantics\runs_20260626_223000\default_overlap_semantics`
  recorded `read_supply_model=native_completion_calibration`,
  `read_supply_worker_cumulative_s=30.826195000000002`,
  `read_supply_file_read_cumulative_s=30.780779700000004`,
  `read_supply_overlap_saved_s=27.324453300009186`, and
  `read_supply_worker_to_wall_ratio=8.80310360986387`. Phase 2 mainline and
  regression gates passed with failed checks `[]`, input lights `200`, and
  active/masked frames `193 / 7`. Runtime compare kept Gate684 as best observed:
  Gate685 elapsed `12.43947100022342 s`, elapsed ratio
  `1.0662535290171555` versus Gate684. Direct SHA256 and array comparisons
  showed byte-identical and array-identical master, weight, coverage,
  low-rejection, high-rejection, and DQ maps.
- Gate686 adds exact early-disallow logic to the resident hardened winsorized
  CUDA rejection-counting pass. The real 200-light run at
  `C:\glass_runs\phase2_s2_gate686_rejection_guard_early_disallow\runs_20260626_231500\default_early_disallow`
  recorded `rejection_guard_early_disallow_enabled=true`, native kernel sync
  `3.1232872 s`, resident integration `3.2561724999686703 s`, and total
  elapsed `12.344183000386693 s`. Runtime compare selected Gate686 over
  Gate685 (`12.43947100022342 s`), elapsed ratio `0.9923398671989334`.
  Phase 2 mainline and regression gates passed with failed checks `[]`, input
  lights `200`, and active/masked frames `193 / 7`. Direct SHA256 and array
  comparisons showed byte-identical and array-identical master, weight,
  coverage, low-rejection, high-rejection, and DQ maps.
- Gate687 adds a no-rejection final accumulation branch to the resident
  hardened winsorized CUDA reducer. The real 200-light run at
  `C:\glass_runs\phase2_s2_gate687_no_reject_accumulation_branch\runs_20260627_000000\default_no_reject_branch`
  recorded
  `rejection_guard_no_reject_accumulation_branch_enabled=true`, native kernel
  sync `3.1146121 s`, resident integration `3.234628599951975 s`, and total
  elapsed `12.207209800020792 s`. Runtime compare selected Gate687 over
  Gate686 (`12.344183000386693 s`), elapsed ratio `0.9889038261696533`.
  Phase 2 mainline and regression gates passed with failed checks `[]`, input
  lights `200`, and active/masked frames `193 / 7`. Direct SHA256 and array
  comparisons showed byte-identical and array-identical master, weight,
  coverage, low-rejection, high-rejection, and DQ maps.
- Gate688 hard-requires `sample_accounting_closure` for resident DQ/count-map
  outputs. The Gate687 200-light resident run was replayed through
  `resident-result-contract` and `pipeline-contract` with pixel verification;
  both passed and wrote:
  `C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_resident_result_contract.json`
  and
  `C:\glass_runs\phase2_s2_gate688_sample_closure_contract\gate688_pipeline_contract.json`.
  Full pytest passed with `1429 passed in 66.28 s`.
- Gate689 adds resident matrix-warp identity bypass. The real 200-light run at
  `C:\glass_runs\phase2_s2_gate689_identity_warp_bypass\runs_20260627_013000\identity_bypass_default`
  passed Phase 2 mainline audit, resident regression versus Gate687, resident
  result contract with pixel verification, and pipeline contract with pixel
  verification. Direct SHA256 and array comparisons showed byte-identical and
  array-identical master, weight, coverage, low-rejection, high-rejection, and
  DQ maps versus Gate687. This data set recorded
  `triangle_warp_identity_bypass_frame_count=0`, so the gate validates
  compatibility and future identity-matrix behavior rather than a speedup on
  the current M38 stack.
- Gate690 adds the hard Phase 2 mainline A/B validation command
  `glass phase2-mainline-ab`. The real 200-light candidate at
  `C:\glass_runs\phase2_s2_gate690_mainline_ab\runs_20260627_023000\mainline_weight_aligned`
  passed the mainline audit, resident regression versus Gate689, and the new
  A/B gate. The new gate requires passing pipeline/resident-result contracts,
  at least `190` active frames, elapsed ratio no higher than `1.15`, all six
  resident integration output classes, and SHA256/size stability for tracked
  FITS maps unless hash drift is explicitly allowed. The Gate690 candidate
  recorded `193` active frames, elapsed ratio `0.9895780022628549` versus
  Gate689, six tracked maps present, zero missing map patterns, and zero hash
  mismatches. Component timing was light read/upload/calibrate
  `3.44842360005714 s`, registration/warp `0.26703780062962323 s`, local
  normalization `0.3525654999539256 s`, integration
  `3.2566704000346363 s`, and output write `0.28603319998364896 s`. Final
  validation also fixed resident CUDA completion-queue frame-weight alignment:
  weights are now written by stack frame index rather than completion order.
- Gate691 promotes that frame-index invariant into the resident frame-mask
  runtime contract. The real 200-light candidate at
  `C:\glass_runs\phase2_s2_gate691_frame_index_alignment\runs_20260627_030000\frame_index_contract`
  passed the mainline audit, resident regression versus Gate690, and the Phase
  2 mainline A/B gate. The candidate recorded `193 / 7` active/masked frames,
  elapsed ratio `0.9972782917458977`, six tracked maps, zero hash mismatches,
  and `resident_frame_masks.json` reported
  `frame_index_alignment_contract.checked=true`, `passed=true`,
  `weight_mismatch_frame_count=0`, and `weight_missing_frame_count=0`.
  Component timing was light read/upload/calibrate `3.3616618000669405 s`,
  registration/warp `0.2609440995147452 s`, local normalization
  `0.3568277000449598 s`, integration `3.2981458000140265 s`, and output
  write `0.2789147000294179 s`.
- Gate692 connects the frame-index invariant to `glass phase2-mainline-ab`.
  The real 200-light current-default repeat at
  `C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\default_repeat`
  passed A/B versus Gate691 with failed checks `[]`, active/masked frames
  `193 / 7`, six tracked maps, zero hash mismatches, and
  `frame_index_alignment_status=passed`. The candidate elapsed ratio was
  `0.9312209070964549`, total elapsed `11.509678000002168 s`, light
  read/upload/calibrate `3.0809543000068516 s`, and integration
  `3.266167899942957 s`. A sequential wave-fill `0 us` probe also passed but
  was not promoted because the same-session current default was slightly faster
  than the wave0 candidate.
- Gate705 promoted the current resident native-completion default to
  `multi_wait_1000us` after the real 200-light default run at
  `C:\glass_runs\phase2_s2_gate705_completion_wavefill\runs_20260626_120000\default_promoted_multi1000`
  passed mainline and regression checks with zero output drift. The run
  recorded total elapsed `10.727156800101511 s`, light read/upload/calibrate
  `2.982370199984871 s`, resident integration `2.627562499954365 s`, native
  completion lane fill `0.9090909090909091`, and `55` native-completion waves.
- Gate706 retested the larger `8` stream / `8` frame calibration-wave candidate
  on the same 200-light mainline. The candidate at
  `C:\glass_runs\phase2_s2_gate706_calibration_lanes\runs_20260626_123000\streams8_wave8_candidate`
  passed the mainline audit and preserved all tracked integration FITS hashes,
  but `glass phase2-mainline-ab` failed `component_ratios_within_budget`:
  total elapsed ratio was `1.0327317952829496`, while
  `light_read_upload_calibrate` regressed from `2.982370199984871 s` to
  `3.173723299987614 s` (`1.0641614176548955x`). The default A/B budget for
  that component is now `1.05x`, so this candidate remains rejected despite
  correct output maps.
- Gate707 added an explicit native-completion H2D elapsed telemetry policy and
  kept detailed collection enabled by default. The default run at
  `C:\glass_runs\phase2_s2_gate707_h2d_timing_policy\runs_20260626_130000\default_h2d_timing_enabled`
  passed mainline and regression checks versus Gate705 with elapsed ratio
  `0.997238093861246`, zero tracked-map hash mismatches, active/masked frames
  `193 / 7`, and `native_completion_h2d_elapsed_collection_policy=default_enabled`.
  The same-code disabled candidate preserved outputs but was slower than the
  default at elapsed ratio `1.0361399053534472`, so
  `GLASS_RESIDENT_NATIVE_COMPLETION_H2D_TIMING=0` remains a diagnostic opt-out
  rather than a promoted default.
- Gate708 moved the public CPU master-frame helpers onto `CPUStackEngine` by
  default. The synthetic validation artifact
  `runs/checkpoints/s2_gate_708_cpu_master_stack_engine_helper/validation.json`
  records `engine=stack_engine_cpu`, invalid/non-finite input samples `2`,
  valid samples after rejection `6`, and a passing StackEngine result contract
  for a generated invalid-sample fixture. The same artifact records a generated
  `24 x 32` synthetic bias master with DQ summary `valid=768` and
  `master_postprocess_operation=bias_mean`. This is CPU baseline/API contract
  consolidation only; it does not change the resident CUDA 200-light hot path.
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
