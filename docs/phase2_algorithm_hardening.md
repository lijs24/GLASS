# GLASS Phase 2: Algorithm Hardening

This document is the controlling execution plan for GLASS Phase 2. The first
phase proved that the project can run a Windows CUDA pipeline on a real
200-light dataset and preserve a large speed advantage over an external
reference stack. Phase 2 turns that working prototype into a durable scientific
algorithm core.

## Mission

Phase 2 focuses on algorithm consolidation, not feature sprawl. The required
outcome is a unified, testable, GPU-oriented processing core where master frame
construction and final light integration share the same stacking engine and the
same mask, rejection, weighting, and reporting contracts.

## Codex Goal Anchor

Use this document as the authoritative long-form execution contract for Phase
2. The interactive `/goal` text should stay short and point here instead of
duplicating every gate, benchmark, and algorithm rule.

Recommended goal text:

```text
GLASS Phase 2: follow docs/phase2_algorithm_hardening.md as the controlling plan. Advance S2-Gates in order; every gate needs code or docs, focused tests, full pytest, a checkpoint, and a Git commit. Failed gates must be fixed before later work. Preserve the Phase 1 200-light benchmark as the speed and numerical baseline; do not accept unexplained runtime, shape, frame-count, mask/rejection, or result-agreement regressions. New algorithms need CPU baselines, synthetic tests, CUDA comparisons where relevant, auditable artifacts, and updates to docs/algorithm_sources.md. Input image directories stay read-only. CUDA remains optional and CPU-only install/tests must keep working.
```
## Hard Constraints

- Keep the existing 200-light real dataset benchmark as a performance and
  numerical baseline.
- Do not accept unexplained regressions in runtime, output shape, frame count,
  rejection behavior, or numerical agreement.
- Prefer CPU baselines first for new scientific behavior, then add CUDA
  acceleration with CPU/GPU comparison tests.
- Keep FITS processing healthy while XISF support evolves.
- Treat user image directories as read-only.
- Keep CUDA optional: CPU-only install and tests must continue to work.
- Every new algorithm path needs tests, diagnostics, and a resumable artifact
  story before it becomes a default path.
- Record algorithm sources and parameter origins in
  `docs/algorithm_sources.md`.
- Do not implement opaque black boxes. Numeric decisions must be explainable in
  code, tests, reports, or documentation.

## Baseline To Preserve

The Phase 1 benchmark is the regression anchor:

- Dataset: 200 light frames with at least 20 frames for each calibration class.
- Reference runtime: recorded in the release benchmark summary.
- GLASS CUDA 11/12/13 runtimes: recorded in the release benchmark summary.
- Output agreement: recorded as image difference statistics against the
  reference output and across CUDA package variants.

Before and after each major engine change, run a small synthetic regression. At
major gates, run the real 200-light benchmark or a documented representative
subset when GPU time is constrained.

### Phase 1 Benchmark Record

Authoritative local baseline files:

- `C:\glass_runs\cuda_version_matrix_200\cuda_version_matrix_summary_v8.json`
- `C:\glass_runs\cuda_version_matrix_200\cuda_version_matrix_summary_v8.md`

Release baseline:

- Release tag: `v0.1.0-windows-gpu.8`
- Release URL: `https://github.com/lijs24/GLASS/releases/tag/v0.1.0-windows-gpu.8`
- Dataset label: `M38_H_200light_20bias_20dark_20flat`
- Processing plan:
  `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- External reference runtime: `1092.541 s`
- External reference master:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf`
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Driver version: `596.21`
- VRAM: `97886 MiB`

Package baselines:

| Package | Runtime | Speedup vs reference | RMS vs reference | P99 absolute difference vs reference | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `cuda11` | `30.361 s` | `35.98x` | `0.00155829` | `0.000430955` | Native CUDA loaded. |
| `cuda12` | `30.515 s` | `35.80x` | `0.00155829` | `0.000430955` | Native CUDA loaded; bit-identical to cuda11 in this run. |
| `cuda13` | `32.004 s` | `34.14x` | `0.00155911` | `0.000430912` | Native CUDA loaded; raw GLASS output differed from cuda11 by about `0.001139` relative RMS. |

Regression interpretation:

- Any major Phase 2 gate that changes calibration, registration, warp, local
  normalization, or integration must compare against this record.
- A runtime regression above 15 percent on the 200-light benchmark requires a
  written explanation and a follow-up optimization plan before the new path can
  replace the Phase 1 default.
- Shape mismatches, unexplained frame-count changes, missing maps, or silent
  registration failures are blocking regressions.
- CUDA-package numerical differences are acceptable only when documented and
  reference-level image agreement remains within the recorded tolerance family.

## Core Contracts

Phase 2 must introduce or stabilize these contracts:

- `ImageSource`: unified read abstraction for FITS, XISF, cache, memory-mapped,
  and resident CUDA image data.
- `TileWindow`: explicit rectangular pixel window with channel, overlap, and
  origin metadata.
- `DQMask`: internal data-quality bitfield propagated through calibration,
  registration, warp, local normalization, and integration.
- `FrameTransform`: per-frame operation that can prepare state and apply itself
  to a tile while updating DQ and metrics.
- `StackRequest`: complete declarative request for stacking a set of frames.
- `CombinePolicy`: mean, median, sum, weighted mean, and later drizzle.
- `RejectionPolicy`: none, min/max, percentile, sigma, MAD, median sigma, and
  winsorized sigma.
- `OutputMapPolicy`: coverage, weight, variance, low rejection, high rejection,
  and DQ output maps.

## Unified StackEngine

Master calibration frames and final integrated lights must use one engine:

- Master bias is `StackEngine(BIAS frames, combine, rejection, maps)`.
- Master dark is `StackEngine(DARK frames, preprocess=[bias?], combine,
  rejection, maps)`.
- Master flat is `StackEngine(FLAT frames, preprocess=[bias, dark],
  normalization, combine, rejection, maps)`.
- Final light master is `StackEngine(LIGHT frames, preprocess=[calibration,
  registration, warp, local normalization], weights, rejection, maps)`.

The StackEngine must work in CPU tiled mode first, then CUDA tiled/resident
mode. Full-frame and tiled CPU outputs must match within documented tolerances.

## Data Quality Mask

DQ/mask propagation is an internal contract, not a final-report afterthought.
The bitfield must cover at least:

- no data
- saturated
- hot, cold, or dead pixel
- cosmetic-corrected pixel
- warp edge or invalid resampling footprint
- local-normalization excluded pixel
- low rejection
- high rejection

Each stage must document whether it consumes, modifies, or only forwards DQ.

## Calibration Completion

Calibration must support:

- robust master bias
- master dark with explicit bias semantics
- master flat with per-flat normalization and floor protection
- scaled dark subtraction
- pedestal
- overscan and trim first pass
- cosmetic correction first pass
- calibration diagnostics in JSON and HTML reports

The light calibration formula and all policy choices must be visible in code,
tests, and reports.

## Quality, Registration, Warp, And LN

The second stage must harden the image-alignment path:

- Star detection should move from a minimal detector to a DAOFIND-like or
  equivalent open, documented algorithm.
- Subframe quality must include star count, background, noise, FWHM,
  eccentricity, SNR proxy, saturation fraction, registration RMS, and final
  weight.
- Registration must support a model ladder: translation, similarity, affine,
  and homography.
- Robust matching must expose matched stars, inliers, RMS, status, and warnings.
- Failed registration frames must not silently enter integration.
- Warp must use an interpolator registry: nearest, bilinear, bicubic, and
  Lanczos 3 at minimum.
- Local normalization must evolve from tile constants to a continuous coefficient
  field `O(x,y) = a(x,y)S(x,y) + b(x,y)` with coefficient and residual maps.

## Integration And Rejection

Integration must support:

- weighted mean
- coverage map
- weight map
- variance map
- low and high rejection maps
- sigma, MAD, median sigma, percentile/min-max, and winsorized sigma rejection
- first-pass variance-aware weighting

The rejection implementation must be shared by master-frame stacking and light
integration where applicable.

## Phase 2 Gates

### S2-Gate 0: Baseline And Documentation

- Create this document and `docs/algorithm_sources.md`.
- Record current release benchmark paths and expected regression metrics.
- Add a checkpoint under `runs/checkpoints/`.
- Run tests.
- Commit with `s2-gate-00: phase 2 baseline and algorithm source tracking`.

### S2-Gate 1: Core Contracts

- Implement minimal stable interfaces for the core contracts.
- Keep the old pipeline running through adapters.
- Add schema and interface tests.

### S2-Gate 2: CPU/Tiled StackEngine

- Implement CPU/tiled mean, median, weighted mean, maps, and basic rejection.
- Prove full-frame and tiled output equivalence on synthetic data.

### S2-Gate 3: StackEngine Integration

- Use StackEngine for master frames and light integration.
- Keep the previous path as fallback until the new path is validated.
- Run a 200-light smoke or representative benchmark and record regression data.

### S2-Gate 4: DQ/Mask Propagation

- Add DQ bitfield support to calibration, warp, LN, and integration.
- Emit DQ summaries and optional maps.

### S2-Gate 5: Robust Calibration

- Complete robust bias, dark, flat, pedestal, overscan, trim, and cosmetic
  correction first passes.
- Report calibration statistics and policy choices.

### S2-Gate 6: Star/PSF Quality And Weighting

- Implement improved star detection and subframe quality metrics.
- Add simple SNR and combined weighting.

### S2-Gate 7: Registration And Warp Hardening

- Implement robust matching, model ladder, registration validation, and
  interpolator registry.
- Validate with synthetic known shifts and rotations.

### S2-Gate 8: Continuous Local Normalization

- Implement continuous LN coefficient fields and diagnostics.
- Record crop boxes if any crop is introduced.

### S2-Gate 9: Rejection And Variance Integration

- Complete winsorized sigma and additional rejection modes.
- Add variance-aware weighting and variance map output.

### S2-Gate 10: XISF, Report, And Real-Data Regression

- Stabilize XISF metadata and safe cache-based image input.
- Expand report coverage for all major stages.
- Run the 200-light benchmark again and compare against Phase 1.

### S2-Gate 11: Benchmark Contract And Regression Guard

- Codify the Phase 1/2 200-light benchmark parameters, scale/offset, coverage
  threshold, required command tokens, and runtime envelope as a machine-readable
  contract.
- Make the acceptance audit consume that contract and fail when benchmark
  parameters drift silently.
- Run the contract against the current 200-light real-data artifacts and record
  whether runtime and numerical results remain within the allowed envelope.

### S2-Gate 12: Performance Regression Diagnostics

- Add per-stage resident CUDA timing baselines to the benchmark contract.
- Make acceptance audit report non-blocking timing diagnostics for stages that
  regress beyond the documented warning factor.
- Use the diagnostics to name the next optimization target without weakening
  the existing hard pass/fail checks for runtime, frame counts, and image
  agreement.

### S2-Gate 13: Resident Output Map Storage Recovery

- Preserve resident master and weight outputs as `float32`.
- Store integer count maps such as coverage and rejection maps using integer
  FITS image types when the frame count fits the selected dtype.
- Record per-map output write timing and estimated data bytes in
  `resident_artifacts.json`.
- Make `glass run` and `glass audit` write `run_command.txt` so benchmark
  contract audits can prove that required command tokens were used.
- Validate the 200-light benchmark again and compare image agreement against
  the release reference output.

### S2-Gate 14: Resident Parallel Output Write Diagnostics

- Write independent resident FITS outputs through a bounded worker pool.
- Preserve the S2-Gate 13 dtype contract for master, weight, coverage, and
  rejection maps.
- Record output-write mode, worker count, per-file timing, and storage
  diagnostics in `resident_artifacts.json`.
- Run a cold-output 200-light benchmark and acceptance audit to separate
  output-write recovery from hot-cache master reuse.

### S2-Gate 15: Shared Resident Master Cache

- Add an explicit `--resident-master-cache-dir` option for `glass run` and
  `glass audit`.
- Keep the default cache run-local, but allow an opt-in shared resident
  master-frame cache across output directories.
- Fingerprint cache entries from frame metadata, file size/mtime, calibration
  groups, shape, filter, and calibration policy so stale or mismatched cache
  entries are not silently reused.
- Record cache scope, key, fingerprint, hit/miss, and cache directory in
  `resident_artifacts.json`.
- Validate the cache-hit 200-light benchmark against the release reference
  output and benchmark contract.

### S2-Gate 16: Resident I/O Overlap Timing Semantics

- Separate resident light-read consumer wait wall time from cumulative
  read-worker FITS open/decode time in `resident_artifacts.json`.
- Record overlap diagnostics for the I/O + upload + calibration pipeline:
  wall-clock stage time, consumer wait time, worker cumulative time, estimated
  overlap saved, wait fraction, and worker-to-wall ratio.
- Keep legacy timing keys for compatibility, but add explicit
  `*_worker_cumulative` and `light_read_wait_wall` aliases.
- Update the 200-light benchmark contract so cumulative worker timings are
  informational diagnostics rather than wall-clock regression failures.
- Validate that acceptance audit still flags real wall-clock regressions while
  excluding cumulative prefetch-worker totals from `regressed_count`.

### S2-Gate 17: Resident CUDA DQ Map Parity

- Make the resident CUDA integration path emit a formal integration DQ map, not
  only coverage and rejection count maps.
- Encode at least `NO_DATA`, `LOW_REJECTED`, and `HIGH_REJECTED` flags from
  resident master, weight, coverage, and rejection outputs.
- Record `dq_map_path`, `dq_summary`, and flag bit meanings in
  `resident_artifacts.json`, and mirror `dq_map_path`/`dq_summary` into
  `integration_results.json`.
- Keep the CPU StackEngine/DQ path unchanged while closing the production
  resident CUDA artifact gap.
- Validate small CUDA tests and the 200-light benchmark contract again because
  the resident output set now includes one more diagnostic map.

### S2-Gate 18: Resident Output Map Policy

- Add an explicit `--resident-output-maps` policy for `glass run` and
  `glass audit`.
- Keep `audit` as the default policy and preserve the full diagnostic output
  set: master, weight, coverage, DQ, low rejection, and high rejection maps
  when those maps are available.
- Add `science` mode for normal validated output: master, weight, coverage, and
  DQ maps while skipping low/high rejection count FITS files.
- Add `minimal` mode for maximum-speed exploratory runs: master FITS only.
- Record available, written, and skipped maps in `resident_artifacts.json` and
  `integration_results.json` so output choices are auditable and reproducible.
- Validate the policy on small CUDA fixtures and rerun a 200-light science-mode
  benchmark because the output set now affects wall-clock performance.

### S2-Gate 19: Resident Output Policy Reporting

- Surface resident output-map policy decisions in the HTML report, not only in
  JSON artifacts.
- Report the policy mode, available maps, written maps, and skipped maps from
  `integration_results.json` and `resident_artifacts.json`.
- Keep the report readable when a run has no resident output policy.
- Validate with CLI report smoke tests; this is a reporting-only gate and does
  not require rerunning the 200-light benchmark unless compute artifacts change.

### S2-Gate 20: Resident Warp-Edge DQ Semantics

- Extend the resident CUDA integration DQ map to encode `WARP_EDGE` when the
  resident coverage map proves that a pixel has no valid contributing warp
  footprint.
- Preserve `NO_DATA`, `LOW_REJECTED`, and `HIGH_REJECTED` behavior.
- Record the `WARP_EDGE` bit in DQ FITS headers and resident artifact
  `dq_flag_bits`.
- Keep the first resident implementation conservative: do not infer partial
  edge pixels from reduced coverage when rejection maps may also reduce
  coverage.
- Validate with direct DQ helper tests and resident CUDA smoke tests.

### S2-Gate 21: Resident DQ Coverage Provenance

- Record resident coverage provenance alongside the DQ map.
- Separate post-rejection integration coverage from finite pre-rejection sample
  coverage by using `coverage + low_rejection + high_rejection` when rejection
  maps are available.
- Report zero pre-rejection pixels, partial pre-rejection pixels, rejection
  reduced pixels, and rejected sample counts in `resident_artifacts.json` and
  `integration_results.json`.
- Keep partial warp-edge inference deferred until a pure geometric
  pre-rejection warp coverage map exists.
- Validate with direct helper tests, resident CUDA smoke tests, and the
  200-light benchmark because the artifact is produced on the resident fast
  path.

### S2-Gate 22: Resident Geometric Warp Coverage

- Add a resident CUDA geometric warp-footprint accumulator that consumes the
  per-frame coverage output from resident translation, matrix bilinear, and
  matrix Lanczos warp kernels.
- Add a native method to record full-frame coverage for active frames that do
  not need a warp, including reference frames and registration-off runs.
- Record geometric warp coverage statistics and frame counts in
  `resident_artifacts.json` and `integration_results.json`.
- Use the geometric map to mark partial `WARP_EDGE` DQ pixels when the native
  signal is available, while keeping post-rejection coverage and rejection
  counts separate.
- Validate with direct CUDA resident-stack tests, DQ helper tests, resident
  CLI smoke tests, full pytest, and the 200-light benchmark because this changes
  the resident fast path artifacts.

### S2-Gate 23: Geometric Warp Coverage Reporting

- Surface resident geometric warp coverage as a first-class HTML report table
  instead of requiring users to inspect nested JSON provenance.
- Include active frame count, geometric coverage frame count, frame-count match
  status, coverage min/max/mean, zero/partial/full pixel counts, and DQ
  `WARP_EDGE`/`NO_DATA` counts when available.
- Keep the table readable for resident and integration artifact sources, and
  keep older runs without the new schema reportable.
- Validate with CLI report tests, ruff, full pytest, and a report regeneration
  on the most recent 200-light resident run.

### S2-Gate 24: Fused Resident Warp Coverage Accumulation

- Fuse geometric warp coverage accumulation into resident CUDA translation,
  matrix bilinear, and matrix Lanczos warp kernels.
- Preserve the standalone warp wrapper API by passing a null accumulator for
  one-off Python calls.
- Keep full-frame coverage accounting for unwarped active frames on its
  existing resident method.
- Validate that the fused path preserves geometric coverage frame counts,
  partial warp-edge DQ semantics, and 200-light numerical agreement while
  removing the extra per-warp coverage-accumulation launch.
- Validate with resident CUDA stack tests, CUDA smoke tests, ruff, full pytest,
  and the 200-light benchmark because this changes the resident fast path.

### S2-Gate 25: StackEngine DQ Provenance

- Add a first-pass DQ provenance contract to the CPU StackEngine result.
- Record source DQ flag counts, flagged sample counts, non-finite sample
  counts, output zero-coverage pixels, rejected-pixel counts, and output DQ
  summaries.
- Keep current StackEngine combine/rejection numerical behavior unchanged:
  source DQ and non-finite samples remain invalid stack samples, while output
  DQ marks no-data and low/high rejection pixels.
- Validate with direct StackEngine synthetic tests, ruff, and full pytest.
- A 200-light benchmark rerun is not required unless this gate changes the
  resident CUDA fast path or default pipeline routing.

### S2-Gate 26: StackEngine DQ Provenance Artifacts

- Write StackEngine DQ provenance into master calibration artifacts and CPU
  integration outputs whenever those stages use StackEngine.
- Surface StackEngine DQ provenance in the HTML report as a first-class table
  rather than requiring users to inspect nested JSON.
- Keep resident CUDA DQ provenance on its existing resident schema while the
  CPU StackEngine bridge matures.
- Validate with pipeline fixture tests, report HTML checks, ruff, and full
  pytest.
- A 200-light benchmark rerun is not required unless this gate changes resident
  CUDA routing or image math.

### S2-Gate 27: Unified DQ Provenance Summary Contract

- Add a compact `dq_provenance_summary` schema that can be emitted by both CPU
  StackEngine artifacts and resident CUDA artifacts.
- Preserve detailed source schemas such as `stack_engine_dq_provenance` and
  `dq_coverage_provenance`; the summary is a bridge for report and audit
  consumers, not a replacement.
- Record common fields for engine, stage, item, source schema, sample counts,
  zero/partial coverage, rejection pixels, and DQ summary counts when the source
  can provide them.
- Surface the normalized summary in the HTML report as `DQ provenance contract`.
- Validate with direct DQ helper tests, pipeline/report tests, resident CUDA
  smoke tests, ruff, and full pytest.
- A 200-light benchmark rerun is not required unless this gate changes resident
  CUDA image math or benchmark routing.

### S2-Gate 28: DQ Provenance Acceptance Contract

- Extend the benchmark acceptance contract so real-data audits can require DQ
  provenance records, expected source schemas, engines, DQ maps, active-frame
  counts, source terms, and output DQ summary flags.
- Make `acceptance-audit` collect normalized DQ provenance records from
  `integration_results.json` and `resident_artifacts.json`.
- Preserve compatibility with S2-Gate 17-24 resident artifacts by normalizing
  legacy `dq_coverage_provenance` plus `dq_summary` into the S2-Gate 27 compact
  summary during audit.
- Update the 200-light benchmark contract to require resident CUDA DQ
  provenance without changing image math or resident execution routing.
- Validate with acceptance-audit unit tests, ruff, full pytest, and a contract
  audit against the latest preserved 200-light resident artifacts when those
  artifacts are locally available.

### S2-Gate 29: DQ FITS Map Pixel Verification

- Add a tiled DQ FITS map verifier that counts bitfield flags from map pixels
  without loading the whole image into memory.
- Let benchmark contracts opt into pixel verification and require selected DQ
  map counts to match artifact `output_dq_summary` values within an explicit
  pixel tolerance.
- Keep the verifier optional so normal acceptance audits can remain lightweight
  and older contracts remain compatible.
- Update the 200-light benchmark contract to verify resident `valid`,
  `WARP_EDGE`, `LOW_REJECTED`, and `HIGH_REJECTED` DQ counts against the actual
  resident DQ FITS map.
- Validate with direct DQ map tests, acceptance-audit tests, ruff, full pytest,
  and a contract audit against the latest preserved 200-light resident
  artifacts.

### S2-Gate 30: Coverage And Rejection Map Consistency Verification

- Extend the tiled map verifier to summarize scalar count maps such as
  coverage and rejection maps without loading full images into memory.
- Let benchmark contracts verify coverage-map finite pixels against
  `dq_coverage_provenance.post_rejection_coverage.finite_pixels`.
- Verify that coverage zero-or-less pixels match DQ `NO_DATA` counts when the
  contract opts into that exact resident invariant.
- When low/high rejection maps are written, verify positive-pixel counts against
  DQ `LOW_REJECTED`/`HIGH_REJECTED` flags and verify total rejection-map sample
  sums against `rejected_sample_count` with an explicit sample-count tolerance
  for integer count-map write rounding.
- When a resident output-map policy intentionally skips low/high rejection map
  FITS files, acceptance audit must report that as an explicit skipped-policy
  PASS rather than silently ignoring the maps.
- Validate with direct count-map tests, acceptance-audit tests, ruff, full
  pytest, and a contract audit against the latest preserved 200-light resident
  artifacts.

### S2-Gate 31: Real-Data Audit-Map Rejection Verification

- Run the 200-light resident CUDA benchmark with `--resident-output-maps audit`
  so low/high rejection FITS maps are actually written.
- Add a strict audit-map benchmark contract that requires
  `--resident-output-maps audit`, forbids policy-skipped rejection maps, and
  verifies low/high rejection map positive pixels and total rejected samples on
  real data.
- Keep the original science-mode benchmark contract unchanged for the release
  speed baseline.
- Compare the audit-map master against the same external reference output and
  record runtime and numerical agreement.
- Validate with acceptance-audit, ruff, full pytest, checkpoint, and commit.

### S2-Gate 32: Resident Artifact Output Path Completeness

- Mirror all resident output map paths into `resident_artifacts.json`,
  including master, weight, coverage, low rejection, high rejection, and DQ
  maps.
- Mirror resident output write storage metadata into the resident artifact so
  audit consumers do not need to join against `integration_results.json` to
  explain written artifacts.
- Extend the benchmark DQ provenance contract so it can require resident
  artifact map paths and verify that each path exists.
- Validate the strict audit-map contract on the 200-light resident CUDA run, so
  the real-data artifact record is self-contained for map provenance, pixel
  verification, and output-storage review.
- Validate with focused resident/audit tests, ruff, full pytest, real-data
  compare, acceptance-audit, checkpoint, and commit.

### S2-Gate 33: Resident Output Map Report Provenance

- Surface resident output map paths as a first-class HTML report table.
- For each resident map, show policy status, path, existence, storage dtype,
  estimated payload size, and per-map write timing when available.
- Resolve relative artifact paths against the run directory so report output
  can distinguish missing files from policy-skipped maps.
- Keep the report path read-only and diagnostic-only; this gate must not change
  image math or resident execution routing.
- Validate with CLI report tests, ruff, full pytest, and a report regeneration
  on the latest 200-light resident audit-map run.

### S2-Gate 34: Report Noise Reduction With Focused Summaries

- Replace broad nested integration-output and DQ provenance dumps in the HTML
  report with focused summary tables.
- Add a compact integration-output table that keeps source stage, backend,
  memory mode, frame counts, weighting/rejection, master path, StackEngine flag,
  resident integration time, and peak memory.
- Add a flattened output-diagnostics table for range, clipping, finite-pixel,
  and normalization-probe values from integration and resident artifacts.
- Keep detailed JSON artifacts on disk for audit, but avoid rendering large
  dictionaries directly into report table cells.
- Validate with CLI report tests, ruff, full pytest, and a report regeneration
  on the latest 200-light resident audit-map run.

### S2-Gate 35: Benchmark Comparison In Main Report

- Let `glass report` summarize compare JSON and acceptance-audit JSON artifacts
  in the main HTML report.
- Auto-discover the newest `*compare*.json` and `*acceptance_audit*.json` files
  in the run directory, with explicit CLI overrides for both.
- Surface speedup, GLASS/reference elapsed time, RMS, P99 absolute difference,
  coverage fraction, compared pixels, active/zero-weight frames, calibration
  frame counts, acceptance status, contract name, and check counts.
- Keep compare/audit JSON files as the authoritative artifacts; the report
  should only present their high-signal fields.
- Validate with CLI report tests, ruff, full pytest, and a report regeneration
  on the latest 200-light resident audit-map run.

### S2-Gate 36: Acceptance Failure Triage In Main Report

- Add a compact acceptance-check failure table to the main HTML report.
- Only failed checks should appear; green runs should show an empty table and
  keep the full authoritative check list in the audit JSON.
- For each failed check, show the check name, note, actual value, required
  threshold/value, and compact remaining evidence fields.
- Keep this as a report-only diagnostic path that does not alter compare,
  acceptance-audit, or image artifacts.
- Validate with CLI report tests for both green and failed audit fixtures, ruff,
  full pytest, and a report regeneration on the latest 200-light resident
  audit-map run.

### S2-Gate 37: Report Navigation Anchors

- Add a static table of contents to the main HTML report so large benchmark
  reports can jump directly to timing, comparison, resident map, and failure
  sections.
- Give every major report section a stable `id` and include a lightweight
  per-section anchor link for shareable diagnostics.
- Keep this as static HTML with no JavaScript and no artifact schema changes.
- Validate with CLI report tests, ruff, full pytest, and a report regeneration
  on the latest 200-light resident audit-map run.

### S2-Gate 38: Large Report Table Limits

- Keep large HTML reports responsive by limiting high-cardinality tables to a
  fixed first-page preview in the rendered report.
- Apply the preview limit to input frames, light plans, frame quality,
  registration, local normalization, and timing rows.
- Show the displayed row count, total row count, and authoritative artifact
  path so the HTML report remains auditable without pretending to contain every
  row.
- Do not truncate or rewrite JSON/FITS artifacts; this is a report-only
  presentation limit.
- Validate with CLI report tests, ruff, full pytest, and a report regeneration
  on the latest 200-light resident audit-map run.

### S2-Gate 39: Quality Gate Reference Candidates

- Add an explicit quality-gate artifact contract to `frame_quality.json`.
- Mark each calibrated light as accepted or rejected for automatic reference
  selection using star count, saturation fraction, optional quality score, and
  FWHM availability.
- Select the automatic reference frame from accepted quality-gate candidates
  first, with an explicit fallback flag when every frame fails the gate.
- Surface quality-gate counts and policy in the HTML report.
- Validate with synthetic quality tests, pipeline/report tests, ruff, full
  pytest, and a report regeneration on the latest 200-light resident audit-map
  run.

### S2-Gate 40: Registration Honors Quality Gate

- Make registration consume `frame_quality.json` quality-gate status.
- When `reject_quality_gate_failed_frames` is enabled, skip non-reference
  frames with `quality_gate_status=rejected` before star matching or preview
  registration.
- Record quality-gate status, warnings, enforcement state, and rejected-frame
  counts in `registration_results.json`.
- Let warp/integration continue using the existing accepted-registration
  contract so quality-rejected frames do not silently enter downstream stages.
- Preserve backward compatibility for older quality artifacts that do not have
  quality-gate fields.
- Validate with registration and pipeline tests, ruff, full pytest, and a
  report regeneration on the latest 200-light resident audit-map run.

### S2-Gate 41: Shared Accepted-Frame Accounting Summary

- Add `frame_accounting.json` as the shared per-light ledger for quality,
  registration, warp, local normalization, integration weight, and final
  use/skip status.
- Generate the accounting artifact automatically after both tiled integration
  and resident CUDA integration so downstream report/audit tooling does not need
  to re-derive accepted frame counts from scattered JSON files.
- Preserve every input light from `processing_plan.json`, then merge stage
  records from calibration artifacts, `frame_quality.json`,
  `registration_results.json`, `warp_results.json`, `local_norm_results.json`,
  and `integration_results.json`.
- Record explicit final states such as `integrated`, `zero_weight`,
  `quality_rejected`, `registration_rejected`, `warp_skipped`, and
  `not_integrated`, with reasons/warnings carried from upstream artifacts.
- Surface a compact accounting summary and limited per-frame table in the HTML
  report while keeping the JSON artifact authoritative for large runs.
- Keep this diagnostic-only: it must not change calibration, registration,
  local-normalization, rejection, or master-light pixel math.
- Validate with direct accounting tests, pipeline/report tests, ruff, full
  pytest, and a report regeneration on the latest preserved 200-light resident
  artifacts.

### S2-Gate 42: Frame Accounting Acceptance Contract

- Add `frame_accounting` requirements to benchmark contracts so real-data
  acceptance cannot pass without the per-light ledger.
- Verify that `frame_accounting.json` exists, uses the expected resident source
  stage, and records the required input, integrated, zero-weight, and
  registration-accepted frame counts.
- Cross-check accounting against `integration_results.json` frame weights,
  speedup summary active/zero-weight counts, DQ provenance active-frame counts,
  and resident registration status counts.
- Update the M38 H-alpha 200-light science and audit-map contracts to require
  200 input lights, 193 integrated lights, and 7 zero-weight lights.
- Include frame-accounting evidence in acceptance-audit JSON/Markdown output so
  benchmark failures explain which count drifted.
- Keep this gate audit-only: it must not alter image math, GPU kernels, or
  runtime scheduling.
- Validate with acceptance-audit tests for pass and mismatch cases, ruff, full
  pytest, and a strict acceptance audit against the latest preserved 200-light
  resident artifacts.

### S2-Gate 43: Rejected-Frame Focused Accounting

- Extend `frame_accounting.json` with `exception_frames` and
  `exception_summary` so non-integrated frames are easy to inspect without
  scanning the full light table.
- For each exception frame, record the final status, primary pipeline stage,
  primary reason, weight, stage statuses, warning/reason counts, and input path.
- Surface a dedicated HTML report section for rejected/zero-weight frames,
  keeping the complete per-frame ledger in `frame_accounting.json`.
- Include exception-frame summary and the first rejected frames in
  acceptance-audit Markdown output.
- Keep this diagnostic-only: it must not alter accepted frames, rejection math,
  registration behavior, GPU kernels, or output pixels.
- Validate with direct frame-accounting tests, report tests, acceptance-audit
  tests, ruff, full pytest, and a report/audit regeneration on the latest
  preserved 200-light resident artifacts.

### S2-Gate 44: Optimization Guidance Contract

- Add a machine-readable `optimization_guidance` section to acceptance-audit
  output that joins benchmark timing diagnostics with frame-accounting exception
  context.
- Name the primary optimization target from resident wall-clock stages, with
  special focus on:
  - I/O + upload + calibration overlap
  - resident registration/warp batching
  - output-map write policy
  - resident master-frame cache
- Keep cumulative worker-thread FITS/decode timings informational so they do
  not outrank true wall-clock bottlenecks.
- Surface the guidance in acceptance-audit Markdown and the main HTML report,
  including target rank, stage timing, baseline factor, exception context, and
  concrete next action.
- Keep this diagnostic-only: it must not alter image math, accepted frame
  counts, GPU kernels, scheduling, or output pixels.
- Validate with acceptance-audit tests, report tests, ruff, full pytest, and a
  report/audit regeneration on the latest preserved 200-light resident
  artifacts.

### S2-Gate 45: Resident Warp Scratch Reuse

- Remove per-frame `cudaMalloc`/`cudaFree` churn from resident CUDA translation,
  matrix bilinear, and matrix Lanczos warp application by allocating reusable
  device scratch buffers inside `ResidentCalibratedStack`.
- Keep resident warp output pixels, geometric coverage accumulation, and DQ
  semantics unchanged.
- Expose `warp_scratch_bytes` through the native binding and Python wrapper, and
  record the value in `resident_artifacts.json` and the HTML resident summary.
- Validate with direct resident CUDA stack tests, resident triangle-registration
  smoke tests, full pytest, and a 200-light benchmark rerun because this changes
  the resident registration/warp fast path.

### S2-Gate 46: Async Resident Warp Copy Dispatch

- Remove per-frame host synchronization from resident CUDA translation, matrix
  bilinear, and matrix Lanczos warp application after successful kernel launch.
- Copy the reusable warp scratch buffer back into the resident frame stack with
  default-stream asynchronous device-to-device copies so subsequent same-stream
  registration/integration operations preserve ordering without blocking Python
  after every frame.
- Expose and report the warp copy mode as
  `default_stream_async_device_to_device` in native/Python APIs,
  `resident_artifacts.json`, and the HTML resident summary.
- Keep error handling clear: launch errors are checked immediately, while later
  synchronization points in integration/download surface asynchronous execution
  failures.
- Validate with direct resident CUDA stack tests, resident triangle-registration
  smoke tests, full pytest, and a 200-light benchmark rerun because this changes
  the resident registration/warp fast path.

### S2-Gate 47: Batch Resident Triangle Pixel Refinement

- Add a native resident CUDA batch API that refines one seed matrix for each
  moving frame against a shared reference frame, reusing the same search
  parameters and reducing Python/native call count in triangle registration.
- Route resident `similarity_cuda_triangle` through deferred batch pixel
  refinement when the native API is available, then apply quality gates and
  resident warp after the batch returns.
- Record `triangle_pixel_refine_batch` and
  `triangle_pixel_refine_batch_mode` in resident artifacts, and emit timing for
  `triangle_pixel_refine_batch`.
- Preserve per-frame registration results, weights, frame accounting, image
  dimensions, geometric coverage, and output pixels within the existing
  benchmark tolerance family.
- Validate with direct resident CUDA stack batch/single equivalence tests,
  resident triangle-registration smoke tests, full pytest, and the 200-light
  benchmark.

### S2-Gate 48: Batch Resident Triangle Descriptor Fit

- Add a native CUDA batch API that estimates triangle-descriptor similarity
  fits for multiple moving catalogs against one shared reference catalog and
  reference descriptor set.
- Route resident `similarity_cuda_triangle` through the batch fit path when the
  fixed-threshold resident catalog batch path is available, while preserving the
  per-frame fallback for auto-threshold or unsupported native builds.
- Record `triangle_descriptor_fit_batch` and
  `triangle_descriptor_fit_batch_mode` in resident artifacts, surface the mode
  in the HTML resident summary, and emit timing for
  `triangle_descriptor_fit_batch`.
- Preserve per-frame selected fit, registration results, batch pixel refine,
  frame accounting, image dimensions, geometric coverage, and output pixels
  within the existing benchmark tolerance family.
- Validate with direct CUDA batch/single descriptor-fit equivalence tests,
  resident triangle-registration smoke tests, full pytest, and the 200-light
  benchmark because this changes resident registration scheduling.

### S2-Gate 49: Shared Reference Device Buffers For Triangle Descriptor Fit

- Replace the first batch descriptor-fit implementation's internal per-frame
  single-fit loop with a native batch implementation that uploads the shared
  reference catalog, reference descriptors, and reference indices to device
  memory once per batch.
- Reuse those reference device buffers for every moving catalog in the batch
  while preserving the existing CUDA descriptor-similarity kernel, matrix
  output, inlier counts, RMS, and candidate-count semantics.
- Record `reference_device_reuse` and `reference_device_bytes` in batch-fit
  results, resident per-frame warnings, resident artifacts, and the HTML
  resident summary.
- Keep the public batch API and resident fallback behavior stable for CPU-only
  installs and older native builds.
- Validate with direct CUDA batch/single descriptor-fit equivalence tests,
  resident triangle-registration smoke tests, ruff, full pytest, and the
  200-light benchmark because this changes native registration memory
  scheduling.

### S2-Gate 50: Shared Moving And Output Device Buffers For Descriptor Fit

- Extend the native triangle descriptor batch fit to pre-validate moving
  catalogs/descriptors, allocate moving-catalog and output/candidate device
  workspaces once per batch, then reuse those buffers for each moving-frame fit
  alongside the S2-Gate 49 shared reference buffers.
- Preserve descriptor generation, CUDA descriptor-similarity scoring, matrix
  output, inlier counts, RMS, candidate-count semantics, and resident
  registration frame accounting.
- Record `moving_device_reuse`, `moving_device_bytes`,
  `output_device_reuse`, and `output_device_bytes` through Python
  normalization, resident per-frame warnings, resident artifacts, and the HTML
  resident summary.
- Keep older native builds and CPU-only installs compatible by preserving the
  public Python wrapper shape and defaulting missing diagnostic fields.
- Validate with direct descriptor batch/single fit equivalence tests, resident
  triangle-registration smoke tests, ruff, full pytest, and the 200-light
  benchmark because this changes native registration memory scheduling.

### S2-Gate 51: Resident Grid Catalog Timing Decomposition

- Instrument native `ResidentCalibratedStack.star_grid_top_nms_candidates_batch`
  with per-frame timing for catalog kernel enqueue, GPU synchronization, count
  downloads, compact catalog downloads, and total native catalog time.
- Preserve the existing grid/NMS star catalog algorithm, output ordering,
  candidate coordinates, fluxes, counts, and resident triangle-registration
  behavior.
- Aggregate the native catalog timings into resident registration component
  timings and record the timing model in per-frame warnings,
  `resident_artifacts.json`, and the HTML resident summary.
- Use the 200-light benchmark to decide whether the remaining
  `triangle_moving_catalog_batch` cost is dominated by device scan/sort/NMS
  work or by host/device transfer and synchronization overhead.
- Validate with direct resident CUDA catalog batch/single equivalence tests,
  resident triangle-registration smoke tests, ruff, full pytest, and the
  200-light benchmark because this gate changes registration diagnostics.

### S2-Gate 52: Resident Grid Catalog Bitonic Shared Sort

- Replace the resident grid/NMS catalog path's shared-memory odd-even sort with
  a shared bitonic sort for grid capacities up to 4096 candidates, preserving
  the GLASS candidate ordering rule of flux descending, then y ascending, then
  x ascending.
- Keep local-maximum detection, per-grid-cell candidate budgets, NMS radius,
  compact catalog output, frame accounting, and downstream triangle
  registration behavior within the existing benchmark tolerance family.
- Record the catalog sort mode in CUDA wrapper results, resident per-frame
  warnings, `resident_artifacts.json`, and the HTML resident summary so
  performance changes remain auditable.
- Validate with a CPU-reference non-power-of-two catalog test, resident
  batch/single equivalence tests, resident triangle-registration smoke tests,
  ruff, full pytest, and the 200-light benchmark because this gate changes the
  resident catalog GPU kernel.

### S2-Gate 53: Resident Grid Top-K Strict Flux Precheck

- Reduce per-cell lock contention in the resident grid top-k catalog kernel by
  adding a lock-free strict-flux precheck before the existing locked top-k
  replacement step.
- Track a per-cell filled-slot counter and enable the precheck only after that
  cell has reached `candidates_per_cell`; sparse cells still take the locked
  path so every available slot can be filled.
- Preserve tie handling by sending equal-flux candidates through the existing
  locked comparator, keeping the established flux/y/x ordering semantics and
  saturated-plateau behavior.
- Record the catalog top-k mode in CUDA wrapper results, resident per-frame
  warnings, `resident_artifacts.json`, and the HTML resident summary.
- Validate with CPU-reference and tie-break catalog tests, resident
  batch/single equivalence tests, resident triangle-registration smoke tests,
  ruff, full pytest, and the 200-light benchmark because this gate changes the
  full-frame grid top-k GPU kernel.

### S2-Gate 54: Resident Pixel-Refine Shared Candidate Metric Workspace

- Reuse one native CUDA workspace for the matrix-translation pixel-refine
  candidate inverse, metric partial-stat, and partial-count buffers across the
  resident triangle-registration batch refine instead of allocating and freeing
  those buffers for each moving frame and fine-search pass.
- Preserve the existing candidate grid, NCC/RMS metric kernel, fine-search
  semantics, quality gates, warp behavior, frame accounting, and output pixels.
- Record workspace mode, candidate capacity, workspace bytes, and coarse/fine
  native metric timings through Python normalization, per-frame registration
  warnings, `resident_artifacts.json`, resident timing components, and the HTML
  resident summary.
- Keep older native builds and CPU-only installs compatible by treating missing
  workspace diagnostics as unavailable or zero.
- Validate with resident CUDA batch/single pixel-refine equivalence tests,
  resident triangle-registration smoke tests, ruff, full pytest, and the
  200-light benchmark because this gate changes native registration memory
  scheduling.

### S2-Gate 55: Resident Pixel-Refine Flattened Batch Metric Launch

- Replace the resident triangle-registration batch pixel-refine loop's
  per-frame coarse/fine metric launches with a flattened frame/candidate metric
  launch for the whole moving-frame batch.
- Run the coarse candidate grid for all moving frames in one native CUDA kernel
  synchronization, then build per-frame fine candidate grids from the coarse
  winners and run the fine metric pass in one additional native CUDA kernel
  synchronization.
- Preserve candidate generation, matrix inversion, NCC/RMS formulas,
  fine-search semantics, quality gates, warp behavior, frame accounting, and
  output pixels within the existing benchmark tolerance family.
- Record flattened metric mode, native metric launch count, coarse/fine total
  candidate counts, workspace capacity, workspace bytes, and coarse/fine metric
  timings through Python normalization, per-frame warnings,
  `resident_artifacts.json`, resident timing components, and the HTML resident
  summary.
- Validate with resident CUDA batch/single pixel-refine equivalence tests,
  resident triangle-registration smoke tests, ruff, full pytest, and the
  200-light benchmark because this gate changes native registration scheduling
  and synchronization behavior.

### S2-Gate 56: Resident Registration Determinism Signatures

- Add exact SHA-256 signatures for resident triangle-registration reference
  catalogs, moving catalogs, triangle descriptors, selected descriptor fits,
  and threshold trial lists.
- Record the per-frame signatures in `resident_artifacts.json` and per-frame
  registration warnings so repeated real-data runs can identify whether a
  coverage or accepted-frame swing came from catalog extraction, descriptor
  generation, descriptor fit selection, or later pixel refinement.
- Surface compact combined determinism hashes in the HTML resident CUDA
  summary while keeping detailed per-frame hashes in JSON artifacts.
- Keep this gate diagnostic-only: it must not alter catalog selection,
  descriptor formulas, fit scoring, pixel refinement, warp behavior, accepted
  frame counts, or output pixels.
- Validate with direct signature-helper tests, repeated resident catalog batch
  determinism checks, resident triangle-registration smoke tests, ruff, and
  full pytest. A fresh 200-light benchmark is optional unless the diagnostic
  change alters image artifacts or registration decisions.

### S2-Gate 57: Resident Determinism Audit

- Add a first-class audit command that compares two resident CUDA runs using
  the S2-Gate 56 triangle-registration signatures, resident registration
  results, frame accounting, and timing artifacts.
- Report artifact-level combined-hash drift, per-frame catalog/descriptor/fit
  hash drift, registration status/matrix drift, frame-accounting drift, and
  candidate/baseline timing ratio in machine-readable JSON and compact
  Markdown.
- Use this audit on repeated 200-light resident runs to decide whether the
  observed Gate55 acceptance swing is catalog extraction, descriptor
  generation, fit selection, pixel refinement, or later accounting.
- If repeated 200-light signatures differ at the catalog level, follow with a
  strict deterministic resident catalog mode or deterministic candidate
  compaction gate before accepting more registration scheduling changes.
- Keep this gate diagnostic-only unless the audit proves a specific
  nondeterministic stage that must be fixed immediately.

### S2-Gate 58: Deterministic Resident Grid Top-K Catalog Mode

- Add an opt-in deterministic resident grid top-k catalog path for
  `similarity_cuda_triangle` so repeated full-frame resident runs can produce
  identical reference and moving catalog signatures.
- Use a serial per-cell CUDA candidate scan for the deterministic mode,
  preserving the existing flux/y/x tie-break semantics while avoiding atomic
  lock scheduling drift in saturated grid cells.
- Wire deterministic single-frame and batch catalog wrappers through the
  native binding, `glass_cuda.py`, resident CUDA run/audit CLI flags,
  `resident_artifacts.json`, registration warnings, and smoke tests.
- Keep the default fast lock-based catalog path available for throughput
  comparisons; the deterministic path is selected only with
  `--resident-star-catalog-deterministic`.
- Treat matching non-finite registration diagnostics such as `NaN` RMS on
  failed or excluded frames as equal in the determinism audit so the audit
  reports scientific/result drift rather than sentinel-value artifacts.
- Validate with focused CUDA resident stack tests, CLI smoke tests, the
  resident determinism unit tests, ruff, full pytest, and a repeated 200-light
  resident CUDA determinism audit.

### S2-Gate 59: Resident Output Pixel Determinism Audit

- Extend `glass resident-determinism` so repeated resident CUDA runs compare
  final output FITS image data, not only catalog/registration/accounting
  metadata.
- Hash the data payload for resident master outputs and available maps
  (`weight`, `coverage`, low/high rejection, and DQ) using a canonical
  contiguous numeric representation with shape, dtype, finite-pixel count, and
  compact summary statistics in the audit evidence.
- Treat missing output artifacts as explicit audit differences unless both
  runs omit the same optional map.
- Keep the audit read-only: never rewrite output FITS files or input image
  directories.
- Validate with synthetic FITS audit fixtures, CLI smoke coverage, ruff, full
  pytest, and the repeated 200-light resident CUDA runs produced by S2-Gate 58.

### S2-Gate 60: Parallel Deterministic Resident Grid Top-K

- Replace the deterministic resident grid top-k catalog scan's one-thread-per
  cell fallback with a one-block-per-cell deterministic parallel scan for the
  standard small `candidates_per_cell` cases.
- Preserve the GLASS catalog comparator exactly: flux descending, then y
  ascending, then x ascending. The parallel path may change scheduling, but not
  catalog contents relative to the deterministic single-frame/batch contract.
- Keep a serial deterministic fallback for unusually large per-cell candidate
  budgets where shared-memory usage would be excessive.
- Surface the top-k mode as `deterministic_parallel_per_cell` so real-data
  artifacts distinguish the optimized deterministic path from the Gate58
  serial path.
- Validate with resident CUDA catalog batch/single/repeat tests, resident
  triangle-registration smoke tests, ruff, full pytest, and repeated 200-light
  resident determinism plus output-pixel audits.

### S2-Gate 61: Resident Descriptor Fit Timing Ledger

- Add native timing fields to the resident triangle descriptor batch-fit path so
  the current descriptor-fit cost is split into host preparation, reference
  allocation/upload, reusable workspace allocation, moving-frame uploads, kernel
  synchronization, output downloads, and total per-frame native fit time.
- Surface the timing ledger in `resident_artifacts.json`, fine timing component
  totals, and per-frame registration warnings without changing catalog
  contents, fit decisions, matrices, pixel refinement, warp behavior, or output
  pixels.
- Use the ledger to choose whether the next optimization gate should attack
  candidate scoring kernels, host/device transfers, descriptor generation, or
  batch orchestration.
- Validate with native descriptor batch tests, resident CUDA smoke tests, ruff,
  full pytest, and a repeated 200-light resident determinism plus output-pixel
  audit.

### S2-Gate 62: Parallel Descriptor Fit Best Reduction

- Replace the descriptor similarity fit's single-thread best-candidate scan
  with a deterministic single-block parallel reduction.
- Preserve the existing selection contract exactly: higher inlier count wins,
  lower RMS breaks ties, and the earliest candidate index breaks exact RMS ties.
- Surface the reduction mode as `single_block_parallel_score_rms_index` in
  native results, resident artifacts, and registration warnings.
- Validate that native batch and single descriptor fits still match, resident
  triangle registration still aligns synthetic shifted pairs, and repeated
  200-light resident CUDA runs pass artifact, registration, frame-accounting,
  and output-pixel determinism audits.

### S2-Gate 63: Pixel-Refine Workload Ledger

- Add a resident CUDA pixel-refine workload ledger for the batched
  coarse/fine metric passes without changing registration decisions, matrices,
  warp behavior, accepted frames, or output pixels.
- Record the workload model, sampled pixels per candidate, total candidate
  sample evaluations, native coarse/fine timings, and effective metric
  throughput for both coarse and fine passes.
- Surface the ledger in native batch-refine results, per-frame registration
  warnings, `resident_artifacts.json`, and fine timing diagnostics so the next
  optimization gate can target measured pixel-refine work rather than only the
  aggregate registration/warp wall time.
- Validate with native resident stack batch/single refine tests, resident
  triangle-registration smoke tests, ruff, full pytest, and a repeated
  200-light resident determinism plus output-pixel audit because this gate is
  diagnostic-only and must not change image pixels.

### S2-Gate 64: Explicit Fast-Coarse Pixel Refinement

- Add an explicit resident CUDA triangle pixel-refine fast-coarse mode that
  raises the coarse metric sample stride to at least the final metric sample
  stride.
- Keep the default path unchanged. The fast mode must be opt-in through CLI or
  registration policy because it changes the pixel-refine sampling grid and can
  change subpixel matrices and output pixels.
- Surface requested/effective strides, whether the coarse stride was adjusted,
  fast-coarse mode, workload counts, timing, and throughput in
  `resident_artifacts.json` and per-frame registration warnings.
- Validate the mode with focused resident CUDA smoke tests, ruff, full pytest,
  repeated 200-light runs in fast-coarse mode, strict A/B determinism for those
  runs, and a numerical drift note against the conservative Gate63 baseline.

### S2-Gate 65: Resident Output Numerical Drift Audit

- Extend `glass resident-determinism` so output FITS hash mismatches include
  numerical drift metrics, not only exact-match failure.
- For each mismatched output/map with compatible shapes, report joint finite
  pixel count, non-finite mismatch count, signed mean, mean/median absolute
  difference, RMS, p95/p99/max absolute difference, baseline/candidate
  mean/std, and RMS relative to baseline standard deviation.
- Keep the strict audit semantics unchanged: hash or registration mismatches
  still fail `--fail-on-mismatch`; the drift metrics explain magnitude and
  support fast-mode quality review.
- Validate with synthetic FITS audit fixtures, CLI Markdown output, ruff, full
  pytest, and the Gate63-conservative vs Gate64-fast 200-light comparison.

### S2-Gate 66: HTML Numerical Drift Reporting

- Surface resident output numerical drift evidence in the main HTML report when
  the report is given an acceptance/resident-determinism audit JSON containing
  `output_numerical_drifts`.
- Add a dedicated report section with artifact key, output field, finite-pixel
  accounting, mean/median/RMS/percentile/max absolute differences, and RMS
  relative to baseline standard deviation.
- Keep the report read-only and do not alter strict audit pass/fail semantics;
  this gate only makes the S2-Gate 65 evidence visible to users reviewing fast
  presets or regressions.
- Validate with CLI report smoke tests, ruff, full pytest, and a real
  Gate63-vs-Gate64 audit JSON rendered through `glass report`.

### S2-Gate 67: Acceptance Audit Resident Drift Attachment

- Add an optional `glass acceptance-audit --resident-determinism-json` input so
  benchmark acceptance artifacts can carry S2-Gate 65 strict resident
  determinism status and output numerical drift rows.
- Preserve acceptance pass/fail semantics: resident drift evidence is attached
  for review/reporting and does not by itself change benchmark acceptance
  checks unless a later contract explicitly requires thresholds.
- Copy the resident determinism source path, strict status, summary, timing,
  output drift count, max relative RMS drift, and drift rows into the
  acceptance JSON/Markdown artifact.
- Validate with acceptance-audit CLI tests, HTML report smoke coverage, ruff,
  full pytest, and a real Gate63-vs-Gate64 drift audit attached to an
  acceptance-style report.

### S2-Gate 68: Resident Drift Contract Thresholds

- Add optional benchmark-contract thresholds under `resident_determinism` so
  output numerical drift can become a hard acceptance check when desired.
- Keep defaults unchanged: no drift checks run unless a contract explicitly
  declares the `resident_determinism` section.
- Supported checks:
  - resident determinism artifact presence;
  - optional strict resident determinism pass requirement;
  - maximum output numerical drift row count;
  - maximum relative output RMS drift;
  - maximum absolute RMS drift;
  - maximum mean absolute drift.
- Add a real M38 200-light resident drift contract fixture and validate it
  against the Gate65 resident drift artifact plus the established 200-light
  WBPP/GLASS comparison.

### S2-Gate 69: Native Batch Matrix Warp Dispatch

- Add resident CUDA native batch dispatch for matrix bilinear and Lanczos3 warp
  application after triangle pixel refinement.
- Keep the existing per-frame warp path as a fallback for translation-only
  matrices, old native extensions, and unsupported interpolation modes.
- Record batch warp frame count, fallback count, timing model, inverse upload,
  kernel enqueue, device copy enqueue, sync, and native total timing in
  `resident_artifacts.json` plus per-frame registration warnings.
- Validate with resident CUDA triangle-registration smoke tests, ruff, full
  pytest, and the 200-light benchmark contract because this gate changes native
  registration scheduling and synchronization behavior.

### S2-Gate 70: Reused Resident Calibration Events

- Remove per-frame CUDA event create/destroy overhead from resident H2D +
  calibration timing by allocating reusable stack-lifetime calibration events.
- Preserve the existing pageable, pinned async, and pinned-ring behavior and
  event-based H2D/kernel timing semantics.
- Record the calibration event mode in `resident_io_pipeline` so 200-light
  profiles can distinguish reused stack events from legacy per-frame event
  allocation.
- Validate with native CUDA resident-stack tests, resident CLI smoke coverage,
  ruff, full pytest, and a 200-light pinned-ring benchmark comparison.

### S2-Gate 71: Opt-In Resident Calibration Batch Enqueue

- Add an explicit resident calibration batch size that can enqueue multiple
  pinned-ring raw-light H2D copies and calibration kernels from native code
  before synchronizing.
- Keep default behavior at one frame per sync until the batch path has enough
  200-light evidence for default routing.
- Enable the batch path only for resident modes that do not need the CPU light
  array for online registration during load; keep translation-preview on the
  legacy per-frame path.
- Record batch enablement, batch count, frame count, timing model, stream
  elapsed time, sync time, and native wall time in `resident_io_pipeline`.
- Validate with resident stack CUDA tests, resident CLI smoke coverage, ruff,
  full pytest, and 200-light pinned-ring benchmark comparison.

### S2-Gate 72: Multi-Stream Resident Calibration Batch

- Add an explicit resident calibration stream count for native batch
  calibration.
- Allocate reusable raw-light device buffers, CUDA streams, and timing events
  per calibration lane.
- Preserve default single-stream behavior unless the user opts into multiple
  streams.
- Keep output identity checks strict against the prior resident calibration
  path.
- Record requested stream count, actual stream count, lane buffer bytes,
  multistream support, multistream enablement, and timing model in
  `resident_io_pipeline`.
- Validate with resident stack CUDA tests, resident CLI smoke coverage, ruff,
  full pytest, and 200-light benchmark comparison.

### S2-Gate 73: Resident Calibration Wave Scheduler

- Add an optional resident calibration wave size that can split a larger
  requested batch into smaller native waves.
- Release pinned prefetch slots after each wave synchronization so the reader
  can refill the ring more frequently.
- Preserve the default no-wave behavior unless the user opts in.
- Record requested wave size, effective wave size, release mode, prefetch slot
  release count, prefetch no-slot blocked count, and maximum in-flight pinned
  slots in `resident_io_pipeline`.
- Validate with resident CLI coverage, ruff, full pytest, and 200-light
  benchmark comparison against the previous resident baseline.

### S2-Gate 74: Resident H2D Completion Release

- Add an opt-in resident calibration release mode that returns pinned host
  prefetch slots after native H2D completion events instead of waiting for the
  calibration kernel/store path to finish.
- Restrict the first implementation to one frame per native calibration lane
  so each host buffer is released only after the lane-specific copy-complete
  event has synchronized.
- Keep the default synchronized release path unchanged until real 200-light
  evidence shows the H2D-event path is worth promoting.
- Record requested release mode, support, enablement, release count,
  H2D-release timing, H2D event timing, and pending-calibration wait timing in
  `resident_io_pipeline`.
- Validate with native resident-stack tests, resident CLI smoke coverage, ruff,
  full pytest, and 200-light benchmark comparison against the previous
  resident event-reuse baseline.

### S2-Gate 75: Resident Calibration Release Auto Policy

- Add an opt-in `auto` resident calibration release mode that chooses
  `h2d_event` only when the effective wave size fills the available native
  calibration stream lanes.
- Keep explicit `sync` and `h2d_event` requests available for controlled
  benchmark experiments.
- Record requested release mode, effective release mode, capability,
  recommendation, policy rule, and reason in `resident_io_pipeline` so tuning
  runs cannot confuse an underfilled-lane experiment with the recommended fast
  path.
- Validate the policy with resident CLI coverage, ruff, full pytest, and a
  200-light benchmark comparison that checks output identity against the prior
  GLASS resident baseline.

### S2-Gate 76: Native Callback Release Calibration Queue

- Add an explicit `callback_queue` resident calibration release mode that
  sends a larger Python batch to native code while native code internally
  schedules smaller H2D waves.
- After each native wave's H2D completion events synchronize, call back into
  Python to release only the host prefetch slots whose copies are complete,
  then continue enqueueing later waves before one final calibration sync.
- Keep host buffer lifetime safe: a slot is released only after the matching
  native H2D event has completed.
- Record callback queue support, capability, enablement, callback release
  count, callback release time, internal wave count, fetch batch size, and
  timing model in `resident_io_pipeline`.
- Validate with native resident-stack callback tests, resident CLI coverage,
  ruff, full pytest, and a 200-light benchmark comparison against the prior
  resident baseline.

### S2-Gate 77: Batched Prefetch Slot Release

- Replace repeated per-index pinned prefetch slot release calls with a batched
  release path that returns all completed slots first and triggers at most one
  `_fill()` call per release batch.
- Preserve the existing `release(index)` API by routing it through
  `release_many([index])`.
- Record prefetch fill call count, submitted frame count, release batch count,
  and release/fill model in `resident_io_pipeline`.
- Use the batched release path for synchronized batch calibration, H2D-event
  release, and callback-queue release.
- Validate with resident CLI coverage, ruff, full pytest, and 200-light
  benchmark comparison against the previous callback-queue run.

### S2-Gate 78: Resident Prefetch Parameter Sweep

- Add a reusable benchmark harness for resident CUDA prefetch tuning so
  prefetch depth, prefetch workers, native batch size, stream count, wave size,
  and release mode can be swept from a single auditable command.
- The harness must support `--dry-run`, reuse of existing variant directories,
  JSON and Markdown summaries, and optional per-variant compare reports against
  a reference master.
- Parse `run_timing.json`, `resident_artifacts.json`, and
  `frame_accounting.json` into a compact ranking table with total runtime,
  read-wait time, native calibration time, callback waves, blocked prefetch
  slots, release batches, active frames, and zero-weight frames.
- Do not change resident image math or defaults in this gate; the output is
  benchmark evidence for later policy/default decisions.
- Validate with benchmark dry-run tests, ruff, full pytest, and a focused
  200-light sweep around the current Gate70B/Gate73/Gate77 parameter family.

### S2-Gate 79: Queued Resident Prefetch Refill

- Add an explicit resident pinned-ring prefetch refill mode so callback-time
  H2D slot release can be decoupled from immediate `_fill()` submission.
- Keep the default `immediate` refill behavior unchanged; add `queued` for a
  lightweight single-thread refill queue and `deferred` as a diagnostic mode.
- Preserve host-buffer lifetime safety: a slot can still be recycled only after
  the matching H2D completion release path says it is safe.
- Record requested refill mode, refill request count, queued submit/execute
  counts, coalesced refill requests, wait time, and release/fill model in
  `resident_io_pipeline`.
- Validate with resident CLI coverage, benchmark dry-run coverage, ruff, full
  pytest, and a 200-light comparison against the Gate70B/Gate78 resident
  baseline.

### S2-Gate 80: Batched Resident Warp Matrix Upload

- Replace per-frame host-to-device inverse-matrix uploads in native resident
  matrix bilinear and Lanczos3 batch warp with one batch inverse preparation
  and one device upload per batch.
- Keep the same warp kernels, interpolation formulas, coverage accounting, DQ
  semantics, accepted-frame contract, and output pixels.
- Record inverse upload mode, inverse preparation time, inverse-batch
  allocation time, inverse-batch bytes, upload time, kernel enqueue time, copy
  enqueue time, sync time, and native total time in native timing results and
  resident artifacts.
- Validate with direct resident CUDA warp-vs-CPU tests, resident CUDA artifact
  coverage, ruff, full pytest, and a 200-light benchmark comparison against
  the Gate70B/Gate78 resident baseline.

### S2-Gate 81: Chunked Multi-Frame Resident Matrix Warp

- Replace native resident matrix bilinear and Lanczos3 batch warp's per-frame
  warp-kernel plus device-copy loop with chunked multi-frame warp kernels,
  chunked coverage reduction, and chunked scatter back into the resident stack.
- Keep in-place safety by writing warped pixels into a temporary chunk
  workspace before scattering them back to their source frame slots.
- Keep interpolation formulas, matrix inversion semantics, coverage/DQ
  accounting, accepted-frame contract, and output pixels unchanged.
- Record chunk size, chunk count, workspace bytes, output/coverage bytes,
  index upload, inverse upload, warp-kernel launches, coverage-reduce launches,
  scatter launches, sync time, and native total timing in native results and
  resident artifacts.
- Validate with direct resident CUDA warp-vs-CPU tests, resident CUDA artifact
  coverage, ruff, full pytest, and a 200-light benchmark comparison against
  Gate70B/Gate78/Gate80.

### S2-Gate 82: Fused Resident Matrix-Warp Mean Primitive

- Add a native resident CUDA primitive that computes weighted mean integration
  directly from unwarped resident frames plus one registration matrix per
  frame, without scattering warped full-frame images back into the resident
  stack.
- Support bilinear and Lanczos3 sampling with the same matrix inversion,
  footprint rules, and Lanczos clamping semantics used by the existing warp
  kernels.
- Emit master, weight, finite-sample coverage, geometric footprint coverage,
  and timing diagnostics that state the path avoids stack scatter and does not
  modify the resident stack.
- Keep the primitive opt-in and non-default until rejection, LN, DQ, and
  pipeline routing are fused or bridged explicitly.
- Validate with direct resident CUDA tests comparing the fused primitive
  against existing warp-then-integrate behavior, plus native build, ruff, and
  full pytest.

### S2-Gate 83: Fused Resident Matrix-Warp Rejection Primitive

- Extend the Gate82 fused resident matrix-warp primitive to support sigma and
  winsorized-sigma rejection without scattering warped full-frame images back
  into the resident stack.
- Support bilinear and Lanczos3 sampling with the same matrix inversion,
  footprint rules, and Lanczos clamping semantics used by GLASS warp kernels.
- Emit master, weight map, finite-sample coverage, low/high rejection maps,
  geometric footprint coverage, and timing diagnostics that state the path
  avoids stack scatter and does not modify the resident stack.
- Keep the primitive opt-in and non-default until LN, DQ map construction,
  report artifacts, and pipeline routing are explicitly bridged.
- Validate with direct resident CUDA tests comparing fused sigma and fused
  winsorized-sigma output against existing warp-then-integrate behavior, plus
  native build, ruff, and full pytest.

### S2-Gate 84: Opt-In Fused Resident Matrix Integration Route

- Add a CLI/engine dispatch switch that can route resident integration through
  the Gate82/Gate83 fused matrix-warp primitives without first writing warped
  full-frame intermediates back into the resident stack.
- Keep the first route deliberately narrow: `registration=off` uses identity
  matrices, and `registration=external_matrix` consumes an existing
  `registration_results.json` artifact while deferring matrix application to
  the integration kernel.
- Require local normalization to be off for the first fused route, because
  resident LN currently mutates already-registered stack frames.
- Emit resident artifacts that state whether fused dispatch was used, how many
  frames were deferred, native fused timing, interpolation/clamping policy, and
  geometric coverage provenance.
- Validate with a CLI-level CUDA test comparing external-matrix stack dispatch
  against fused-matrix dispatch, plus native build, ruff, full pytest, and a
  200-light external-registration A/B run when local benchmark artifacts are
  available.

### S2-Gate 85: Fused Minimal Diagnostic Download Mode

- Reduce fused resident matrix integration output traffic when
  `--resident-output-maps minimal` is selected by downloading only the master
  and weight maps from the native fused primitive.
- Keep `audit` and `science` modes on full diagnostic downloads so coverage,
  rejection, DQ, and geometric footprint provenance remain complete when those
  modes are requested.
- Support the same download policy for fused matrix-warp weighted mean and
  fused matrix-warp sigma/winsorized-sigma rejection.
- Record native `download_mode`, `diagnostic_maps_downloaded`, and reduced
  output byte counts in fused timing and resident artifacts.
- Validate that minimal fused dispatch matches the stack route numerically,
  does not write or report unavailable diagnostic maps, and reduces 200-light
  fused output traffic without changing the master.

### S2-Gate 86: Triangle Registration Fused Matrix Dispatch

- Extend the opt-in `--resident-integration-dispatch fused_matrix` route from
  identity/external matrices to resident `similarity_cuda_triangle`.
- Keep triangle catalog, descriptor fit, pixel refinement, quality gates, and
  frame zero-weight decisions unchanged; only defer the accepted matrix
  application from the registration stage into the fused integration kernel.
- In fused dispatch, avoid writing accepted triangle-registered full-frame
  intermediates back into the resident stack. The resident stack keeps
  calibrated frames; integration samples each frame through its accepted
  triangle matrix.
- Record explicit artifacts and per-frame warnings for
  `triangle_warp_batch_mode=fused_matrix_deferred`,
  `triangle_warp_batch_timing_model=fused_integration_deferred`, and
  `triangle_fused_matrix_deferred_count`.
- Validate with a CLI-level CUDA A/B test comparing triangle stack dispatch
  against triangle fused dispatch on the same synthetic shifted pair, plus
  native build, ruff, full pytest, and a 200-light triangle fused benchmark.

### S2-Gate 87: Resident Integration Auto Dispatch Policy

- Add `--resident-integration-dispatch auto` for resident CUDA runs and audits.
- Use current measured evidence to select only verified fast fused routes:
  bilinear matrix registration with local normalization off can automatically
  use fused matrix integration.
- Keep conservative stack routing for routes that are not yet verified as fast
  and numerically identical, especially non-bilinear/Lanczos3 rejection paths
  where Gate86 showed fused multi-pass sampling can be slower.
- Record requested mode, effective mode, selection reason, and auto-policy
  flags in resident artifacts and integration outputs.
- Validate with focused CUDA CLI tests for both branches: bilinear triangle
  auto selects fused dispatch, while Lanczos3+winsorized triangle auto remains
  on stack dispatch.
- Re-run the 200-light tuned bilinear triangle benchmark with auto dispatch and
  compare it against the Gate86 explicit fused bilinear result.

### S2-Gate 88: StackEngine Default Contract Audit

- Add a standalone `stack-engine-contract` audit command that verifies master
  calibration artifacts and tile/CPU integration outputs use StackEngine by
  default.
- Require StackEngine DQ provenance and normalized `dq_provenance_summary`
  records for the audited StackEngine surfaces.
- Keep resident CUDA integration explicit: the audit can be pointed at resident
  runs with `--expected-integration-engine cuda_resident_stack`, but the default
  contract checks the tile/CPU StackEngine route.
- Emit JSON and optional Markdown artifacts so future refactors can fail fast on
  fallback routing, missing DQ provenance, or legacy accumulators.
- Validate with a synthetic CPU audit run, a failing legacy fixture, ruff, and
  full pytest. A 200-light benchmark rerun is not required because this gate is
  diagnostic-only and does not change image math or resident CUDA routing.

### S2-Gate 89: StackEngine Contract Reporting

- Let `glass report` auto-discover `*stack_engine_contract*.json` or consume an
  explicit `--stack-engine-contract` audit artifact.
- Surface StackEngine contract status, expected integration engine, artifact
  source path, failed checks, and audited calibration/integration surfaces in
  the main HTML report.
- Keep the standalone contract JSON authoritative; the report is a readable
  triage layer for default-route and DQ-provenance failures.
- Validate with report fixture tests, ruff, full pytest, and report
  regeneration against the latest preserved 200-light resident artifact using
  the Gate88 contract JSON.
- No new 200-light benchmark is required because this gate is report-only and
  does not alter image math or resident CUDA routing.

### S2-Gate 90: Pipeline Invariant Contract Audit

- Add a standalone `pipeline-contract` audit command for structural invariants
  that should hold across warp, local normalization, and integration artifacts.
- Check integration output map paths, rejection-map policy, DQ map summaries,
  and normalized DQ provenance summaries without loading full science images.
- Check local-normalization crop-box recording, coefficient-grid artifacts,
  DQ summaries, and normalized/coverage output paths when LN artifacts exist.
- Check warp registered outputs, coverage maps, DQ maps, DQ summaries, and
  explained skipped-frame records when warp artifacts exist.
- Emit JSON and optional Markdown so missing maps, silent crop changes, and
  missing DQ/LN records fail in a machine-readable way.
- Validate with a passing synthetic CPU audit run, a failing fixture, ruff, full
  pytest, and a contract audit against the latest preserved 200-light resident
  artifact. A new 200-light benchmark is not required because this gate is
  artifact-contract only and does not change image math or resident CUDA
  routing.

### S2-Gate 91: Pipeline Contract Reporting

- Let `glass report` auto-discover `*pipeline_contract*.json` or consume an
  explicit `--pipeline-contract` audit artifact.
- Surface pipeline contract status, artifact source path, failed checks,
  integration map rows, local-normalization rows, and warp rows in the main HTML
  report.
- Keep the standalone pipeline contract JSON authoritative; the report should be
  a readable triage layer for missing maps, DQ/LN records, crop-box omissions,
  and unexplained skipped frames.
- Validate with report fixture tests, ruff, full pytest, and report
  regeneration against the latest preserved 200-light resident artifact using
  the Gate90 contract JSON.
- No new 200-light benchmark is required because this gate is report-only and
  does not alter image math or resident CUDA routing.

### S2-Gate 92: Pipeline Contract Pixel Verification

- Add an explicit `pipeline-contract --pixel-verify` mode that reads integration
  DQ, coverage, and rejection count maps in FITS tiles, not as full in-memory
  images.
- Compare DQ map pixel counts against integration `dq_summary` values with an
  explicit pixel tolerance, treating absent zero-count flags as zero.
- Compare coverage zero-or-less pixels against DQ `no_data` counts, and
  rejection-map positive pixels against DQ `low_rejected` and `high_rejected`
  counts when those maps are written or required by policy.
- Surface the pixel-verification rows in the main HTML report while keeping
  `pipeline_contract.json` authoritative for automated checks.
- Validate with passing and failing synthetic/FITS fixtures, ruff, full pytest,
  and a pixel-verification audit against preserved 200-light artifacts when the
  required map files are locally available.
- No new 200-light benchmark is required because this gate reads existing
  artifacts and does not alter image math or resident CUDA routing.

### S2-Gate 93: Pipeline Pixel Delta Reporting

- Expand the HTML pipeline-contract section so optional pixel-verification
  evidence includes per-map and per-flag `actual`, `summary`, `delta`, and
  pass/fail rows.
- Cover DQ bit counts, coverage `no_data` matching, and low/high rejection-map
  positive-pixel matching when the fields are present in `pipeline_contract`.
- Keep `pipeline_contract.json` authoritative. The report is only a review layer
  for quickly locating the mismatched map or DQ flag.
- Validate with report fixture tests, ruff, full pytest, and report
  regeneration against the Gate92 real artifact JSON.
- No new 200-light benchmark is required because this gate is report-only and
  does not alter image math or resident CUDA routing.

### S2-Gate 94: Run Guardrail Bundle

- Add a `glass guardrails` command that creates a run-local review bundle from
  existing artifacts without modifying the original run directory or input
  image directories.
- The bundle must generate StackEngine contract JSON/Markdown, Pipeline
  contract JSON/Markdown, optional tiled pixel verification, a compact
  `guardrails_summary.json`, and an HTML report wired to those contract files.
- Support CPU/tile and resident CUDA runs by allowing the expected integration
  engine to be `stack_engine_cpu`, `cuda_resident_stack`, or `any`.
- Return a failing exit code when either contract fails, so future optimization
  scripts can use this as a regression guard.
- Validate with a synthetic CPU audit run, CLI help tests, ruff, full pytest,
  and a guardrail bundle over preserved 200-light audit-map artifacts.
- No new 200-light benchmark is required because this gate only orchestrates
  existing artifact audits and report generation.

### S2-Gate 95: Guarded Resident Sweep

- Extend the resident CUDA sweep harness so each executed variant can optionally
  run `glass guardrails` after the variant completes.
- Record guardrail command lines in dry-run plans, and record guardrail
  pass/fail status, summary path, report path, and failed contract names in the
  sweep summary for completed variants.
- Rank guardrail-failed variants behind guardrail-passed variants so the
  "best" sweep result cannot silently prefer a faster but contract-broken run.
- Preserve existing sweep behavior when guardrails are not requested.
- Validate with dry-run sweep tests, direct ranking tests, ruff, full pytest,
  and a dry-run command matrix suitable for the 200-light resident benchmark.
- No new 200-light benchmark is required because this gate changes benchmark
  orchestration and reporting, not resident CUDA kernels or image math.

### S2-Gate 96: Resident Sweep Runtime Guard

- Add per-variant and per-guardrail timeout controls to the resident CUDA sweep
  harness so a single pathological parameter set cannot monopolize the GPU.
- Record run timeout/failure status, timeout seconds, exit code, error text, and
  skipped guardrail status in `resident_prefetch_sweep_summary.json` instead of
  crashing the whole sweep.
- Keep timed-out, failed, and guardrail-failed variants out of the `best_variant`
  slot while preserving completed green variants for ranking.
- Preserve default behavior when no timeout is supplied.
- Validate with a controlled timeout sweep test, dry-run sweep tests, direct
  ranking tests, ruff, full pytest, native CUDA build, and `glass doctor`.
- The attempted 200-light guarded sweep that motivated this gate was stopped
  before completion after one variant ran far longer than the current baseline;
  no performance result from that interrupted run is accepted as green.

### S2-Gate 97: Resident Sweep Baseline Command Import

- Add a `--common-run-args-from-command` option to the resident sweep harness so
  a known-good `run_command.txt` can seed shared science and tuning arguments.
- Filter out sweep-managed arguments from the imported command: plan, output
  directory, backend, stage, memory mode, prefetch, H2D, batch, stream, wave,
  and release-mode knobs.
- Preserve imported science and benchmark-stability arguments such as shared
  resident master cache, reference frame, registration model, interpolation,
  star-catalog thresholds, flat floor, output-map policy, and excluded frame
  ids.
- Validate with dry-run import tests that prove the sweep owns only the swept
  parameters while carrying forward the proven 200-light run settings.
- Run a bounded 200-light guarded single-variant sweep imported from the latest
  proven audit-map command, with timeout guards and pixel-verifying guardrails.
- Compare the imported-run master against the external reference output and
  record runtime, frame counts, guardrail status, and image agreement.

### S2-Gate 98: Resident Sweep Provenance And Mini Matrix

- Record common-run-argument provenance in resident sweep JSON and Markdown
  summaries, including source type, imported command path, source argument
  count, imported/inline/repeated argument counts, total argument count, and
  filtered sweep-managed options.
- Validate provenance in dry-run tests so imported benchmark matrices are
  auditable without manually reconstructing long command lines.
- Run a small imported 200-light sweep matrix over prefetch depth and refill
  mode with timeout guards and per-variant guardrails.
- Require all completed variants to preserve 200 input lights, 193 active
  frames, 7 zero-weight frames, and passing guardrails before considering them
  rankable.
- Compare the best variant against the external reference master and record
  runtime, speedup, shape match, coverage-masked RMS, and p99 absolute
  difference.
- Use the result to decide whether queued refill is worth carrying forward into
  the next resident registration/warp optimization sweep.

### S2-Gate 99: Resident Registration Component Sweep Reporting

- Promote resident registration/warp component timings from
  `resident_artifacts.json` into resident sweep JSON and Markdown summaries.
- Include at least total resident registration/warp time, moving star-catalog
  extraction, descriptor fit, moving descriptor generation, pixel refinement,
  total warp, and native batch-warp timings when present.
- Keep older runs reportable when component timings are absent.
- Validate with synthetic summary fixtures and reuse the latest 200-light mini
  matrix to regenerate a component-visible sweep summary without rerunning the
  GPU stack.
- Use the resulting component table to choose the next real optimization target
  from evidence rather than from the aggregate stage total alone.

### S2-Gate 100: Resident Registration Parameter Sweep

- Extend the resident sweep harness beyond I/O tuning so it can sweep selected
  registration parameters from the same audited command matrix.
- Add variant dimensions for triangle pixel-refinement fast-coarse mode,
  coarse stride, final stride, and star max candidates.
- Encode registration-tuning dimensions in the variant id and generated command
  line so each run is reproducible.
- Preserve existing default sweep behavior when registration dimensions are not
  provided.
- Validate with dry-run tests and run a small 200-light guarded comparison of
  baseline pixel refinement versus fast-coarse pixel refinement.
- Compare the best fast-coarse candidate against the external reference and the
  baseline-refine GLASS output, and keep it as a candidate rather than a new
  default unless both performance and numerical agreement are convincingly
  stable.

### S2-Gate 101: Resident Sweep Compare Contract

- Attach per-variant reference-comparison metrics directly to resident sweep
  summaries when `--reference-master` is supplied.
- Forward compare normalization controls through the sweep harness: candidate
  scale, offset, clip limits, candidate coverage map, and minimum coverage.
- Record compare JSON/HTML paths, shape match, RMS difference, relative RMS,
  p99 absolute difference, compared-pixel counts, coverage fraction, and
  speedup versus the reference in `resident_prefetch_sweep_summary.json`.
- Surface the key compare metrics in the Markdown sweep table so faster variants
  can be reviewed alongside image agreement without manual follow-up commands.
- Validate with unit tests and regenerate the Gate 100 two-variant 200-light
  sweep summary from existing runs using per-candidate coverage maps.
- Treat a fast variant as a candidate only when guardrails and comparison
  metrics are both acceptable for the intended benchmark contract.

### S2-Gate 102: Compare-Gated Resident Sweep Ranking

- Add optional compare-gate thresholds to resident sweep summaries so rankable
  variants must satisfy image-agreement constraints before speed decides the
  best result.
- Support shape-match requirement, maximum RMS difference, maximum relative RMS
  difference, and maximum p99 absolute difference.
- Record per-variant compare-gate pass/fail status and reasons in the sweep JSON
  and Markdown table.
- Include a top-level compare-gate summary with policy, passed count, failed
  count, and planned count.
- Keep default behavior unchanged when compare-gate thresholds are not supplied.
- Validate with unit tests and a reused 200-light sweep in which the faster
  fast-coarse candidate is intentionally demoted because its reference RMS/p99
  exceed the selected benchmark contract.

### S2-Gate 103: Resident Triangle Catalog Sweep Knobs

- Promote resident triangle catalog tuning parameters from plan-only policy
  values to explicit resident CLI overrides:
  - grid top candidates retained per cell
  - non-grid NMS scan candidate count
  - NMS minimum separation in pixels
- Add these catalog dimensions to the resident sweep harness and encode them in
  variant ids and generated command lines.
- Record the effective catalog parameters in resident registration artifacts and
  per-frame registration warnings.
- Preserve imported command behavior by appending sweep-owned overrides after
  imported science arguments.
- Validate with focused tests and a two-variant 200-light sweep over
  `triangle_grid_top_per_cell=2,4` using guardrails and compare-gated ranking.
- Use the result to decide whether lower per-cell catalog capacity is a viable
  next optimization candidate for moving-catalog time.

### S2-Gate 104: Resident Sweep Analysis Artifact

- Emit a machine-readable `resident_prefetch_sweep_analysis.json` and companion
  Markdown summary for every resident sweep.
- Identify completed variants, promotion candidates, fastest variant, lowest
  moving-catalog variant, lowest registration/warp variant, and fastest variant
  satisfying all enabled guardrail and compare gates.
- Record recommendation status and reasons, especially when a faster catalog
  candidate is blocked by compare-gated image agreement.
- Preserve the existing sweep summary schema while adding the analysis artifact
  beside it.
- Validate with focused tests and generate analysis for the 200-light
  S2-Gate 103 catalog sweep without rerunning CUDA.

### S2-Gate 105: Resident Sweep Frame-Accounting Gate

- Add an optional frame-accounting promotion gate to resident sweeps so a fast
  variant cannot become `best_variant` when it changes the expected input,
  integrated, or zero-weight light frame counts.
- Support exact expected counts for input light frames, active/integrated light
  frames, and zero-weight frames, plus a minimum active-frame floor.
- Record per-variant frame-gate pass/fail status and reasons in sweep JSON,
  Markdown, and analysis artifacts.
- Include top-level frame-gate policy and passed/failed/planned counts.
- Keep default behavior unchanged when frame-gate requirements are omitted.
- Validate with unit tests and regenerate a frame-gated 200-light catalog sweep
  analysis from existing S2-Gate 103 artifacts without rerunning CUDA.

### S2-Gate 106: Resident Sweep Contract Frame-Gate Import

- Let the resident sweep harness import frame-accounting promotion requirements
  from an existing GLASS benchmark contract JSON.
- Map benchmark-contract `frame_accounting` fields into sweep frame-gate policy:
  input light frames, integrated frames, zero-weight frames, and minimum
  integrated-frame floor.
- Preserve explicit CLI frame-gate options as overrides when both CLI values and
  contract values are supplied.
- Record contract provenance in the sweep summary and Markdown output.
- Validate with dry-run tests and a real Phase 2 benchmark-contract dry run.

### S2-Gate 107: Resident Sweep Contract Compare Import

- Let the resident sweep harness import compare-gate thresholds and compare
  normalization defaults from an existing GLASS benchmark contract JSON.
- Map benchmark-contract `comparison` fields into sweep compare policy and
  compare command defaults:
  - shape-match requirement
  - maximum RMS difference
  - maximum p99 absolute difference
  - candidate scale and offset
  - minimum coverage threshold
  - external reference runtime
- Preserve explicit CLI compare values as overrides when both CLI values and
  contract values are supplied.
- Record compare-contract provenance in the sweep summary and Markdown output.
- Validate with dry-run tests and a real Phase 2 benchmark-contract dry run.

### S2-Gate 108: Contract-Gated 200-Light Catalog Sweep

- Run a bounded 200-light resident CUDA catalog-capacity sweep using imported
  science arguments from a known-good run command.
- Require GLASS benchmark-contract frame counts, guardrails with pixel
  verification, candidate coverage maps, and strict compare-gate overrides
  before any variant can be considered for promotion.
- Sweep `triangle_grid_top_per_cell` over a small candidate set and record
  total runtime, moving-catalog time, registration/warp time, frame counts,
  guardrail status, and reference comparison metrics.
- Treat speed-only wins as blocked when image agreement fails the strict
  compare gate.
- Record the result as evidence for the next registration-quality optimization
  target rather than changing defaults.

### S2-Gate 109: Contract-Gated 200-Light NMS Separation Sweep

- Run a bounded 200-light resident CUDA sweep over triangle catalog NMS minimum
  separation while keeping `triangle_grid_top_per_cell=2`.
- Use the same contract-derived frame gate, strict compare gate, candidate
  coverage maps, and guardrails with pixel verification as S2-Gate 108.
- Record the runtime, moving-catalog time, registration/warp time, frame counts,
  guardrail status, and reference comparison metrics for each separation value.
- Use the result to decide whether NMS separation alone can recover strict image
  agreement for the faster low-catalog-capacity path.
- Do not promote a default unless guardrails, frame gate, and strict compare
  gate all pass.

### S2-Gate 110: Contract-Gated 200-Light Grid-Shape Sweep

- Run a bounded 200-light resident CUDA sweep around the S2-Gate 109 near misses
  by varying star-grid column density while keeping rows fixed.
- Use the same contract-derived frame gate, strict compare gate, candidate
  coverage maps, and guardrails with pixel verification as S2-Gates 108-109.
- Record runtime, moving-catalog time, registration/warp time, frame counts,
  guardrail status, and reference comparison metrics for each grid/separation
  pair.
- Use the result to decide whether grid-column density alone can recover strict
  image agreement for the faster `triangle_grid_top_per_cell=2` path.
- Do not promote a default unless guardrails, frame gate, and strict compare
  gate all pass.

### S2-Gate 111: Resident Registration Candidate Audit

- Add a machine-readable audit for resident CUDA triangle registration candidate
  selection without rerunning GPU stacking.
- Parse existing `registration_results.json` warnings into stable JSON fields:
  triangle trial counts, candidate counts, fit RMS, pixel-refine RMS/NCC,
  quality-gate status, catalog parameters, and determinism signatures.
- Provide a CLI command that writes JSON and optional Markdown from a run
  directory or standalone `registration_results.json`.
- Run the audit over the S2-Gate 110 200-light variants to determine whether
  strict compare failures were caused by outright registration failures or by
  subtler agreement drift.
- Keep this as an observability gate; do not change registration defaults until
  a follow-up gate uses the audit to justify a scoring or refinement change.

### S2-Gate 112: Resident Candidate/Compare Correlation

- Join resident sweep compare metrics with S2-Gate 111 candidate audits so
  registration tuning can relate candidate/refine statistics to image
  difference outcomes.
- Provide a CLI command that reads `resident_prefetch_sweep_summary.json` plus
  a directory of `*_candidate_audit.json` files and writes JSON/Markdown.
- Record per-variant compare RMS, p99, frame failure counts, candidate-count
  statistics, fit RMS, pixel-refine RMS/NCC, and registration component timing.
- Compute simple correlation rows between candidate/refine statistics and
  compare metrics to identify the next optimization target.
- Run the join over the S2-Gate 110/111 200-light artifacts and keep the result
  as evidence for the next scoring/refinement gate.
- Keep this as an observability gate; do not change registration defaults until
  a follow-up gate proves a candidate change with guardrails and compare gates.

### S2-Gate 113: Resident Triangle Agreement Gate

- Add a project-defined resident triangle pixel-agreement score based on
  pixel-refine NCC penalized by pixel RMS so candidate/refine drift can be
  audited directly in `registration_results.json`.
- Keep default behavior audit-only; only reject frames when
  `cuda_triangle_min_agreement_score` or the matching CLI override is supplied.
- Record the agreement score, status, reason, RMS scale, and threshold in
  per-frame warnings and resident registration artifacts.
- Validate the score helper, resident triangle smoke path, CLI help, ruff, full
  pytest, and a lightweight real-data artifact/review before using the gate for
  200-light promotion sweeps.
- Treat this as a scoring-control gate, not a default-performance optimization;
  any stricter threshold must still pass frame-count, guardrail, and image
  compare gates before promotion.

### S2-Gate 114: Agreement-Threshold Sweep Dimension

- Extend the resident sweep harness so agreement thresholds and agreement RMS
  scales can be swept as first-class variant dimensions.
- Encode agreement threshold values in variant ids and generated `glass run`
  commands using `--resident-triangle-min-agreement-score` and
  `--resident-triangle-agreement-rms-scale`.
- Preserve existing sweep behavior when the new dimensions are omitted or set
  to `inherit`.
- Validate with dry-run matrix tests, ruff, full pytest, and a real-data dry run
  generated from the 200-light benchmark command before running expensive
  threshold sweeps.
- Do not promote any threshold in this gate; promotion requires a later
  executed sweep with frame-count, guardrail, and image-compare gates.

### S2-Gate 115: Contract-Gated Agreement Threshold Sweep

- Run a bounded 200-light resident CUDA sweep over the S2-Gate 113 triangle
  agreement threshold while importing the known-good 200-light command
  arguments from the latest proven grid-shape run.
- Use the benchmark-contract frame gate, benchmark-contract compare
  normalization, candidate coverage maps, and per-variant guardrails with
  pixel verification before any threshold can be considered rankable.
- Record per-variant runtime, frame counts, guardrail status, agreement
  threshold, agreement score statistics, registration component timings, and
  external-reference comparison metrics.
- Audit each completed variant with `glass resident-registration-audit` and
  join audit statistics with compare metrics using
  `glass resident-registration-compare`.
- Treat agreement-threshold variants as rejected for promotion if they drop the
  expected 193 integrated frames or fail strict image agreement, even if they
  improve runtime.
- Do not change defaults in this gate. Use the result only to decide whether
  agreement gating should become a quality control, a diagnostic, or a tuning
  dead end for the current M38 200-light benchmark.

### S2-Gate 116: Agreement Rejection Triage

- Add a reusable resident registration triage artifact that compares an
  audit-only baseline candidate audit against one or more agreement-threshold
  candidate audits.
- Report frames newly rejected by agreement gating, recovered frames, per-frame
  agreement score/RMS/NCC deltas, and signature drift for reference catalog,
  reference descriptor, moving catalog, moving descriptor, selected fit, and
  trial signatures.
- Run the triage over the S2-Gate 115 threshold sweep to determine whether the
  extra rejected frames are isolated threshold decisions or are mixed with
  resident catalog nondeterminism.
- Do not change thresholds or registration defaults in this gate; use the
  result to choose between deterministic catalog hardening and agreement-score
  tuning as the next real optimization step.

### S2-Gate 117: Deterministic Catalog Sweep Control

- Promote resident star-catalog deterministic mode into the resident sweep
  harness so matrices can explicitly run `inherit`, `off`, or `on` with stable
  variant ids and reproducible `glass run` commands.
- When this dimension is explicitly supplied, make the sweep harness own the
  `--resident-star-catalog-deterministic` flag so imported command files cannot
  accidentally keep deterministic mode enabled for an `off` variant.
- Validate the new sweep dimension with dry-run tests and a 200-light dry-run
  imported from the current benchmark command.
- Run two 200-light deterministic resident CUDA variants with the same
  parameters and compare them with `glass resident-determinism
  --fail-on-mismatch`.
- Accept this as a control-surface gate only if repeated deterministic runs
  match artifact signatures, per-frame signatures, registration results, frame
  accounting, and output pixels/maps.
- Do not change default fast catalog behavior in this gate. Use the result to
  rerun agreement-threshold experiments under deterministic catalog control.

## Gate Rules

Each gate requires:

- code or documentation matching the gate scope
- focused tests
- `python -m pytest -q`
- checkpoint file in `runs/checkpoints/`
- known limitations
- performance or numerical regression note when relevant
- Git commit

If a gate fails, stop and fix that gate before starting later work.

## Completion Criteria

Phase 2 is complete when:

- StackEngine is the default for master frames and light integration.
- DQ/mask propagation is a formal pipeline contract.
- Calibration, quality, registration, LN, and rejection are scientifically
  stronger than Phase 1.
- The 200-light dataset still runs end to end.
- Performance remains explainably close to or better than the Phase 1 baseline.
- Reports explain timing, memory, quality, masks, rejection, and output
  differences.
- The repository remains installable, testable, and auditable.
