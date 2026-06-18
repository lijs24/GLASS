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

### S2-Gate 118: Deterministic Agreement Threshold Sweep

- Rerun the S2-Gate 115 agreement-threshold experiment with
  `--star-catalog-deterministic-modes on` so candidate/signature changes are
  attributable to threshold logic instead of resident catalog nondeterminism.
- Use the same benchmark-contract frame gate, compare normalization, strict
  compare overrides, candidate coverage maps, and guardrails with pixel
  verification as S2-Gate 115.
- Audit each completed deterministic variant with
  `glass resident-registration-audit`, join compare metrics with
  `glass resident-registration-compare`, and repeat
  `glass resident-registration-triage` against the deterministic audit-only
  baseline.
- Treat a threshold as blocked if it improves RMS or p99 only by rejecting
  required frames from the 193-frame benchmark contract.
- Do not change defaults in this gate. Use the result to design a less blunt
  agreement policy, such as diagnostic flagging, down-weighting, or a
  multi-condition rejection rule.

### S2-Gate 119: Agreement Downweight Policy

- Add an explicit resident triangle agreement action with default behavior
  unchanged: hard fail remains the default when a minimum agreement score is
  supplied.
- Support `downweight` and `flag` actions so low-agreement frames can be kept
  in the 193-frame benchmark contract while still emitting audit warnings and
  per-frame diagnostics.
- Ensure downweighting composes with resident `simple_snr` weighting by applying
  agreement multipliers after frame-quality weights are computed and before
  local normalization/integration.
- Record agreement action, minimum weight, downweighted-frame count, and
  per-frame multipliers in resident artifacts and registration audits.
- Run deterministic 200-light sweeps over several downweight thresholds under
  the same strict frame gate, compare gate, and guardrails used in S2-Gate 118.
- Do not promote the policy unless it preserves 200/193/7 frame accounting and
  passes strict RMS and p99 compare gates. If linear downweighting fails, use
  the result to design a non-linear or multi-signal agreement weighting rule.

### S2-Gate 120: Compare Tail Outlier Audit

- Add a reusable `glass compare-outliers` audit that localizes strict compare
  p99 tails and target-threshold exceedance pixels after the same scale/offset,
  clipping, border, and coverage-mask policy used by benchmark compare gates.
- Report compared-pixel accounting, tail threshold, top residual tiles, top
  residual pixels, signed tail counts, edge-band fraction, and a machine-readable
  recommendation that classifies the tail as edge-dominated, localized,
  signed-global, or diffuse.
- Run the audit on the deterministic agreement baseline and the best
  S2-Gate 119 downweight candidate against the same user-generated external
  reference output.
- Treat this as an observability gate only. It must not promote weighting
  defaults; it decides whether the next optimization should inspect localized
  residual tiles, crop/coverage policy, normalization, or per-frame contribution
  maps before designing another agreement-weighting rule.

### S2-Gate 121: Localized Compare Tile Package

- Add a reusable `glass compare-tile-pack` command that consumes a
  `compare-outliers` JSON audit and exports the top residual tiles as small
  FITS cutouts plus optional PNG previews for GLASS, reference, signed diff,
  absolute diff, and coverage.
- Preserve the compare audit transform so tile cutouts use the same scale,
  offset, clipping, and source coordinates as the p99 residual audit.
- Write a `tile_pack_manifest.json` with tile extents, paths, diff statistics,
  and source top-tile metadata so localized residual evidence can be attached
  to later benchmark and report work.
- Run the package on the best S2-Gate 119 downweight candidate's S2-Gate 120
  outlier audit and inspect top signed-diff previews.
- Treat this as an observability gate only. It must not change defaults; it
  prepares the next gate to attribute localized residuals to frame
  contribution, rejection maps, local normalization, or registration.

### S2-Gate 122: Localized Tile Map Attribution

- Add a reusable `glass compare-tile-attribution` command that consumes a
  `compare-tile-pack` manifest and a GLASS run directory.
- Join localized residual tile extents with available integration output maps:
  coverage, weight, DQ, low rejection, and high rejection.
- Join the same report with `frame_accounting.json`, including integrated,
  zero-weight, low-weight, and agreement-downweighted frame counts and rows.
- Emit JSON and Markdown with per-tile coverage/rejection/weight/DQ summaries,
  frame-weight context, and explicit limitations when per-frame registered
  caches are unavailable.
- Run the command on the S2-Gate 121 `agr0p5` tile package.
- Treat this as an attribution-observability gate only. It must not change
  defaults; it decides whether map-level evidence explains the localized
  residuals or whether the next gate must save/replay per-frame tile samples.

### S2-Gate 123: Bounded Per-Frame Tile Replay

- Add a reusable `glass compare-tile-replay` command that consumes a
  `compare-tile-pack` manifest and a GLASS run directory.
- For each localized residual tile, replay selected source frames through a
  bounded CPU diagnostic path: read only the required source window, apply the
  available master calibration cache, apply the registration matrix, and sample
  the destination tile.
- Support frame selection strategies for all positive-weight frames,
  lowest-weight frames, and agreement-downweighted frames.
- Rank replayed frames by signed/weighted local delta to the final GLASS master
  tile and report diagnostic sigma-proxy low/high outlier counts.
- Record interpolation and limitation metadata. This diagnostic replay may use
  bilinear sampling even when the resident CUDA benchmark used Lanczos3, so it
  is attribution evidence rather than a byte-exact resident replay.
- Run the command on the S2-Gate 121 `agr0p5` tile package for all positive
  weight frames and compare with lower-cost low-weight/downweighted subsets.
- Treat this as an observability gate only. It must not change defaults; it
  identifies candidate frame families for the next numerical correction or
  exact replay gate.

### S2-Gate 124: Lanczos3 Replay Parity

- Extend `glass compare-tile-replay` with an explicit replay interpolation
  choice, at least `bilinear` and `lanczos3`.
- Implement bounded CPU Lanczos3 sampling in a vectorized way suitable for the
  exported residual tiles.
- Preserve the same source-window, master-calibration-cache, registration
  matrix, frame-selection, and ranking contract from S2-Gate 123.
- Run the Lanczos3 replay on the S2-Gate 121 `agr0p5` top residual tiles for
  agreement-downweighted frames and all positive-weight frames.
- Compare the top contributor ordering against the S2-Gate 123 bilinear replay.
- Treat this as an observability gate only. It must not change defaults; it
  decides whether the S2-Gate 123 frame-family finding survives closer
  interpolation parity with the resident Lanczos3 benchmark path.

### S2-Gate 125: Residual Frame-Family Audit

- Add a reusable `glass compare-frame-family` command that consumes a
  `compare-tile-replay` JSON artifact and a GLASS run directory.
- Let the audit select focus frames by explicit ids or an id range, then select
  neighboring positive-weight control frames unless explicit controls are
  provided.
- Join replay tile ranks/deltas, frame-accounting weights/agreement warnings,
  and registration matrices into per-frame rows with group summaries and
  focus-vs-control contrasts.
- Run the audit on the S2-Gate 124 `agr0p5` all-positive-weight Lanczos3
  replay for the F000100-F000110 frame family against neighboring controls.
- Treat this as an observability gate only. It must not change registration,
  weighting, rejection, or integration defaults; it should decide whether the
  next corrective gate should target a coherent motion/registration frame
  family, agreement weighting, or exact resident replay capture.

### S2-Gate 126: Resident Tile Capture Parity

- Add a native read-only resident CUDA API that downloads a bounded tile from a
  selected resident frame without downloading the full calibrated stack.
- Add a reusable `glass resident-tile-capture` command that rebuilds only
  selected positive-weight frames into a small resident CUDA stack, applies the
  run's master calibration cache and registration matrices, then captures the
  localized residual tiles after resident CUDA calibration and warp.
- Join the captured tile statistics with an optional `compare-tile-replay` JSON
  artifact so the resident CUDA capture can be checked against the bounded CPU
  Lanczos3 replay used in S2-Gates 123-124.
- Write JSON and optional Markdown summaries, and optionally write captured
  FITS tile artifacts for visual inspection.
- Run the command on the S2-Gate 121 top residual tiles for the F000100-F000110
  focus family identified by S2-Gate 125.
- Treat this as a parity/observability gate only. It must not change default
  registration, weighting, rejection, local normalization, or integration
  behavior; it should decide whether replay disagreement is a likely cause or
  whether the next corrective work should target the integration/rejection
  policy itself.

### S2-Gate 127: Localized Integration Contribution Audit

- Add a reusable `glass compare-tile-integration` command that consumes a
  `compare-tile-pack` manifest and a GLASS run directory.
- Replay all selected positive-weight frames for each localized residual tile,
  applying the same bounded source-window, master-calibration-cache,
  registration-matrix, and interpolation diagnostics established in
  S2-Gates 123-126.
- Recompute the resident CUDA rejection semantics over the replayed tile stack:
  `none`, two-pass mean/std `sigma_clip`, and the current two-stage
  `winsorized_sigma` approximation.
- Emit per-frame accepted/rejected pixel counts, low/high rejection counts,
  accepted weighted deltas, normalized contribution to the reconstructed tile,
  focus/control group summaries, and diagnostic reconstructed-master delta to
  the actual GLASS master tile.
- Run the command on the S2-Gate 121 top residual tiles for all 193
  positive-weight frames, focusing F000100-F000110 against neighboring control
  frames.
- Treat this as an observability gate only. It must not change registration,
  weighting, rejection, local normalization, or integration defaults; it should
  decide whether the localized residual family survives the actual rejection
  policy and therefore should be handled by a motion-family/weighting policy
  rather than by calibration, interpolation, or warp replay fixes.

### S2-Gate 128: Registration-Motion Weighting Candidate

- Add an explicit opt-in resident registration-motion weighting policy.
- The first supported mode is `translation_mad`: group accepted registration
  matrices by orientation cluster, compute robust translation centers and MAD
  scales per cluster, and downweight high-score motion outliers with a smooth
  multiplier floor.
- Apply the multiplier after normal integration weighting and triangle
  agreement downweighting, so it composes with existing frame-quality and
  agreement evidence without turning frames into hard registration failures.
- Record per-frame motion cluster, distance, score, multiplier, and before/after
  weight in `resident_artifacts.json`, and add registration warnings for frames
  actually motion-downweighted so `frame_accounting.json` can surface the cause.
- Preserve default behavior: the policy must default to `off`.
- Run a 200-light candidate using the S2-Gate 119 benchmark settings plus the
  opt-in policy, compare against the same user-generated external reference,
  and decide whether the policy is promotable.
- Do not promote if it fails to materially reduce the localized residual tail or
  if it causes unexplained frame-count, timing, or artifact regressions.

### S2-Gate 129: Localized Frame-Weight Proposal

- Add a reusable `glass frame-weight-proposal` command that consumes a
  `compare-tile-integration` JSON artifact and produces an explicit proposal
  JSON containing per-frame multipliers for a localized focus family.
- The first supported proposal method is `control_ratio`: compute the ratio of
  neighboring control contribution mean to focus-family contribution mean, clamp
  it to a configured multiplier range, and assign that multiplier to every
  focus frame listed by the diagnostic artifact.
- Add an opt-in resident CUDA input,
  `--resident-frame-weight-proposal`, that applies proposal multipliers after
  ordinary integration weighting, triangle agreement downweighting, and
  registration-motion weighting.
- Record the loaded proposal, applied downweighted frame count, per-frame
  multiplier, and registration warnings in resident artifacts so frame
  accounting can explain the experiment.
- Preserve default behavior: no proposal is loaded unless the user supplies the
  JSON path explicitly.
- Run a 200-light candidate generated from the S2-Gate 127 F000100-F000110
  localized integration audit and compare it against the same user-generated
  external reference.
- Do not promote if the candidate improves only the known focus tile while
  damaging global residual statistics, frame counts, or timing.

### S2-Gate 130: Frame-Weight Proposal Direction Audit

- Add a reusable `glass frame-weight-proposal-audit` command that consumes a
  `compare-tile-integration` audit, a frame-weight proposal JSON, and the
  matching tile-pack residual manifest.
- For each localized residual tile, compare the signed GLASS-minus-reference
  residual direction against the first-order master change implied by applying
  the proposal multiplier to the focus-family contribution.
- Emit per-tile predicted master delta in GLASS ADU and transformed reference
  units, before/after signed residual estimates, and `moves_toward_reference`
  booleans for both mean residual and tail residual summaries.
- Use this as a gate before any further weighting experiment: a proposal that
  moves residuals away from the reference direction should not be promoted, even
  if its source contribution audit identified a coherent frame family.
- Run the audit on the S2-Gate 129 F000100-F000110 proposal and confirm whether
  the failed 200-light candidate was directionally predictable.

### S2-Gate 131: Resident Tile Contribution Capture

- Add a reusable `glass resident-tile-contribution` command that rebuilds
  selected positive-weight frames into a small resident CUDA stack, applies the
  same master calibration cache and registration matrices, downloads bounded
  post-warp resident tile pixels, and replays rejection/contribution statistics
  on those captured resident pixels.
- Reuse the localized residual tile-pack manifest and support the same
  frame-selection controls used by prior attribution tools: all positive frames
  by frame id, lowest-weight frames, agreement-downweighted frames, plus
  focus/control frame selection for group summaries.
- Emit per-frame accepted/rejected pixel counts, weighted delta, normalized
  contribution, focus/control summaries, diagnostic reconstructed-master delta,
  and capture timing.
- Treat this as a near-native observability gate: it avoids CPU interpolation
  replay, but it still computes contribution/rejection summaries on the CPU
  after downloading selected resident tiles.
- Run the command on the S2-Gate 121 top residual tile package using the
  S2-Gate 119/120 benchmark run and the F000100-F000110 focus family.

### S2-Gate 132: Tile-Local Policy Proposal

- Add a reusable `glass tile-local-policy-proposal` command that consumes a
  `resident-tile-contribution` artifact and its matching residual tile-pack
  manifest.
- For each localized residual tile, solve a first-order tile-local multiplier
  for a target group, initially `focus`, using signed GLASS-minus-reference
  residuals and the resident-captured group contribution in reference units.
- Support bounded multipliers so the proposal can express both downweight and
  boost directions without silently pretending an unconstrained correction is
  safe.
- Emit per-tile action (`boost`, `downweight`, `hold`, or
  `insufficient_signal`), unconstrained and clamped multiplier, predicted
  residual after applying the local multiplier, residual-reduction fraction,
  and summary recommendation.
- Treat this as an artifact-only gate. It must not change the integration
  output or enable tile-local weights in the production pipeline yet.
- Run the command on the S2-Gate 131 resident contribution artifact for the
  F000100-F000110 focus family and decide whether a future tile-local native
  implementation is directionally justified.

### S2-Gate 133: Tile-Local Policy Replay

- Add a reusable `glass tile-local-policy-replay` command that consumes a
  `resident-tile-contribution` artifact and a matching
  `tile-local-policy-proposal` artifact.
- Reconstruct the proposal at summary level for each localized residual tile:
  selected target-family frame rows, original contribution, proposed
  contribution, delta contribution, signed residual before and predicted
  residual after.
- Keep canonical tile contribution values from the proposal while reporting
  per-frame row sums from the resident contribution artifact, so mismatches
  between stored group summaries and frame rows are visible.
- Emit JSON and optional Markdown summaries with boost/downweight counts,
  clamping counts, mean before/after residuals, multiplier statistics, and a
  conservative recommendation.
- Treat this as a pre-native replay gate only. It must not change production
  integration, resident CUDA buffers, frame weights, or image pixels.
- Run the command on the S2-Gate 132 F000100-F000110 focus proposal and use it
  as the handoff contract for a future native tile-local integration
  implementation.

### S2-Gate 134: Resident Tile-Local Policy Contract

- Add an explicit resident-run input for a `tile-local-policy-replay` artifact.
- Validate the replay contract before integration: artifact type, target group,
  target frame ids, non-negative multipliers, positive tile extents, summary
  direction fields, and per-tile canonical deltas.
- Record the validated contract in `resident_artifacts.json` under resident
  integration weighting diagnostics.
- Preserve current science output. This gate must mark the contract as
  `validated_not_applied` and must not alter frame weights, resident CUDA
  buffers, integration maps, or output pixels.
- Add tests for the contract loader and an opt-in resident CUDA smoke path that
  records the contract while leaving the existing frame-weight proposal behavior
  intact.
- Treat this as the interface lock for a future native tile-local integration
  implementation.

### S2-Gate 135: Opt-In Resident Tile-Local Mean

- Add a native `ResidentCalibratedStack.integrate_tile_local_mean` primitive
  for resident stack dispatch only.
- Apply tile-local multipliers to selected target frames inside explicit
  half-open tile extents while preserving frame-global weights elsewhere.
- Support `rejection=none` weighted mean only in this gate. Sigma and
  winsorized rejection must remain on the record-only replay contract.
- Add `--resident-tile-local-policy-mode record|apply_mean`; keep `record` as
  the default so existing science output is unchanged.
- Validate target-frame membership, image-bounded tile extents,
  non-overlapping tiles, and finite non-negative multipliers before launching
  the native primitive.
- Record native timing, applied tile/frame counts, multiplier statistics, and
  limitations in `resident_artifacts.json`.
- Add direct CUDA CPU-reference tests for the primitive and a resident CLI smoke
  test that proves the opt-in route changes only the target tile as expected.

### S2-Gate 136: Opt-In Resident Tile-Local Rejection

- Add a native `ResidentCalibratedStack.integrate_tile_local_sigma_clip`
  primitive for resident stack dispatch.
- Add `--resident-tile-local-policy-mode apply` as the forward path for
  tile-local policies across `none`, `sigma_clip`, and `winsorized_sigma`
  rejection modes.
- Preserve `apply_mean` as a compatibility alias limited to `rejection=none`.
- Reuse the same replay contract validation as S2-Gate 135: target-frame
  membership, image-bounded non-overlapping tile extents, and finite
  non-negative multipliers.
- Apply tile-local multipliers before resident rejection accumulation so
  weight, coverage, low-rejection, and high-rejection maps remain produced by
  the native path.
- Record native timing, rejection mode, applied tile/frame counts, multiplier
  statistics, and limitations in `resident_artifacts.json`.
- Add direct CUDA CPU-reference tests for winsorized tile-local rejection and a
  resident CLI smoke test proving `apply` routes through the rejection-aware
  primitive and writes rejection maps.

### S2-Gate 137: Bounded 200-Light Tile-Local Apply Experiment

- Add a reusable `glass tile-local-apply-experiment` command that audits a
  real resident CUDA baseline run, a candidate tile-local `apply` run, the
  replay contract used by the candidate, optional compare artifacts, and the
  pinned 200-light benchmark contract.
- Treat candidate promotion as a hard evidence gate: the candidate must record
  a native applied tile-local policy, match baseline and contract frame
  accounting, remain within the runtime regression budget, preserve the
  benchmark speedup floor, and pass the same reference-compare RMS/p99/coverage
  thresholds.
- Keep localized improvement evidence explicit. The command must surface the
  replay-predicted before/after residuals, the count of tiles moving toward the
  reference, multiplier statistics, applied tile count, applied target-frame
  count, and native tile-local timing.
- Keep this as an opt-in experiment. Do not change the default resident
  `record` mode, do not automatically promote the policy globally, and do not
  hide missing compare artifacts as success.
- Run the command on the M38 H-alpha 200-light benchmark using the
  F000100-F000110 bounded replay contract before planning any broader
  tile-local policy sweep.

### S2-Gate 138: Non-Overlapping Tile-Local Policy Subsets

- Add `glass tile-local-policy-subset` to convert a tile-local replay artifact
  into a native-apply-compatible non-overlapping replay subset.
- Preserve the `tile_local_policy_replay` artifact type so the resident CUDA
  pipeline can consume the subset directly, while recording source replay,
  selection strategy, original tile count, selected tile count, overlap drops,
  limit drops, and recalculated replay summary statistics.
- Support greedy strategies for `canonical_delta_abs`, `residual_reduction`,
  and `tile_index`, plus an optional maximum selected tile count.
- Add tests proving overlapping tiles are dropped deterministically and the
  summary is recomputed from the selected subset.
- Run the command on the S2-Gate 133 F000100-F000110 replay, then run a
  200-light resident CUDA bounded apply experiment with the selected subset and
  verify it through compare, `tile-local-apply-experiment`, and
  `acceptance-audit`.
- Keep this as an experiment-only gate. Do not enable tile-local apply by
  default and do not promote global policy selection until localized post-apply
  residual verification exists.

### S2-Gate 139: Localized Tile-Local Apply Verification

- Add `glass tile-local-apply-verify` to measure selected tile-local apply
  residuals directly from baseline master, candidate master, reference master,
  and replay/subset tile extents.
- Apply the same GLASS-to-reference scale/offset/clip transform used by the
  benchmark compare, and optionally mask tile pixels by coverage.
- Emit per-tile measured residual statistics before and after apply:
  signed mean, mean absolute residual, median absolute residual, RMS, p90/p99,
  maximum absolute residual, compared pixels, and measured improvement flags.
- Emit summary-level measured before/after mean absolute residual and RMS,
  improved-tile counts, pass/fail status, and recommendation.
- Add synthetic FITS tests and run the command on the S2-Gate 138 two-tile
  200-light candidate to verify measured local residual movement.
- Keep this as a diagnostic gate. It must not mutate pipeline outputs and must
  not enable tile-local apply by default.

### S2-Gate 140: Measured Tile-Local Policy Decision

- Add `glass tile-local-policy-decision` to rank and accept/reject one or more
  measured tile-local apply verification artifacts.
- Consume optional `tile-local-apply-experiment` and `acceptance-audit`
  artifacts so local measured improvement is gated by the same real-data
  200-light runtime, frame-accounting, compare, and DQ contracts.
- Require configurable minimum signed-mean improvement fraction, RMS
  improvement fraction, mean-absolute-residual improvement fraction, aggregate
  mean-absolute-residual improvement, and aggregate RMS improvement.
- Emit candidate scores, per-candidate checks, global checks, failed reasons,
  top candidate, accepted/rejected status, and Markdown summary.
- Run the decision command on the S2-Gate 139 two-tile verification plus the
  S2-Gate 138 apply experiment and acceptance audit.
- Keep this as a promotion-control artifact only. It must not mutate pipeline
  outputs and must not enable tile-local apply by default.

### S2-Gate 141: Measured Tile-Local Policy Sweep Summary

- Add `glass tile-local-policy-sweep` to rank multiple
  `tile-local-policy-decision` artifacts from measured candidates.
- Emit accepted/rejected counts, top decision, top score, top tile count, and
  per-decision measured residual summary fields.
- Run the sweep over the measured single-tile and two-tile candidates from
  S2-Gates 137-140.
- Keep this as a summary artifact. It must not run new image processing, mutate
  pipeline outputs, or enable tile-local apply by default.

### S2-Gate 142: Tile-Local Sweep Plan And Three-Tile Candidate

- Add `glass tile-local-sweep-plan` to generate a reproducible command queue for
  measured tile-local policy sweeps.
- The plan must derive candidate subset paths, run directories, compare,
  apply-experiment, acceptance-audit, verification, decision, and final sweep
  commands from explicit inputs.
- Run the plan over the measured F000100-F000110 replay and include the
  single-tile, two-tile, and three-tile candidate ladder.
- Execute the three-tile candidate through the same real-data compare,
  acceptance, local verification, decision, and sweep checks used for the
  previous measured candidates.
- The plan and measured candidate must remain opt-in and must not enable
  tile-local apply by default.

### S2-Gate 143: Residual Tile Candidate Mining

- Add `glass residual-tile-candidates` to merge one or more
  `compare-outliers` artifacts into a larger residual tile candidate manifest.
- Rank candidates by an explicit tail metric, greedily drop overlapping selected
  candidates by default, and mark overlaps with known tile packs so new regions
  are distinguishable from previously studied F000100-F000110 tiles.
- Emit top-level `tiles` with extents so downstream resident tile contribution
  tools can consume the manifest as a tile-pack-like input.
- Run the command on the existing 200-light outlier audits and the Gate121
  known tile pack to produce a broader candidate set for the next contribution
  capture gate.
- Keep this as an artifact-mining gate. It must not read image pixels, rerun
  integration, mutate pipeline outputs, or enable tile-local apply by default.

### S2-Gate 144: New-Region Resident Contribution Capture

- Extend residual tile candidate mining with `known-overlap-mode` so a sweep can
  include, exclude, or isolate regions overlapping previously studied tile
  packs.
- Generate a new-region-only tile candidate manifest from the S2-Gate 143
  outlier sources and the S2-Gate 121 known tile pack.
- Run `resident-tile-contribution` on the new-region manifest using the
  200-light resident CUDA benchmark run, all positive-weight frames, the
  F000100-F000110 focus range, neighboring control frames, and winsorized sigma
  rejection.
- Emit focus/control contribution summaries for the newly mined residual
  regions so the next proposal gate can decide whether the same frame family
  explains more than the original three tiles.
- Keep this as a diagnostic gate. It must not change weighting, rejection,
  registration, local normalization, integration defaults, or tile-local apply
  defaults.

### S2-Gate 145: New-Region Tile-Local Proposal Replay

- Run `tile-local-policy-proposal` on the S2-Gate 144 new-region resident
  contribution artifact using the F000100-F000110 focus group and
  tail-signed-mean residuals.
- Run `tile-local-policy-replay` on the proposal to measure summary-level
  before/after residual movement across all new-region tiles.
- Record whether the new-region proposal moves every tile toward the reference,
  whether it requires clamped boost/downweight multipliers, and whether the
  aggregate residual reduction is material enough to justify a future native
  apply experiment.
- Keep this as a proposal/replay gate only. It must not run a new integration,
  mutate image pixels, or promote tile-local apply by default.

### S2-Gate 146: Tile-Local Multiplier Saturation Diagnostics

- Extend `tile-local-policy-proposal` summary output with explicit multiplier
  saturation diagnostics.
- Record unconstrained multiplier stats, applied multiplier stats, required
  boost/downweight stats, applied-to-required boost ratio, downweight depth
  ratio, clamped fraction, and mean residual reduction fraction.
- Re-run the S2-Gate 145 new-region proposal and replay to verify the
  diagnostics explain the universal max-boost clamp without changing replay
  compatibility.
- Keep this as an artifact/diagnostic gate only. It must not change resident
  integration defaults, image pixels, or promotion thresholds.

### S2-Gate 147: Tile-Local Frame-Family Search

- Add `glass tile-local-frame-family-search` to rank contiguous frame windows
  from a resident contribution artifact by bounded tile-local residual
  correction potential.
- Score candidate frame windows with the same residual, GLASS-to-reference
  scale, multiplier bounds, and saturation diagnostics used by
  `tile-local-policy-proposal`.
- Run the search on the S2-Gate 144 new-region contribution artifact across
  1/3/5/11-frame windows and retain both top-ranked and all-candidate
  artifacts.
- Use the result to decide whether F000100-F000110 is an arbitrary focus group
  or the best currently visible frame-family explanation.
- Keep this as a search/diagnostic gate only. It must not change resident
  integration defaults, image pixels, or promotion thresholds.

### S2-Gate 148: Tile-Local Residual Source Audit

- Add `glass tile-local-residual-source-audit` to summarize coverage,
  rejection-map, focus/control rejection, and top frame-family explanatory
  signals for residual candidate tiles.
- Consume the S2-Gate 144 new-region contribution artifact and S2-Gate 147
  frame-family search artifact without reading image pixels.
- Separate obvious coverage/valid-mask problems from rejection/registration
  interaction clues and weak frame-family explanations.
- Use this gate to decide whether the next native experiment should continue
  frame-family weighting or pivot toward rejection/registration diagnostics.
- Keep this as an artifact/diagnostic gate only. It must not change resident
  integration defaults, image pixels, or promotion thresholds.

### S2-Gate 149: Tile-Local Rejection/Registration Audit

- Add `glass tile-local-rejection-registration-audit` to aggregate
  frame-level rejection and registration agreement diagnostics across residual
  candidate tiles.
- Consume the S2-Gate 144 resident contribution artifact and optional
  S2-Gate 147 frame-family search artifact.
- Rank frames by high-rejection fraction and record focus/control/top-family
  membership, triangle agreement score, agreement weight multiplier, NCC,
  registration RMS, accepted fraction, and rejection fraction.
- Emit group summaries and correlations so the next gate can decide whether to
  test registration agreement, rejection behavior, or frame weighting.
- Keep this as an artifact/diagnostic gate only. It must not change resident
  integration defaults, image pixels, or promotion thresholds.

### S2-Gate 150: Tile-Local Rejection/Registration Experiment Plan

- Add `glass tile-local-rejection-registration-plan` to turn Gate149 audit
  evidence into explicit measured-experiment commands.
- Generate candidate run directories and command queues from a baseline
  resident `run_command.txt`.
- Include at least these opt-in candidates: agreement flag-only, softer
  agreement downweight, stricter agreement downweight, and exclusion of the
  highest-rejection focus/top-family hotspot frames.
- Emit optional compare and acceptance-audit commands when reference,
  manifest, WBPP result, and benchmark contract inputs are provided.
- Keep this as a planning gate only. It must not execute heavy integration,
  change resident integration defaults, mutate image pixels, or promote any
  candidate.

### S2-Gate 151: Soft Agreement-Downweight Candidate Execution

- Execute the `agreement_soft_downweight` candidate from the S2-Gate 150 plan.
- Use the same 200-light benchmark inputs, WBPP black-box reference, compare
  scale/offset, minimum coverage, frame-accounting contract, DQ contract, and
  runtime contract as the Phase 1/2 baseline.
- If the first run fails for runtime or compare-contract reasons, preserve the
  failed artifact and rerun only after identifying whether the failure is a
  candidate regression or an anomalous run/contract-parameter issue.
- Record candidate runtime, compare metrics, acceptance status, speedup, and
  dominant timing stages.
- Keep this as an opt-in measured candidate gate. Passing this gate does not
  promote the candidate to default behavior; it only makes it eligible for
  broader candidate comparison.

### S2-Gate 152: Candidate-vs-Baseline Comparison

- Add `glass candidate-comparison` to compare a measured candidate run against
  a baseline GLASS run using existing run timing, frame accounting, reference
  compare, candidate-vs-baseline compare, and acceptance-audit artifacts.
- Recompute the baseline-vs-reference compare for the same no-border,
  minimum-coverage region used by the Gate151 retry candidate, then compare the
  Gate151 retry candidate directly against the Gate119 historical baseline.
- Require candidate acceptance, minimum speedup versus the black-box reference,
  shape agreement, bounded reference RMS/p99 growth, and unchanged frame
  accounting before marking the candidate as passed.
- Preserve a conservative recommendation: a passing candidate can enter broader
  sweeps, but if it is slower than the historical baseline it is not promoted
  as a default policy.
- Keep this as an artifact/decision gate only. It must not execute integration,
  mutate image pixels, alter CUDA kernels, or change resident defaults.

### S2-Gate 153: Candidate Comparison Sweep Summary

- Add `glass candidate-comparison-sweep` to rank multiple
  `candidate-comparison` artifacts in one measured sweep summary.
- Preserve failed candidate attempts as first-class rows instead of discarding
  them, including failed required checks and runtime/speedup evidence.
- Rank candidates by acceptance pass status, speedup, runtime, and reference
  agreement, while keeping the recommendation scoped to broader sweep planning
  rather than default promotion.
- Run the sweep over the Gate151 failed first attempt and the Gate151 retry
  success artifact so the runtime anomaly and recovery remain auditable.
- Keep this as an artifact/decision gate only. It must not execute integration,
  run image compares, mutate image pixels, or alter resident defaults.

### S2-Gate 154: Runtime-Focused Candidate Sweep Plan

- Add `glass candidate-runtime-sweep-plan` to derive runtime-only experiment
  variants from the accepted `agreement_soft_downweight` candidate command.
- Keep science parameters fixed and vary only resident orchestration knobs such
  as prefetch depth/workers and calibration batch/stream/wave settings.
- Generate explicit run, reference-compare, baseline-compare,
  acceptance-audit, candidate-comparison, and final sweep-summary commands for
  each planned variant.
- Preserve failed variants as candidate-comparison artifacts by not using
  per-candidate fail-fast behavior in generated comparison commands.
- Keep this as a planning gate only. It must not execute integration, run image
  compares, mutate image pixels, or alter resident defaults.

### S2-Gate 155: Runtime-Focused Candidate Sweep Execution

- Execute the S2-Gate 154 runtime-only variants sequentially on the 200-light
  benchmark dataset.
- For each variant, run integration, reference compare, baseline compare,
  acceptance audit, and candidate-comparison without changing science options.
- Run the generated `candidate-comparison-sweep` summary to rank all measured
  variants by acceptance, speedup, runtime, and reference agreement.
- Record stage timing differences so the next gate can decide whether to
  promote a runtime setting or run a narrower confirmation sweep.
- Keep this as a measured benchmark gate only. It must not alter resident
  defaults until a follow-up promotion gate explicitly accepts a variant.

### S2-Gate 156: Prefetch/Worker Matrix Planning and Preflight

- Extend `glass candidate-runtime-sweep-plan` with generated
  prefetch-frame/prefetch-worker matrix variants.
- Use the Gate155 best result to plan a narrow confirmation matrix around
  prefetch frames 10/12/14 and workers 5/6/7 while inheriting the accepted
  soft-downweight science settings.
- Preserve explicit run, reference-compare, baseline-compare,
  acceptance-audit, candidate-comparison, and final sweep-summary commands for
  every matrix cell.
- Run focused and full tests for the matrix planner.
- If GPU memory is unavailable because another process is using the device,
  record the failed preflight and stop before executing later gates. Do not
  kill unrelated user processes.
- Keep this as a planning/preflight gate when GPU is occupied. The measured
  matrix execution remains the next gate after GPU memory is available.

### S2-Gate 157: Resumable Runtime Sweep Executor

- Add `glass candidate-runtime-sweep-execute` to execute or dry-run the
  S2-Gate 156 prefetch/worker matrix plan from one auditable command.
- Support variant selection, `--start-at`, `--stop-after`, `--skip-existing`,
  dry-run review, executable substitution, working-directory control, and
  fail-on-failed behavior so interrupted sweeps can resume without rerunning
  completed candidate-comparison artifacts.
- Record every planned or executed step with command, status, return code, and
  elapsed time in a `candidate_runtime_sweep_execution` JSON artifact.
- Harden local diagnostics for Windows/loaded-GPU environments: `glass doctor`
  can skip CUDA probing, CUDA tests skip when the GPU is externally saturated,
  optional astroalign-dependent tests skip when the library smoke test hangs,
  and benchmark subprocesses have explicit timeouts.
- Keep this as an orchestration and test-hardening gate. The dry-run artifact
  proves the executor contract; measured matrix execution remains the next gate
  when the GPU is reserved for GLASS.

### S2-Gate 158: Prefetch/Worker Matrix Execution

- Execute the S2-Gate 156 3x3 prefetch-frame/prefetch-worker matrix with the
  S2-Gate 157 resumable executor on the 200-light benchmark dataset.
- For every variant, run GLASS resident CUDA integration, reference compare,
  baseline compare, acceptance audit, and candidate comparison with fixed
  science settings.
- Run the generated `candidate-comparison-sweep` summary and record the ranked
  matrix.
- Treat this as benchmark evidence only. A later promotion gate must explicitly
  update defaults or recommended command templates.
- Current measured winner: `prefetch12_workers7`, `17.101234800000043 s`,
  `63.88667325940681x` versus the black-box reference, and `0.9549992718308159`
  runtime ratio versus the historical GLASS baseline.

### S2-Gate 159: Explicit Throughput Runtime Preset

- Add an opt-in `--resident-runtime-preset throughput-v1` for `glass run` and
  `glass audit`.
- The preset applies only resident runtime scheduling knobs measured in
  S2-Gate 158: prefetch frames/workers, queued refill, pinned-ring H2D, and
  batched multistream calibration with callback-queue release.
- Preserve the conservative `manual` default. Do not silently change scientific
  defaults or force the preset on users.
- Respect explicit user overrides for any individual runtime knob so the preset
  can be used as a starting point for later tuning.
- Record the effective values in existing resident artifacts through the
  `resident_io_pipeline` contract.

### S2-Gate 160: Throughput Preset Confirmation and Contract Update

- Run the 200-light benchmark with `--resident-runtime-preset throughput-v1`
  instead of manually expanding every runtime scheduling flag.
- Compare the preset run against the black-box reference and the historical
  GLASS baseline with the same scale/offset and coverage contract.
- Extend benchmark contracts with `required_command_token_groups` so a contract
  can accept equivalent command evidence, such as explicit `--resident-h2d-mode
  pinned_ring` or the measured throughput preset.
- Record that the preset path applied the intended runtime values in
  `resident_io_pipeline`.
- Current confirmation result: accepted and scientifically consistent, but
  slower than the Gate158 winner because read/decode wait time increased.
  Therefore the preset remains opt-in and is not promoted to default.

### S2-Gate 161: Resident Runtime Variance Compare

- Add `glass resident-runtime-compare` to compare resident CUDA timing artifacts
  from multiple GLASS runs without rerunning image processing.
- Read `run_timing.json` and `resident_artifacts.json`, rank runs by elapsed
  time, and report resident I/O settings plus stage timings for read/decode,
  H2D+calibration, registration/warp, integration, output, and GC.
- Compare Gate158 `prefetch12_workers7` against Gate160
  `--resident-runtime-preset throughput-v1` to prove both used the same
  effective resident scheduling settings.
- Current diagnosis: Gate160 is `1.364279174741225x` slower overall, but
  H2D+calibration and registration/warp are essentially unchanged. The
  regression is dominated by read/decode variance: read-wait ratio
  `2.451504514719359`, worker-read cumulative ratio `2.0380521300990586`.
- Recommendation: repeat the preset measurement with warm cache or in a
  dedicated I/O window before changing defaults. Keep `throughput-v1` opt-in.

### S2-Gate 162: Resident Runtime Repeat Plan

- Add `glass resident-runtime-repeat-plan` to convert a known-good
  `run_command.txt` into repeated resident benchmark commands.
- Preserve the original scientific and runtime settings, replacing only the
  `--out` directory for each repeat.
- Record the intended cache/I/O state label, repeat count, baseline repeat, run
  directories, commands, and a final `resident-runtime-compare` command.
- Generate a dedicated-I/O-window repeat plan for the Gate160
  `throughput-v1` command under
  `C:\glass_runs\phase2_s2_gate_162_repeat_plan`.
- Keep this as a planning gate while the local GPU is externally loaded. The
  next measured gate can execute the generated commands when the machine is in
  a controlled I/O/GPU window.

### S2-Gate 163: Resident Runtime Repeat Executor

- Add `glass resident-runtime-repeat-execute` to execute or dry-run a
  `resident-runtime-repeat-plan`.
- Support dry-run review, `--skip-existing` based on `run_timing.json`,
  optional `glass` executable substitution, working-directory control, optional
  final compare execution, and fail-on-failed exit status.
- Record each repeat run command and the final `resident-runtime-compare`
  command with status, return code, and elapsed time when executed.
- Validate the Gate162 real repeat plan with a dry-run execution audit under
  `C:\glass_runs\phase2_s2_gate_163_repeat_executor`.
- Keep this as an orchestration gate. Heavy 200-light repeat execution remains
  blocked until the local GPU and disks are available for a controlled window.

### S2-Gate 164: Resident Runtime Repeat Preflight

- Add `glass resident-runtime-repeat-preflight` to check whether a
  `resident-runtime-repeat-plan` is safe to execute before launching heavy
  200-light repeats.
- Validate run output directories, existing `run_timing.json` resume markers,
  final compare output path, CUDA/resident command intent, and point-in-time
  `nvidia-smi` GPU memory/utilization state.
- Emit `ready_to_execute`, `recommendation`, GPU status, per-repeat run status,
  and output conflict counts in a JSON artifact.
- Run the preflight against the Gate162 plan under
  `C:\glass_runs\phase2_s2_gate_164_repeat_preflight`.
- Current result: not ready. Three repeat outputs are clean and ready, but the
  GPU is externally busy, so the recommendation is
  `wait_for_controlled_window`.

### S2-Gate 165: Preflight-Gated Resident Repeat Executor

- Extend `glass resident-runtime-repeat-execute` with
  `--require-preflight-ready`.
- When enabled, run the repeat preflight before launching any repeat command.
  If the preflight recommendation is not `execute_repeat_plan`, write an
  execution audit with `status=preflight_blocked` and do not start image
  processing.
- Support writing the embedded preflight to a separate `--preflight-out` path
  and reuse the same GPU readiness thresholds as `resident-runtime-repeat-preflight`.
- Validate the Gate162 plan with guarded dry-run output under
  `C:\glass_runs\phase2_s2_gate_165_guarded_repeat_executor`.
- Current result: guarded execution correctly blocks before launching repeats
  because the local GPU remains externally busy.

### S2-Gate 166: StackEngine Result DQ Contract

- Add an in-memory StackEngine result contract builder for CPU StackEngine
  outputs.
- Validate requested output-map presence, map shape consistency, finite master
  pixels, coverage/no-data agreement, rejection-map/DQ-flag agreement,
  DQ-summary/provenance agreement, coverage-sum/metrics agreement, and
  request-shape/input-sample agreement.
- Embed the result contract into `StackEngineResult.dq_provenance` and expose
  a `result_contract_passed` metric without changing pixel calculations.
- Add synthetic CPU StackEngine tests that cover passing results, provenance
  drift, missing requested maps, and rejection/DQ mismatch.
- Keep this as a core contract gate. It strengthens DQ/mask invariants at the
  engine boundary and does not require the externally busy GPU.

### S2-Gate 167: StackEngine Contract Requires Result Contract

- Extend `glass stack-engine-contract` so CPU StackEngine calibration and
  integration records must include an embedded `result_contract` with
  `passed=true`.
- Surface `result_contract_passed` for every master and integration output in
  the StackEngine contract audit.
- Preserve resident CUDA acceptance behavior: `expected_integration_engine=
  cuda_resident_stack` still uses the resident provenance path until resident
  result-contract parity is implemented.
- Add regression coverage for legacy StackEngine-looking records that have DQ
  provenance but no embedded result contract.
- Generate a small synthetic CPU audit and StackEngine contract artifact under
  `C:\glass_runs\phase2_s2_gate_167_stack_contract_result_gate`.

### S2-Gate 168: Pipeline Contract Exposes StackEngine Result Contract

- Extend `glass pipeline-contract` so integration rows expose
  `stack_result_contract` status from embedded StackEngine DQ provenance.
- Add a new `integration_stack_result_contract` check: CPU StackEngine
  integration outputs must carry `result_contract.passed=true`.
- Preserve resident CUDA behavior by treating result-contract status as not
  required unless the output declares CPU StackEngine provenance or
  `tile_stack_mode=stack_engine_cpu`.
- Add regression coverage for CPU StackEngine-looking integration artifacts
  with DQ provenance but no embedded result contract.
- Generate a synthetic CPU audit and pixel-verifying pipeline-contract artifact
  under `C:\glass_runs\phase2_s2_gate_168_pipeline_result_contract`.

### S2-Gate 169: Resident CUDA Result Contract Audit

- Add `glass resident-result-contract` to audit resident CUDA integration
  outputs without rerunning image processing.
- Validate resident identity, required output map paths, DQ summary presence,
  resident DQ provenance schema, DQ summary/provenance agreement, active-frame
  counts, coverage provenance, source terms, and geometric warp coverage
  frame-count agreement.
- Support optional tiled FITS pixel verification for DQ/count maps, with tests
  covering passing and mismatched summaries on tiny synthetic maps.
- Run the JSON-only audit against the Gate160 `throughput-v1` resident run under
  `C:\glass_runs\phase2_s2_gate_169_resident_result_contract`.
- Current real artifact result: passed, with one H output, active frame count
  `193`, input frame count `200`, and nine resident output checks.

### S2-Gate 170: Pipeline Contract Exposes Resident Result Contract

- Extend `glass pipeline-contract` so resident CUDA integration rows expose a
  `resident_result_contract` summary.
- Add `integration_resident_result_contract`: resident CUDA outputs must satisfy
  the resident result-contract audit.
- Reuse the S2-Gate169 contract logic in JSON-only mode inside pipeline-contract
  so normal pipeline audits do not perform extra large FITS reads unless pixel
  verification is explicitly requested elsewhere.
- Add tests for passing resident outputs and resident outputs with missing
  source-term provenance.
- Run the updated pipeline-contract against the Gate160 `throughput-v1` resident
  run under `C:\glass_runs\phase2_s2_gate_170_pipeline_resident_contract`.

### S2-Gate 171: Acceptance Audit Requires Pipeline Contract Evidence

- Extend `glass acceptance-audit` with optional `--pipeline-contract-json`.
- When supplied, require the referenced audit to exist, identify as
  `pipeline_invariant_contract`, and pass all pipeline-contract checks.
- Expose the pipeline-contract status, failed checks, integration summary, and
  pixel-verification summary in the acceptance JSON/Markdown.
- Add tests for passing and failing pipeline-contract artifacts without changing
  the default acceptance path when the option is omitted.
- Run the updated acceptance audit against the Gate160 `throughput-v1` resident
  run and Gate170 pipeline contract under
  `C:\glass_runs\phase2_s2_gate_171_acceptance_pipeline_contract`.
- Current real artifact result: passed, with 92 acceptance checks, pipeline
  contract status `passed`, zero failed pipeline checks, and the same measured
  `46.82815250883293x` speedup versus the black-box reference.

### S2-Gate 172: Benchmark Contract Requires Pipeline Contract Evidence

- Extend benchmark contracts with a `pipeline_contract` requirement block.
- Add contract checks for pipeline-contract presence, audit type, pass status,
  minimum check count, required check names, and absence of failed checks.
- Update the M38 200-light release contracts so a release-grade acceptance audit
  cannot pass without a passing `pipeline_invariant_contract` artifact.
- Extend candidate runtime sweep plans with a `pipeline_contract` command between
  compare and acceptance, and pass its JSON into `acceptance-audit`.
- Keep the runtime sweep executor compatible with older plans that lack the new
  step while executing the step for new plans.
- Run the updated contract against the Gate160 `throughput_v1` resident run under
  `C:\glass_runs\phase2_s2_gate_172_release_contract_pipeline`.
- Current real artifact result: passed, with 98 acceptance checks, all six
  benchmark pipeline-contract checks passing, and dry-run sweep execution
  showing the new `pipeline_contract` step before `acceptance_audit`.

### S2-Gate 173: Release Evidence Report Surface

- Add `release_contract_evidence.pipeline_contract` to acceptance-audit JSON so
  release-grade pipeline-contract evidence is a stable summary, not only a set
  of individual checks.
- Extend acceptance Markdown with a `Pipeline Contract Evidence` section showing
  required-by-contract status, pipeline-contract path, pass state, check counts,
  and all pipeline-related acceptance checks.
- Extend HTML reports with a `Release contract evidence` section immediately
  after benchmark comparison, showing pipeline-contract release evidence even
  when all checks pass.
- Keep failed-check tables unchanged; this gate adds positive evidence
  visibility for green release candidates.
- Run the updated acceptance audit and HTML report over the Gate160
  `throughput_v1` resident run under
  `C:\glass_runs\phase2_s2_gate_173_release_evidence_report`.
- Current real artifact result: passed, with release evidence status `passed`,
  `2` direct pipeline checks, `6` benchmark pipeline checks, `0` failed
  pipeline checks, and visible Markdown/HTML evidence rows.

### S2-Gate 174: StackEngine Adoption Evidence

- Extend `glass stack-engine-contract` with a StackEngine adoption summary that
  classifies each audited surface by engine family, result-contract readiness,
  fallback status, and Phase 2 default-readiness gap reason.
- Preserve resident CUDA acceptance: integration-only audits may still pass with
  `--expected-integration-engine cuda_resident_stack`, while adoption evidence
  records the remaining `resident_cuda_surface` gap before CPU StackEngine can be
  declared the default across all audited surfaces.
- Surface adoption counts and recommendations in Markdown and HTML reports,
  including `stack_engine_default_ready`, `resident_cuda_surfaces_remain`, and
  `stack_engine_contract_gaps_remain`.
- Add regression coverage for all-ready CPU StackEngine surfaces, legacy/fallback
  surfaces, missing result contracts, and resident CUDA integration adoption gaps.
- Run the adoption audit against the Gate160 `throughput_v1` resident run under
  `C:\glass_runs\phase2_s2_gate_174_stack_engine_adoption`.
- Current real artifact result: stack-engine contract passed for resident CUDA
  integration, with `1` resident CUDA surface, `0` StackEngine CPU surfaces,
  `1` Phase 2 default gap, and recommendation `resident_cuda_surfaces_remain`.

### S2-Gate 175: StackEngine Default Promotion Guard

- Add a `default_promotion` block to `glass stack-engine-contract` output.
- Require all of the following before a run is considered ready for full
  StackEngine default promotion: `scope=all`, at least one calibration master
  surface, at least one integration surface, passing StackEngine contract checks,
  zero Phase 2 StackEngine default gaps, and adoption recommendation
  `stack_engine_default_ready`.
- Add `glass stack-engine-contract --require-default-ready`, returning exit code
  `3` when the contract itself passes but the default-promotion guard is blocked.
- Add `glass guardrails --require-stack-default-ready`, so release/CI guardrails
  can fail on nonzero StackEngine default gaps instead of only reporting them.
- Surface default-promotion readiness, status, blocker count, and blocker rows in
  HTML reports.
- Add tests for ready CPU StackEngine promotion, resident CUDA integration
  blocked promotion, guardrails success with the requirement enabled, and HTML
  rendering of promotion blockers.
- Run a small synthetic CPU ready artifact and a Gate160 resident CUDA blocked
  artifact under `C:\glass_runs\phase2_s2_gate_175_default_promotion_guard`.
- Current artifact result: CPU StackEngine run passed with default promotion
  `ready=true`; Gate160 resident CUDA integration contract still passed, but
  `--require-default-ready` returned `3` with blockers `scope_not_all`,
  `missing_calibration_surface`, `phase2_stack_engine_default_gaps`, and
  `adoption_recommendation_not_ready`.

### S2-Gate 176: Release Contract Requires StackEngine Default Promotion

- Extend benchmark contracts with a `stack_engine_default_promotion` requirement
  block.
- Add benchmark checks for StackEngine contract presence, audit type, pass
  status, default-promotion readiness, scope, adoption recommendation, default
  gap count, blocker count, and failed contract checks.
- Extend `glass acceptance-audit` with `--stack-engine-contract-json` and embed
  `stack_engine_contract` plus
  `release_contract_evidence.stack_engine_default_promotion` in acceptance JSON
  and Markdown.
- Extend HTML reports so release contract evidence includes both pipeline
  contract evidence and StackEngine default-promotion evidence.
- Update candidate runtime sweep plans to generate `glass stack-engine-contract`
  artifacts and pass them into `acceptance-audit`; keep the sweep executor
  compatible with older plans that lack this step.
- Update the M38 200-light release benchmark contracts so release-grade
  acceptance cannot pass while `default_promotion.ready` is false.
- Run the updated acceptance audit against the Gate160 resident CUDA run with
  Gate170 pipeline contract and Gate175 StackEngine contract under
  `C:\glass_runs\phase2_s2_gate_176_release_stack_default_contract`.
- Current real artifact result: acceptance fails only on StackEngine
  default-promotion checks while retaining the measured `46.82815250883293x`
  speedup and passing pipeline-contract evidence. The failure is intentional:
  the current resident run is fast and pipeline-valid, but not yet eligible to
  be advertised as full StackEngine default.

### S2-Gate 177: Resident Result-Contract Parity In StackEngine Audit

- Extend `glass stack-engine-contract` with optional
  `--resident-result-contract-json`.
- When a resident CUDA integration output has a matching passing resident
  result-contract entry, mark its `resident_result_contract_passed` and
  `result_contract_passed` fields true.
- Treat resident CUDA integration surfaces with passing resident result-contract
  parity as StackEngine-contract-ready for adoption purposes, while preserving
  default-promotion blockers for non-`all` scope and missing calibration
  surfaces.
- Surface resident result-contract parity in StackEngine JSON, Markdown, and
  HTML reports.
- Update candidate runtime sweep plans to generate `resident-result-contract`
  artifacts before `stack-engine-contract` and pass them through with
  `--resident-result-contract-json`; keep older plans compatible.
- Run the updated StackEngine audit against the Gate160 resident CUDA run with
  Gate169 resident result-contract evidence under
  `C:\glass_runs\phase2_s2_gate_177_resident_stack_parity`.
- Current real artifact result: resident integration StackEngine contract passed
  with resident result-contract parity, adoption gap count fell from `1` to `0`,
  and release acceptance failed on only the remaining scope/calibration
  promotion blockers instead of the previous resident CUDA surface gap.

### S2-Gate 178: Resident Calibration-Contract Parity In StackEngine Audit

- Add `glass resident-calibration-contract`, auditing resident CUDA
  `resident_artifacts.json` for master-calibration evidence: resident artifact
  presence, master set records, bias/dark/flat source counts, master statistics,
  cache file presence, light frame IDs, calibration timing, and downstream
  resident master output existence.
- Extend `glass stack-engine-contract` with optional
  `--resident-calibration-contract-json`, converting a passing resident
  calibration contract into a resident CUDA master-calibration surface.
- With both resident calibration-contract and resident result-contract parity
  attached, resident CUDA runs can satisfy all-surface StackEngine default
  promotion without fabricating a legacy `calibration_artifacts.json`.
- Update candidate runtime sweep plans/executor so each candidate emits
  `resident-calibration-contract` before `resident-result-contract` and
  `stack-engine-contract`, passing both resident contract JSON files into the
  StackEngine audit.
- Surface resident calibration-contract attachment and per-surface status in
  StackEngine JSON, Markdown, and HTML reports.
- Run the updated resident calibration/result/StackEngine/acceptance chain
  against the Gate160 200-light resident CUDA run under
  `C:\glass_runs\phase2_s2_gate_178_resident_calibration_parity`.
- Current real artifact result: resident calibration contract passed, resident
  result contract passed, StackEngine contract passed with
  `default_promotion.ready=true`, and release acceptance passed with the
  measured `46.82815250883293x` speedup and zero StackEngine default-promotion
  blockers.

### S2-Gate 179: Release Promotion Decision Audit

- Add `glass release-promotion-decision`, a machine-readable decision artifact
  for the point after release acceptance passes but before runtime/default
  settings are promoted.
- The decision separates `release_candidate_ready` from
  `default_change_ready`. Release-candidate readiness requires passing
  acceptance, speedup threshold, pipeline release evidence, StackEngine release
  evidence, StackEngine default readiness, and `scope=all`.
- Default-change readiness additionally requires stable repeat/runtime evidence:
  at least the configured minimum completed runtime observations, a non-repeat
  recommendation from `resident-runtime-compare`, and a bounded slowest/best
  elapsed-time ratio.
- Optional `resident-runtime-repeat-preflight` evidence is recorded so a busy
  GPU or low free VRAM can explain why repeat benchmarking should wait instead
  of silently promoting defaults.
- Add CLI strict mode with `--fail-on-not-ready` for CI/release guard usage.
- Run the decision audit against the Gate178 passed release artifact,
  Gate178 StackEngine contract, Gate170 pipeline contract, Gate161 runtime
  comparison, and Gate164 repeat preflight under
  `C:\glass_runs\phase2_s2_gate_179_release_promotion_decision`.
- Current real artifact result: `release_candidate_ready=true`,
  `default_change_ready=false`, recommendation `wait_for_controlled_window`,
  measured speedup `46.82815250883293x`, runtime comparison recommendation
  `repeat_with_warm_cache_or_dedicated_io_window`, slowest/best elapsed ratio
  `1.364279174741225`, and preflight GPU status `busy`.

### S2-Gate 180: Controlled Repeat Benchmark Promotion Evidence

- Execute the Gate162 three-run resident repeat plan after a fresh
  `resident-runtime-repeat-preflight` reports `execute_repeat_plan`.
- Preserve repeat execution evidence under
  `C:\glass_runs\phase2_s2_gate_180_controlled_repeat` and the measured
  `resident-runtime-compare` artifact under
  `C:\glass_runs\phase2_s2_gate_162_repeat_plan\runtime_compare.json`.
- Extend `glass release-promotion-decision` with explicit
  `--ignore-warmup-runs`, recording ignored labels and using only the remaining
  observations for repeat stability. This keeps warm-up handling auditable
  instead of silently dropping outliers.
- Run release promotion decision twice:
  - without warm-up trimming, the first cold-cache repeat keeps
    `default_change_ready=false`;
  - with `--ignore-warmup-runs 1`, the second and third repeats satisfy runtime
    stability and strict `--fail-on-not-ready` passes.
- Current real artifact result: repeat execution completed 3/3 runs, best run
  `throughput_v1_repeat02` at `18.54452279999896 s`, third run
  `18.585318899999038 s`, first warm-up run `29.639423599999645 s`, post-warm-up
  slowest/best ratio `1.0021999002314625`, and final decision
  `default_change_ready=true` with recommendation `promote_default_candidate`.

### S2-Gate 181: Promote Resident Throughput Preset Default

- Promote `throughput-v1` from an opt-in resident CUDA runtime preset to the
  default for `glass run` and `glass audit`.
- Keep explicit `--resident-runtime-preset manual` as the legacy conservative
  resident schedule for diagnostics and fallback comparisons.
- Preserve user overrides: any explicitly supplied prefetch, worker, H2D,
  batch, wave, or release-mode option still wins over the preset defaults.
- Extend benchmark acceptance token-group checks so a defaulted runtime can be
  validated from `resident_artifacts.json` effective `resident_io_pipeline`
  fields, while individual required command-token checks remain strict.
- Run a no-preset 200-light resident CUDA benchmark under
  `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident`; the
  command contains no `--resident-runtime-preset`, but the effective runtime
  schedule records `prefetch_frames=12`, `prefetch_workers=7`,
  `h2d_mode=pinned_ring`, `calibration_batch_requested_frames=8`,
  `calibration_batch_requested_streams=4`,
  `calibration_wave_requested_frames=2`, and callback-queue release.
- Current real artifact result: default no-preset elapsed time
  `18.80478299999959 s`, compare coverage `0.9577924192878646`, RMS
  difference `0.0014945534429799121`, p99 absolute difference
  `0.00043544556712731865`, acceptance status `passed`, speedup
  `58.099101701945926x`, runtime slowest/best ratio `1.0140343433372492` with
  zero ignored warm-up runs, and release decision
  `default_change_ready=true` / recommendation `promote_default_candidate`.

### S2-Gate 182: Windows CUDA Release Matrix Guard

- Add `glass windows-release-matrix`, a release-readiness artifact that joins
  `glass doctor` CUDA/package compatibility evidence with the Gate181 release
  promotion decision and optional acceptance audit.
- Audit the planned Windows package set: `cuda13`, `cuda12`, `cuda11`, and CPU
  fallback. The matrix records package artifact names, compatibility state,
  native-cubin versus PTX-JIT match mode, release role, and recommended try
  order.
- Require the release machine to have CUDA available by default, while retaining
  `--allow-cpu-only` for documentation or CPU package dry-runs.
- Require `default_change_ready=true`, promotion recommendation
  `promote_default_candidate`, default resident preset `throughput-v1`, stable
  runtime repeat ratio, package recommendation presence, CPU fallback, and
  compatible CUDA 13/12/11 rows.
- Run the guard against the Gate181 doctor, acceptance, and release-decision
  artifacts under `C:\glass_runs\phase2_s2_gate_182_windows_release_matrix`.
- Current real artifact result: status `release_matrix_ready`, recommendation
  `publish_windows_cuda_matrix`, primary package `cuda13`, try order
  `cuda13,cuda12,cuda11,cpu`, `cuda13` native-cubin match, `cuda12` and `cuda11`
  PTX forward-JIT fallback matches, CPU fallback present, and zero failed
  checks.

### S2-Gate 183: Windows Portable Package Smoke

- Add `glass windows-package-smoke`, a package-level audit for Windows portable
  folders and their zip artifacts.
- Validate package structure: runtime `python.exe`, `glass.cmd`,
  `glass-doctor.cmd`, README, LICENSE, docs, source stamp, portable zip, and
  non-empty zip size.
- Execute package startup checks by default: `glass-doctor.cmd --json ...` and
  `glass.cmd --help`, recording return codes, output tails, generated doctor
  JSON, CUDA status, and package recommendation.
- Keep `--skip-exec` available for structure-only CI fixtures, while real
  release use should execute the package commands.
- Build a fresh CPU portable package with
  `packaging\windows\build_portable.ps1 -Python .\.venv\Scripts\python.exe`.
- Run package smoke against `.release\windows\GLASS` and
  `.release\windows\GLASS-Portable-win64.zip` under
  `C:\glass_runs\phase2_s2_gate_183_windows_package_smoke`.
- Current real artifact result: status `package_smoke_passed`, recommendation
  `portable_package_ready_for_next_release_step`, zip size `290938309` bytes,
  source stamp `4b54e77`, `glass-doctor.cmd` return code `0`, `glass.cmd --help`
  return code `0`, CPU portable CUDA availability `false`, and zero failed
  checks.

### S2-Gate 184: CUDA13 Portable Package Smoke

- Extend the Windows portable builder with `-PackageLabel`, package manifest
  emission, isolated `PYTHONNOUSERSITE=1` launchers, and automatic Visual
  Studio C++ environment import through `vswhere.exe`/`vcvars64.bat` when
  `cl.exe` is not already on `PATH`.
- Write `package_manifest.json` without UTF-8 BOM and make GLASS JSON reads
  tolerant of BOM-marked JSON generated by older tools.
- Extend `glass windows-package-smoke` with package-label checks and a
  `--require-cuda` gate that requires package manifest `build_cuda=true` and a
  CUDA-capable portable doctor result.
- Build a fresh CUDA 13 portable package with
  `packaging\windows\build_portable.ps1 -Python .\.venv\Scripts\python.exe
  -BuildCuda -StaticCudaRuntime -CudaArchitectures native -PackageLabel cuda13`.
- Run CUDA-required package smoke against `.release\windows\GLASS` and
  `.release\windows\GLASS-Portable-win64-cuda13.zip` under
  `C:\glass_runs\phase2_s2_gate_184_cuda13_package_smoke` and mirror the JSON
  and Markdown artifacts into `runs\checkpoints`.
- Current real artifact result: status `package_smoke_passed`, recommendation
  `portable_package_ready_for_next_release_step`, zip size `339732356` bytes,
  source stamp `245c2f9`, package label `cuda13`, manifest CUDA build `true`,
  portable CUDA availability `true`, native extension loaded `true`, GPU
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition` with compute capability
  `12.0` and `97886 MiB` VRAM, and zero failed checks.

### S2-Gate 185: Windows Package Build Plan

- Add `glass windows-package-build-plan`, a non-mutating preflight that plans
  Windows CPU/CUDA portable package variants from local CUDA Toolkit
  availability.
- The plan records requested labels, detected Toolkit roots, nvcc presence,
  package zip paths, package-root reuse, CMake CUDA architecture strings,
  ready/missing variants, and copy-pasteable `build_portable.ps1` commands.
- Support `--toolkit-root LABEL=PATH` overrides, `--packages`, release-root and
  Python overrides, static/shared CUDA runtime planning, and strict
  `--fail-on-missing` / `--require-all-toolkits` modes.
- Run the preflight on the local release machine and write artifacts under
  `C:\glass_runs\phase2_s2_gate_185_windows_package_build_plan` and
  `runs\checkpoints`.
- Current real artifact result: status `partial_toolkits`, passed `true`,
  ready variants `cuda13,cpu`, missing CUDA variants `cuda12,cuda11`, detected
  Toolkit `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2`, cuda13
  match `major_compatible`, and recommendation
  `build_ready_variants_and_install_missing_toolkits`.

### S2-Gate 186: Minimal CUDA Toolkit Installer Plan

- Add `packaging\windows\install_cuda_toolkit_minimal.ps1`, a driver-safe
  helper for CUDA12/CUDA11 Toolkit preparation.
- The helper defaults to `plan_only`; explicit `-Download` or `-Install` is
  required for external actions.
- The helper records installer URL, expected SHA256, target Toolkit root,
  planned components, and `driver_component_included=false`.
- Planned components are limited to `nvcc_12.4`/`cudart_12.4` and
  `nvcc_11.8`/`cudart_11.8`.
- Extend `glass windows-package-build-plan` so missing `cuda12` and `cuda11`
  rows include read-only download and install commands for the minimal helper.
- Run plan-only artifacts for `cuda12` and `cuda11` under
  `C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer` and mirror
  them into `runs\checkpoints`.
- Current real artifact result: both Toolkit helper artifacts report
  `status=plan_only`, `install_requested=false`, `download_requested=false`,
  `driver_component_included=false`, and the refreshed package build plan still
  reports ready variants `cuda13,cpu` with missing variants `cuda12,cuda11`.

### S2-Gate 187: CUDA12 Minimal Toolkit Install

- Use the Gate186 minimal installer helper to download and install CUDA12
  Toolkit components needed for release-package compilation.
- Download `cuda_12.4.1_551.78_windows.exe` with BITS, verify SHA256
  `7d20c5eb186e4d3c64680fe5096bed05926aea89754192102323c956c26244de`, then
  install only `nvcc_12.4` and `cudart_12.4`.
- Confirm `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin\nvcc.exe`
  reports CUDA compilation tools `V12.4.131`.
- Confirm `cuda_runtime.h`, `cudart.lib`, and `cudart64_12.dll` exist under
  the CUDA12 Toolkit root.
- Confirm `nvidia-smi` still reports driver `596.21` after install.
- Refresh `glass windows-package-build-plan`; current result reports ready
  variants `cuda13,cuda12,cpu`, missing variant `cuda11`, and CUDA12 Toolkit
  match `exact`.

### S2-Gate 188: CUDA12 Portable Package Smoke

- Build `GLASS-Portable-win64-cuda12.zip` using CUDA Toolkit 12.4 and the
  Gate187 build-plan command.
- Build settings: `-PackageLabel cuda12`, `-BuildCuda`,
  `-StaticCudaRuntime`, `-CudaArchitectures "75;80;86;89;90"`, and
  `-CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"`.
- Package manifest records package label `cuda12`, CUDA Toolkit root `v12.4`,
  architecture string `75;80;86;89;90`, runtime linkage `Static`, and source
  stamp `fbf454a`.
- Run `glass windows-package-smoke` with `--expected-package-label cuda12`,
  `--expected-source fbf454a`, and `--require-cuda`.
- Current real artifact result: status `package_smoke_passed`, recommendation
  `portable_package_ready_for_next_release_step`, zip size `341206870` bytes,
  native extension loaded, CUDA available on RTX PRO 6000 Blackwell cc 12.0,
  driver `596.21`, and zero failed checks.

### S2-Gate 189: CUDA11 Minimal Toolkit Install

- Use the Gate186 minimal installer helper to download and install CUDA11
  Toolkit components needed for release-package compilation.
- Download `cuda_11.8.0_522.06_windows.exe` with BITS, verify SHA256
  `b70f38f27321c0a53993438a91970a2e3c426f46da4c42eceff1eeea031a6555`, then
  install only `nvcc_11.8` and `cudart_11.8`.
- Confirm `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\nvcc.exe`
  reports CUDA compilation tools `V11.8.89`.
- Confirm `cuda_runtime.h`, `cudart.lib`, and `cudart64_110.dll` exist under
  the CUDA11 Toolkit root.
- Confirm `nvidia-smi` still reports driver `596.21` after install.
- Refresh `glass windows-package-build-plan --fail-on-missing`; current result
  reports status `build_plan_ready`, ready variants `cuda13,cuda12,cuda11,cpu`,
  no missing CUDA variants, and recommendation `build_all_variants`.

### S2-Gate 190: CUDA11 Portable Package Smoke

- Build `GLASS-Portable-win64-cuda11.zip` using CUDA Toolkit 11.8 and the
  Gate189 build-plan command.
- Build settings: `-PackageLabel cuda11`, `-BuildCuda`,
  `-StaticCudaRuntime`, `-CudaArchitectures "50;52;60;61;70;75;80;86"`, and
  `-CudaToolkitRoot "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"`.
- Package manifest records package label `cuda11`, CUDA Toolkit root `v11.8`,
  architecture string `50;52;60;61;70;75;80;86`, runtime linkage `Static`, and
  source stamp `260c832`.
- Run `glass windows-package-smoke` with `--expected-package-label cuda11`,
  `--expected-source 260c832`, and `--require-cuda`.
- Current real artifact result: status `package_smoke_passed`, recommendation
  `portable_package_ready_for_next_release_step`, zip size `342183616` bytes,
  native extension loaded, CUDA available on RTX PRO 6000 Blackwell cc 12.0,
  driver `596.21`, and zero failed checks.

### S2-Gate 191: Labeled CPU Portable Package Smoke

- Build `GLASS-Portable-win64-cpu.zip` with `-PackageLabel cpu`.
- Package manifest records package label `cpu`, `build_cuda=false`, and source
  stamp `a1604b0`.
- Run `glass windows-package-smoke` with `--expected-package-label cpu` and
  `--expected-source a1604b0`.
- Current real artifact result: status `package_smoke_passed`, recommendation
  `portable_package_ready_for_next_release_step`, zip size `296215418` bytes,
  CPU package startup passed, and zero failed checks.

### S2-Gate 192: Windows Package Suite Readiness

- Add `glass windows-package-suite`, which aggregates labeled package smoke
  artifacts for `cuda13`, `cuda12`, `cuda11`, and `cpu` into one publish
  readiness artifact.
- Validate smoke presence, smoke pass status, package-label agreement, and
  non-empty zip size for every required label.
- Keep same-source-stamp checking optional with `--require-same-source-stamp`
  because the current historical package set was built across several gate
  commits; formal release packages should normally be rebuilt from one final
  tag or commit.
- Current real artifact result: status `package_suite_ready`, recommendation
  `publish_package_suite`, source stamps `245c2f9,260c832,a1604b0,fbf454a`,
  zip sizes `339732356`, `341206870`, `342183616`, and `296215418` bytes, and
  zero failed checks.

### S2-Gate 193: Windows Release Manifest

- Add `glass windows-release-manifest`, which consumes the Gate192 suite
  artifact, reads the release zip files, and records package size plus SHA256
  for every package label.
- Validate that the suite passed, every referenced zip exists and is non-empty,
  zip sizes match the smoke artifacts, each suite row passed, and each SHA256
  digest is recorded.
- Keep `--require-same-source-stamp` optional so historical multi-gate package
  sets can be archived while final release automation can enforce one source
  tag.
- Current real artifact result: status `release_manifest_ready`,
  recommendation `ready_for_upload`, package count `4`, and zero failed checks.

### S2-Gate 194: Strict Same-Source Windows Packages

- Rebuild `cuda13`, `cuda12`, `cuda11`, and `cpu` Windows portable packages
  from current source stamp `aa63510`.
- Smoke-test every freshly rebuilt package immediately after its build, because
  the shared portable package root is overwritten by the next variant.
- Generate strict package-suite and release-manifest artifacts with
  `--require-same-source-stamp`.
- Current real artifact result: strict suite status `package_suite_ready`,
  strict manifest status `release_manifest_ready`, source stamps `aa63510`,
  package count `4`, and zero failed checks.

### S2-Gate 195: GitHub Release Handoff Plan

- Add `glass windows-github-release-plan`, which converts a strict Windows
  release manifest into GitHub release notes, an asset table, and a `gh release
  create` command.
- Keep publishing explicit: the command does not create tags, push commits,
  upload assets, or publish a release.
- Record whether GitHub CLI is available when `--check-gh` is supplied.
- Current real artifact result: status `release_plan_ready`, tag
  `v0.1.0-windows-gpu.9`, package count `4`, source stamp `aa63510`, and
  `publication_ready=false` because `gh` is not installed on the checkpoint
  machine.

### S2-Gate 196: GitHub CLI Auth Preflight

- Extend `glass windows-github-release-plan` with `--gh-path` and
  `--check-gh-auth` so release readiness can distinguish an installed GitHub
  CLI from an authenticated GitHub CLI.
- Install GitHub CLI 2.94.0 locally with winget and rerun the release handoff
  plan against the strict same-source manifest.
- Keep asset checks green while marking `publication_ready=false` when
  `gh auth status` fails.
- Current real artifact result: status `release_plan_ready`, package count `4`,
  `gh.available=true`, `gh.auth_ok=false`, and recommendation
  `authenticate_github_cli_then_run_release_command`.

### S2-Gate 197: Windows GitHub Release Script

- Extend `glass windows-github-release-plan` with `--script` to emit a
  PowerShell release script from the strict Windows release manifest.
- Keep the generated script dry-run by default; require `-Publish` before it
  calls `gh release create`.
- Have the script verify GitHub CLI authentication, asset existence, recorded
  file sizes, SHA256 hashes, and release notes presence before upload.
- Record the script path and dry-run publication mode in the JSON release plan.
- Current real artifact result: status `release_plan_ready`, package count `4`,
  `publication_ready=false` because `gh auth status` still fails locally, and
  a generated publish script is ready for use once GitHub CLI authentication is
  completed.

### S2-Gate 198: Guardrails Acceptance Contract Bundle

- Extend `glass guardrails` so every guardrail run emits
  `acceptance_contract_bundle.json` alongside StackEngine contract, pipeline
  contract, Markdown summaries, and the HTML report.
- Record the contract bundle path in `guardrails_summary.json`.
- Include an acceptance-audit argument vector and map for
  `--pipeline-contract-json` and `--stack-engine-contract-json` so 200-light
  release checks can consume the exact generated contracts without hand
  assembling paths.
- Preserve existing guardrail pass/fail behavior and keep the bundle available
  for failed guardrail runs as diagnostic evidence.
- Current real artifact result: a synthetic CPU audit run produced passing
  StackEngine and pipeline contracts, `stack_default_promotion.ready=true`, and
  a passing `glass_acceptance_contract_bundle` under the Gate198 checkpoint.

### S2-Gate 199: Acceptance Audit Contract Bundle Ingestion

- Add `glass acceptance-audit --contract-bundle` support so a guardrails
  `acceptance_contract_bundle.json` can supply the generated pipeline and
  StackEngine contract paths.
- Keep explicit `--pipeline-contract-json` and `--stack-engine-contract-json`
  as higher priority overrides.
- Record contract-bundle evidence in the acceptance audit JSON and Markdown.
- Fail clearly when a requested bundle path is missing or is not a
  `glass_acceptance_contract_bundle` artifact.
- Current real artifact result: a Gate198 synthetic guardrails bundle was
  consumed by `glass acceptance-audit --contract-bundle`, producing a passing
  acceptance audit with both pipeline and StackEngine contract checks active.

### S2-Gate 200: Real 200-Light Bundle Acceptance

- Extend `glass guardrails` with optional
  `--resident-calibration-contract-json` and
  `--resident-result-contract-json` so resident CUDA guardrail bundles can carry
  the same calibration/result contracts used by StackEngine default-promotion
  audits.
- Record resident contract inputs and attachment status in
  `guardrails_summary.json` and `acceptance_contract_bundle.json`.
- Rebuild guardrails for the Gate181 M38 H-alpha 200-light resident CUDA run
  using its resident calibration and result contracts.
- Run `glass acceptance-audit --contract-bundle` against the real 200-light
  manifest, GLASS run, WBPP black-box timing, reference comparison, and
  `benchmarks/phase2_m38_h_200_contract.json`.
- Current real artifact result: acceptance status `passed`, speedup versus
  WBPP `58.099101701945926x`, frame counts `200/20/20/20`, active frames `193`,
  coverage fraction `0.9577924192878646`, StackEngine default promotion
  `ready=true`, and both contract-bundle checks passed.

### S2-Gate 201: Resident Bundle Contract Enforcement

- Make `glass acceptance-audit --contract-bundle` validate resident CUDA
  calibration and resident CUDA result contracts when a guardrails bundle
  declares them.
- Record resident contract path, existence, artifact type, status, pass/fail,
  output count, check count, and failed checks in the acceptance audit JSON.
- Add blocking checks for resident contract presence, expected artifact type,
  and `passed=true`.
- Surface resident bundle contracts in the acceptance-audit Markdown summary.
- Validate with direct acceptance-audit tests and rerun the real Gate200
  200-light acceptance bundle as a read-only artifact audit.

### S2-Gate 202: Acceptance Bundle Schema Audit

- Add a formal schema/version audit for `glass_acceptance_contract_bundle`
  artifacts consumed by `glass acceptance-audit --contract-bundle`.
- Require schema version `1`, purpose `acceptance_audit_contract_inputs`,
  required artifact keys, and required acceptance-audit argument-map keys.
- Keep historical diagnostic bundles compatible by auditing schema shape
  separately from the bundle's own `passed` status.
- Record `contract_bundle_schema` in acceptance-audit JSON and Markdown.
- Validate with passing and malformed bundle tests plus the real 200-light
  Gate200 bundle artifact.

### S2-Gate 203: Phase 2 Handoff Status Index

- Add `glass phase2-status`, a compact handoff artifact that summarizes the
  latest Phase 2 checkpoint, optional 200-light acceptance audit, CUDA doctor
  state, Windows release manifest, and GitHub release plan.
- Emit machine-readable JSON and optional Markdown.
- Keep the command read-only and artifact-driven; it must not rerun image
  processing or modify input data.
- Validate command help, direct report tests, and a real handoff summary from
  the latest checkpoints and release artifacts.

### S2-Gate 204: Phase 2 Handoff Regression Guard

- Add `glass phase2-status-compare`, a read-only comparison artifact for two
  `glass_phase2_status` JSON files.
- Flag regressions in latest checkpoint gate/status, overall green status,
  acceptance audit pass/status, CUDA availability, Windows release-manifest
  readiness, and GitHub release-plan readiness.
- Emit machine-readable JSON and optional Markdown.
- Support `--fail-on-regression` for CI/handoff guard usage.
- Validate with passing, failing, and CLI-output tests plus a real comparison
  between the previous and current Phase 2 handoff artifacts.

### S2-Gate 205: Release Plan Phase 2 Preflight

- Extend `glass windows-github-release-plan` with optional `--phase2-status`
  and `--phase2-status-compare` evidence inputs.
- Require supplied Phase 2 status artifacts to be structurally correct and
  green/passed before the release plan can pass.
- Include Phase 2 preflight evidence in release-plan JSON, Markdown, release
  notes, and generated PowerShell publish scripts.
- Keep publication explicit: the script remains dry-run by default and still
  requires `-Publish` before calling GitHub CLI.
- Validate with passing/failing preflight tests and a real release-plan
  artifact using the latest Gate204 handoff status and regression comparison.

### S2-Gate 206: Master Calibration Surface Contract

- Harden the StackEngine default contract for master bias/dark/flat surfaces
  so a master frame is not accepted merely because it used the expected engine.
- Require local master calibration records to expose an existing output path,
  finite `min/max/mean/median/std` statistics, tile size, master rejection
  policy, and type-specific calibration semantics such as dark bias semantics
  and flat per-frame normalization metadata.
- Keep resident CUDA master calibration compatible through the attached
  `resident_cuda_calibration_contract`, which remains the authoritative
  resident surface audit.
- Surface failures as `calibration_masters_science_auditable` and
  `master_calibration_science_contract_failed` so release guardrails can point
  at missing stats/semantics instead of reporting a generic StackEngine gap.

### S2-Gate 207: Calibration Pipeline Contract

- Extend `glass pipeline-contract` so `calibration_artifacts.json`, when
  present, participates in the same pipeline invariant audit as warp, local
  normalization, integration maps, and DQ maps.
- Reuse the master calibration surface contract introduced in Gate206 for
  local master bias/dark/flat records.
- Add calibrated-light DQ contract rows requiring calibrated image path,
  DQ mask path, DQ summary with valid-pixel accounting, tile count, and tile
  size.
- Keep integration-only diagnostic fixtures compatible by making calibration
  checks active only when `calibration_artifacts.json` exists.
- Surface calibration master and calibrated-light rows in the HTML report's
  Pipeline contract audit section.

### S2-Gate 208: Resident Calibration Release Contract Bridge

- Extend `glass pipeline-contract` with
  `--resident-calibration-contract-json` so resident CUDA runs without
  `calibration_artifacts.json` can still expose calibration surface evidence
  in the unified pipeline invariant audit.
- Have `glass guardrails` pass the attached resident calibration contract into
  both StackEngine and pipeline contract audits.
- Add `resident_calibration_surface_contract` rows and checks to the pipeline
  contract while preserving local CPU calibration checks from Gate207.
- Harden `benchmarks/phase2_m38_h_200_contract.json` so the 200-light
  acceptance contract requires calibration master surface evidence and resident
  calibration surface evidence in addition to resident integration evidence.
- Keep this gate contract-only: no image processing algorithm changes and no
  new algorithm-source entry required.

### S2-Gate 209: Native Resident Calibration Artifact

- Make resident CUDA runs write a first-class `calibration_artifacts.json`
  alongside `resident_artifacts.json`.
- Represent resident master bias/dark/flat surfaces with explicit
  `cuda_resident_stack` backend, cache path, stats, dark/bias semantics,
  flat normalization semantics, full-frame resident tile scope, and embedded
  resident master-surface contracts.
- Represent resident light calibration as per-frame `resident_in_vram` ledger
  rows instead of pretending calibrated FITS/DQ-mask files exist on disk.
- Extend `glass pipeline-contract` so resident-native calibration artifacts use
  `resident_calibrated_lights_present` and
  `resident_calibrated_light_contract`, while CPU/out-of-core calibrated FITS
  rows still use `calibrated_light_dq_contract`.
- Extend StackEngine contract handling so native resident calibration master
  rows count as CUDA resident StackEngine-family surfaces when their embedded
  resident master contracts and science metadata pass.
- Keep this gate artifact-only: no image processing algorithm changes and no
  new algorithm-source entry required.

### S2-Gate 210: Native Resident Calibration Reporting

- Surface native resident calibration artifact evidence in
  `frame_accounting.json` summary and per-frame rows.
- Add an HTML report section for resident calibration artifacts, including
  resident master surfaces and per-light in-VRAM ledger rows.
- Include native resident calibration evidence in `glass guardrails` summaries
  and acceptance bundles.
- Keep this gate reporting/accounting only: no image processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 211: Native Resident Result Contract Artifact

- Make resident CUDA runs write a first-class `resident_result_contract.json`
  after `integration_results.json`.
- Register the native resident result contract in `run_state.json` artifacts.
- Let StackEngine contract audits auto-discover
  `RUN/resident_result_contract.json` when no explicit
  `--resident-result-contract-json` is supplied.
- Let `glass guardrails` auto-discover and bundle the native resident result
  contract path, while preserving explicit-path override behavior.
- Keep this gate artifact/contract only: no image processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 212: Runtime Sweep Uses Native Guardrails Bundle

- Update generated candidate runtime sweep plans so new resident CUDA variants
  use one `glass guardrails` command instead of separate resident
  calibration/result bridge-contract commands.
- Make generated acceptance-audit commands consume the guardrails
  `acceptance_contract_bundle.json`, allowing the bundle to carry the
  run-default native `resident_result_contract.json`.
- Record run-local `resident_result_contract.json` and
  `calibration_artifacts.json` as native variant artifacts in the plan.
- Preserve execution compatibility with older plans that still contain
  separate resident calibration/result, StackEngine, and pipeline contract
  commands.
- Keep this gate planning/orchestration only: no image processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 213: Native Guardrails Bundle Release Provenance

- Surface native guardrails-bundle provenance in acceptance-audit JSON and
  Markdown, including resident result contract source/path, run-default
  discovery status, native resident calibration artifact presence, master
  count, and resident calibrated-light count.
- Propagate the same provenance through `glass phase2-status` so handoff
  status artifacts can be consumed without reparsing acceptance audit internals.
- Include native resident contract source and native calibration artifact
  counts in Windows GitHub release plan notes and preflight Markdown when a
  Phase 2 status artifact is supplied.
- Keep this gate reporting/release-handoff only: no image processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 214: Resident Registration Fast-Path Acceptance Contract

- Add a benchmark-contract section that verifies the resident CUDA
  `similarity_cuda_triangle` fast path is actually active in real runs.
- Require descriptor-fit batching, shared reference/moving/output device buffer
  reuse, batch pixel refinement, native matrix-Lanczos warp batching,
  asynchronous resident warp copy mode, positive warp scratch allocation, and
  required registration component timing rows.
- Surface the collected fast-path evidence in acceptance-audit JSON and
  Markdown so release handoff cannot silently pass if resident registration
  falls back to slower per-frame orchestration.
- Update the M38 H-alpha 200-light benchmark contract with these requirements
  and validate it on the preserved real resident CUDA run.
- Keep this gate contract/reporting only: no image processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 215: Resident Registration Fast-Path Release Provenance

- Propagate resident registration fast-path evidence from acceptance-audit
  artifacts into Phase 2 status JSON and Markdown.
- Include fast-path status, contract status, contract check counts,
  descriptor-fit batching, device buffer reuse, pixel-refine batching,
  matrix-Lanczos warp batching, warp batch frame count, resident copy mode,
  and scratch allocation in Windows release handoff artifacts.
- Ensure generated GitHub release notes and preflight Markdown surface this
  evidence whenever a Phase 2 status artifact contains it.
- Keep this gate reporting/release-handoff only: no processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 216: Pipeline DQ Contract Handoff Provenance

- Add `glass phase2-status --pipeline-contract` so a green Phase 2 handoff can
  include the pipeline invariant contract as a first-class artifact.
- Summarize DQ/mask contract state in Phase 2 status JSON and Markdown,
  including integration output/map counts, DQ contract status, StackEngine and
  resident result-contract status, pixel-verification state, and DQ/coverage/
  rejection pixel-match checks.
- Preserve the pipeline contract in Phase 2 status comparisons so later gates
  cannot silently drop a previously passing DQ contract or pixel verification.
- Propagate this evidence into Windows GitHub release-plan JSON, Markdown, and
  generated release notes when a Phase 2 status artifact supplies it.
- Keep this gate reporting/release-handoff only: no processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 217: Release Promotion Requires Pipeline DQ Handoff

- Tighten `glass release-promotion-decision` so a top-level passed pipeline
  contract is not enough for release-candidate readiness.
- Require concrete pipeline DQ handoff evidence: pipeline invariant contract
  presence, integration DQ contract pass, StackEngine/resident result-contract
  pass, pixel verification enabled, and DQ/coverage/rejection pixel-match
  checks passing.
- Accept this evidence either from an explicit `--pipeline-contract` artifact
  or the pipeline-contract block embedded in the acceptance audit.
- Surface the normalized pipeline handoff evidence in release-promotion JSON
  and Markdown for later release matrix and default-promotion decisions.
- Keep this gate contract/reporting only: no processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 218: Controlled Runtime Repeat Default-Promotion Evidence

- Execute a real repeated 200-light resident CUDA benchmark from the accepted
  default resident configuration instead of relying on a dry-run runtime plan.
- Use `glass resident-runtime-repeat-plan`, `resident-runtime-repeat-preflight`,
  `resident-runtime-repeat-execute`, and `resident-runtime-compare` to produce
  auditable repeated timing evidence under a controlled GPU-ready preflight.
- Feed the resulting runtime-compare artifact into
  `glass release-promotion-decision` together with the real acceptance,
  StackEngine, and pipeline DQ contract artifacts.
- Promote the decision state from release-candidate-ready to
  default-change-ready only when repeated timing is stable, speedup remains
  above threshold, and pipeline DQ handoff checks still pass.
- Keep this gate validation/evidence only: no processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 219: Default-Change Decision Release Handoff

- Add `glass phase2-status --release-decision` so Phase 2 handoff artifacts
  consume the release-promotion decision generated from controlled runtime
  repeat evidence.
- Require supplied release decisions to be `default_change_ready` with
  `promote_default_candidate`; otherwise Phase 2 status is not green.
- Preserve default-change readiness and promotion recommendation in Phase 2
  status comparisons so later gates cannot silently drop the repeated runtime
  proof.
- Propagate release-decision and runtime-repeat evidence into Windows GitHub
  release-plan JSON, Markdown, and generated release notes.
- Keep this gate contract/reporting only: no processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 220: Default Promotion Manifest

- Add `glass default-promotion-manifest` to convert default-change-ready
  evidence into an explicit resident CUDA default-promotion contract.
- Require the release-promotion decision to be `default_change_ready` with
  `promote_default_candidate`, and require Phase 2 status to remain green with
  the same embedded decision.
- Verify stable runtime-repeat evidence, pipeline DQ/mask handoff, StackEngine
  and resident result contracts, pixel verification, resident calibration
  artifacts, and the 200-light resident calibrated frame count.
- When a doctor artifact is supplied, surface CUDA availability, native
  extension loading, Windows package primary selection, and CPU fallback order.
- Keep this gate reporting/release-handoff only: no processing algorithm
  changes and no new algorithm-source entry required.

### S2-Gate 221: Guarded Resident CUDA Default Route

- Promote `glass run` and the run portion of `glass audit` to the resident CUDA
  default route when `--backend auto` can use the native CUDA backend.
- Preserve CPU-only and partial-stage safety by falling back to tile mode when
  CUDA is unavailable, `--backend cpu` is explicit, a partial `--until-stage`
  is requested, or user-selected options are only supported by tile mode.
- Keep explicit user intent strict: `--memory-mode resident` still fails with a
  clear error if CUDA is unavailable or a non-CUDA backend is selected.
- Record the requested/effective backend and memory-mode resolution in
  `run_timing.json` so benchmark and release artifacts can prove whether the
  default path actually used resident CUDA or a documented fallback.
- Keep this gate execution-routing only: no processing algorithm changes and no
  new algorithm-source entry required.

### S2-Gate 222: Default Route Acceptance Evidence

- Teach the benchmark acceptance contract to treat explicit command tokens and
  audited runtime artifacts as equivalent evidence for execution-route tokens.
- Allow `--memory-mode resident` and `--backend cuda` requirements to be proven
  by `run_timing.json` and `execution_default_resolution` when Gate 221 selected
  the CUDA resident default route.
- Allow resident runtime preset requirements to be proven by run timing default
  metadata or resident I/O pipeline artifacts, and resident registration mode
  requirements to be proven by `resident_artifacts.json`.
- Keep scientific parameter requirements explicit: parameters such as
  `--flat-floor 0.05` are still required in the command unless a later gate adds
  a dedicated scientific-parameter artifact.
- Keep this gate release-contract only: no processing algorithm changes and no
  new algorithm-source entry required.

### S2-Gate 223: Fast-Path Contract Status Preservation

- Treat resident registration fast-path acceptance as required release evidence
  whenever the Phase 2 release decision is ready to promote the default
  candidate.
- Make `glass phase2-status` fail closed if the acceptance artifact has no
  resident registration fast-path contract checks, or if those checks did not
  pass, while preserving the existing CUDA/package/pipeline checks.
- Make `glass phase2-status-compare` detect evidence regressions where a
  baseline had `resident_registration_fastpath_contract_status=passed` and a
  candidate falls back to `not_requested`, `failed`, or a smaller contract check
  count.
- Use the preserved 200-light fast-path acceptance audit as the authoritative
  Phase 2 status input for release handoff; keep smaller default-route fixtures
  as behavioral tests rather than release-strength evidence.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 224: Default Route Supplemental Handoff Evidence

- Extend `glass phase2-status` with an optional
  `--default-route-acceptance-audit` input so release handoff can carry both the
  primary 200-light science/fast-path acceptance audit and the smaller guarded
  default-route acceptance audit.
- Summarize the default-route artifact separately as `default_route_acceptance`
  instead of weakening or replacing the primary `acceptance_audit`.
- Require the default-route artifact, when supplied, to pass the route contract
  checks for resident memory mode, CUDA backend, resident registration mode, and
  the resident runtime preset/group evidence.
- Extend `glass phase2-status-compare` so a candidate cannot drop or regress
  default-route acceptance evidence once a baseline status contains it.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 225: Default Route Promotion Manifest Provenance

- Extend `glass default-promotion-manifest` so the manifest consumes
  `phase2_status.default_route_acceptance` from S2-Gate 224.
- Require default-route acceptance to be present, passed, route-contract passed,
  and backed by at least the four route checks for resident memory, CUDA backend,
  resident registration mode, and resident runtime preset/group evidence.
- Surface the default-route acceptance summary in default-promotion JSON and
  Markdown so default promotion cannot be approved from runtime/pipeline evidence
  alone.
- Add pass, missing-evidence, failed-evidence, and CLI Markdown tests.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 226: Windows Release Matrix Promotion Provenance

- Extend `glass windows-release-matrix` with a
  `--default-promotion-manifest` input so Windows package-matrix readiness
  consumes the Gate 225 default-route promotion provenance.
- Require the default-promotion manifest, unless explicitly waived, to be
  present, `default_promotion_ready`, passed, default-change ready, and backed by
  a passing default-route route contract with at least four route checks.
- Surface the default-promotion summary in Windows release matrix JSON and
  Markdown beside CUDA package compatibility, runtime, and release-decision
  evidence.
- Keep an explicit diagnostic escape hatch for old matrix artifacts that do not
  yet carry the manifest, but use the strict path for release checkpoints.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 227: GitHub Release Handoff Matrix Provenance

- Extend `glass windows-github-release-plan` with a
  `--windows-release-matrix` input so release notes, JSON handoff artifacts, and
  the dry-run publish script consume the Gate 226 package/default-promotion
  matrix.
- Require the Windows release matrix by default, unless explicitly waived, to be
  present, `release_matrix_ready`, passed, backed by a ready default-promotion
  manifest, and backed by a passing default-route route contract with at least
  four route checks.
- Verify that every matrix package label has a matching release-manifest asset
  in the GitHub release handoff plan, and preserve the CPU fallback in the
  matrix install order.
- Surface the matrix primary package, install order, default-promotion status,
  and default-route evidence in release-plan JSON, Markdown, generated release
  notes, and generated PowerShell publish scripts.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 228: Release Manifest Matrix Contract

- Extend `glass windows-release-manifest` with a `--windows-release-matrix`
  input so the manifest that records actual ZIP size and SHA256 also consumes
  the Windows package/default-promotion matrix.
- Require the matrix by default, unless explicitly waived, to be present,
  `release_matrix_ready`, passed, backed by ready default-promotion evidence,
  and backed by a passing default-route route contract with at least four route
  checks.
- Verify every matrix package label has a matching release-manifest package row,
  and preserve the CPU fallback in the matrix install order before the manifest
  can become `release_manifest_ready`.
- Surface the matrix primary package, install order, default-promotion status,
  and default-route evidence in release-manifest JSON and Markdown, then generate
  the Gate 228 GitHub handoff from that stricter manifest.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 229: Windows Publish Preflight Bundle Contract

- Add `glass windows-publish-preflight` to verify the release manifest, GitHub
  release handoff plan, Windows release matrix, and default-promotion manifest
  as one publication bundle before any real GitHub release is attempted.
- Require the release manifest to be `release_manifest_ready`, the GitHub handoff
  plan to be `release_plan_ready`, the Windows matrix to be
  `release_matrix_ready`, and the default-promotion manifest to be
  `default_promotion_ready`.
- Verify cross-artifact provenance: the manifest and GitHub handoff must
  reference the supplied matrix, the GitHub handoff must reference the supplied
  manifest, matrix package labels must match manifest package rows, and manifest
  ZIP path/size/SHA256 rows must match GitHub release assets.
- Preserve the CPU fallback and default-route route-contract evidence in the
  preflight JSON and Markdown so a future publish script can depend on a single
  artifact.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 230: Phase 2 Status Publish-Preflight Handoff

- Extend `glass phase2-status` with `--publish-preflight` so the Phase 2 status
  artifact can consume the Gate 229 single publication-bundle contract.
- Require the supplied publish-preflight artifact to be
  `publish_preflight_ready` and passed, carrying asset/package counts, primary
  package, CPU fallback order, default-promotion status, and default-route
  route-contract evidence.
- Surface publish-preflight summary in Phase 2 status JSON, Markdown, and CLI
  console output beside release manifest and GitHub release-plan evidence.
- Extend `glass phase2-status-compare` to flag regressions if a candidate drops
  a previously ready publish-preflight handoff.
- Keep this gate release/status only: no image processing algorithm changes and
  no new algorithm-source entry required.

### S2-Gate 231: StackEngine Rejection Sample Accounting Contract

- Extend the StackEngine result contract so low/high rejection count maps are
  validated as per-pixel rejected-sample counts, not just binary masks.
- Require each rejection map to contain finite, non-negative, near-integer
  counts, and require the rounded map sum to match the corresponding
  `metrics.low_rejected` or `metrics.high_rejected` sample total.
- Require rejection-map positive pixel counts to match DQ provenance
  `output_low_rejected_pixels` and `output_high_rejected_pixels`, while DQ
  flags continue to mark pixels touched by rejection rather than sample totals.
- Add focused tests for the important case where two rejected samples land in
  the same pixel: the high-rejection map sum is larger than the DQ pixel count,
  and both meanings must be preserved.
- Keep this gate algorithm-contract scoped: no CUDA kernel, runtime default,
  release packaging, or external-reference behavior changes.

### S2-Gate 232: Resident Rejection Sample Accounting Parity

- Extend `glass resident-result-contract` so resident CUDA artifacts preserve
  the same sample-versus-pixel rejection semantics introduced for StackEngine
  in Gate 231.
- Require resident JSON provenance to record rejected-sample totals in both
  `dq_coverage_provenance.rejected_sample_count` and
  `dq_provenance_summary.rejected_samples` when low/high rejection source terms
  are present.
- When `--pixel-verify` is enabled, read low/high rejection FITS maps in tiles,
  require finite non-negative near-integer counts, and require their rounded
  sample sum to match both resident rejected-sample provenance fields.
- Preserve existing DQ checks: DQ low/high flags still count touched pixels,
  while rejection count maps carry sample totals.
- Add positive, JSON-mismatch, and fractional-count-map tests.
- Keep this gate resident-contract scoped: no CUDA kernel math, runtime default,
  release packaging, or real-data benchmark rerun.

### S2-Gate 233: Pipeline Rejection Sample Pixel Handoff

- Extend `glass pipeline-contract --pixel-verify` so integration pixel
  verification reports rejected-sample accounting directly in pipeline guardrail
  artifacts.
- Verify low/high rejection FITS maps as finite, non-negative, near-integer
  count maps in the pipeline count-map verifier, not only in the resident
  result-contract verifier.
- Add `rejection_sample_accounting` rows that sum low/high rejection-map
  rounded counts and compare the total with available resident provenance
  fields or StackEngine metrics.
- Add a top-level pipeline check
  `integration_rejection_sample_counts_match_maps` so guardrails fail when DQ
  touched-pixel counts still match but rejected-sample totals drift.
- Preserve DQ semantics: DQ low/high flags count touched pixels; rejection maps
  count rejected samples.
- Add resident pipeline pixel-verification tests for pass, JSON sample-count
  drift, and fractional rejection-map values.
- Keep this gate pipeline-contract scoped: no image math, CUDA kernel, runtime
  default, release packaging, or real-data benchmark rerun.

### S2-Gate 234: Pipeline Rejection Sample Report Surface

- Extend HTML reports generated by `glass report` and `glass guardrails` so
  pipeline-contract rejection sample accounting is visible without opening raw
  JSON.
- Add a report table under Pipeline contract audit for
  `rejection_sample_accounting` rows, including required/verified/ok status,
  integration rejection mode, low/high rejection-map sample total, provenance
  source counts, failed source deltas, and sample-vs-pixel semantics.
- Preserve the existing DQ pixel delta table so users can compare touched-pixel
  counts against rejected-sample counts in the same report section.
- Add CLI report tests that verify sample-count drift appears in both failed
  check rows and the new rejection sample accounting table.
- Keep this gate report-surface scoped: no image math, CUDA kernel, runtime
  default, release packaging, or real-data benchmark rerun.

### S2-Gate 235: Acceptance Rejection Sample Triage

- Extend acceptance audit release evidence so pipeline-contract rejection
  sample accounting is machine-readable in
  `release_contract_evidence.pipeline_contract.rejection_sample_accounting`.
- Summarize the pipeline check
  `integration_rejection_sample_counts_match_maps`, pixel-verification state,
  accounted/required/verified/failed row counts, failed output items, low/high
  rejection-map rejected-sample totals, provenance source counts, and failed
  source deltas.
- Also attach the same compact summary to `pipeline_contract` inside the
  acceptance JSON so downstream status tools can consume either location.
- Add Markdown output for failed rejection sample accounting rows so release
  reviewers can diagnose sample-count drift without opening raw contract JSON.
- Add acceptance-audit tests for a pipeline contract where rejected-sample maps
  disagree with provenance while the rest of the benchmark fixture is valid.
- Keep this gate acceptance/report scoped: no image math, CUDA kernel, runtime
  default, release packaging, or real-data benchmark rerun.

### S2-Gate 236: Phase 2 Rejection Sample Status Handoff

- Extend `glass phase2-status` so pipeline-contract rejection sample accounting
  is summarized in the Phase 2 status artifact.
- Surface the pipeline check
  `integration_rejection_sample_counts_match_maps`, compact
  `rejection_sample_accounting` status, check presence, accounted/required/
  verified/failed row counts, failed output items, low/high rejection-map
  sample totals, and failed source deltas.
- Add `pipeline_rejection_sample_accounting_passed` to Phase 2 status checks so
  supplied pixel-verified pipeline contracts cannot be green when rejected
  sample maps disagree with provenance or the accounting row is missing.
- Extend `glass phase2-status-compare` so a baseline with passing rejection
  sample accounting requires the candidate to preserve both the accounting
  check presence and passing status.
- Add Phase 2 status and status-compare tests for passing accounting,
  sample-count drift, and schema/check disappearance.
- Keep this gate status/compare scoped: no image math, CUDA kernel, runtime
  default, release packaging, or real-data benchmark rerun.

### S2-Gate 237: Promotion Rejection Sample Blocker

- Extend `glass release-promotion-decision` so release-candidate and default
  change readiness require pipeline rejection sample accounting to pass.
- Preserve the `integration_rejection_sample_counts_match_maps` check and
  compact `rejection_sample_accounting` evidence in `pipeline_handoff`.
- Add `pipeline_rejection_sample_accounting_passed` to release-blocking checks
  so sample-count drift blocks promotion even if DQ touched-pixel checks pass.
- Extend `glass default-promotion-manifest` so Phase 2 status rejection sample
  accounting also blocks final default-promotion readiness.
- Surface the accounting status in release/default promotion Markdown output.
- Add release-promotion and default-promotion tests for passing accounting and
  sample-count drift blockers.
- Keep this gate promotion-control scoped: no image math, CUDA kernel, runtime
  default change, release packaging, or real-data benchmark rerun.

### S2-Gate 238: Windows Release Matrix Rejection Sample Handoff

- Extend `glass windows-release-matrix` so default-promotion rejection sample
  accounting is visible in the Windows publication matrix.
- Carry the default-promotion pipeline-contract fields
  `integration_rejection_sample_counts_match_maps`,
  `rejection_sample_accounting_status`, failed count, and failed items into the
  matrix summary.
- Add `default_promotion_rejection_sample_accounting_passed` to release-matrix
  checks so a Windows release matrix cannot pass when default promotion was
  blocked by rejected-sample map/provenance drift.
- Surface the accounting status in release-matrix Markdown output for release
  reviewers.
- Add release-matrix tests for passing accounting and sample-count drift
  blockers.
- Keep this gate release-matrix scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, or real-data benchmark rerun.

### S2-Gate 239: GitHub Release Plan Rejection Sample Handoff

- Extend `glass windows-github-release-plan` so Phase 2 and Windows release
  matrix rejection sample accounting are visible in final release handoff
  artifacts.
- Carry Phase 2 fields
  `pipeline_integration_rejection_sample_counts_match_maps`,
  `pipeline_rejection_sample_accounting_status`, and failed count into release
  plan summaries.
- Carry release-matrix fields
  `integration_rejection_sample_counts_match_maps`,
  `rejection_sample_accounting_status`, and failed count into release plan
  summaries.
- Add checks so publication plans fail when Phase 2 or release-matrix
  rejected-sample accounting is missing or failed.
- Add release notes, Markdown, and generated PowerShell dry-run validation for
  release-matrix rejection sample accounting.
- Add GitHub release-plan tests for passing accounting and matrix drift
  blockers.
- Keep this gate release-handoff scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, or real-data benchmark rerun.

### S2-Gate 240: Windows Publish Preflight Rejection Sample Handoff

- Extend `glass windows-publish-preflight` so final publication preflight
  consumes rejection sample accounting from the GitHub release plan, the Windows
  release matrix, and the default-promotion manifest.
- Require the release plan Phase 2 accounting check, the release plan matrix
  accounting check, the direct matrix accounting summary, and the direct
  default-promotion accounting summary to pass before a publish-preflight
  artifact can become ready.
- Cross-check the release plan matrix accounting summary against the supplied
  Windows release matrix so a stale handoff cannot mask rejected-sample
  map/provenance drift.
- Surface the accounting chain in preflight JSON and Markdown beside the
  release tag, package count, source stamps, default-promotion status, and
  route evidence.
- Add publish-preflight tests for passing accounting, Phase 2 sample-count
  drift, release-matrix sample-count drift, and CLI Markdown output.
- Keep this gate publication-preflight scoped: no image math, CUDA kernel,
  runtime default change, package build, upload, or real-data benchmark rerun.

### S2-Gate 241: Phase 2 Publish Preflight Rejection Status

- Extend `glass phase2-status --publish-preflight` so Phase 2 status artifacts
  preserve the publish-preflight rejection sample accounting chain introduced in
  Gate 240.
- Surface publish-preflight Phase 2, plan-matrix, direct matrix, and
  default-promotion accounting statuses and checks in Phase 2 JSON and Markdown.
- Add `windows_publish_preflight_rejection_sample_accounting_passed` so a
  publish-preflight artifact that is ready but lacks rejected-sample accounting
  evidence still blocks a green Phase 2 status.
- Extend `glass phase2-status-compare` so a candidate cannot regress from a
  baseline whose publish-preflight rejected-sample accounting chain was fully
  passed.
- Add Phase 2 status tests for passing accounting, missing accounting, failed
  accounting, Markdown output, and compare regression detection.
- Keep this gate status/compare scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, or real-data benchmark rerun.

### S2-Gate 242: StackEngine Invalid Sample Accounting Contract

- Extend StackEngine DQ provenance with explicit
  `input_valid_samples_before_rejection` and
  `input_invalid_samples_before_rejection` counters.
- Record matching StackEngine metrics for input valid/invalid samples and total
  rejected samples so downstream artifacts can distinguish invalid source
  samples from rejected source samples.
- Add result-contract checks that prove:
  - initial valid plus initial invalid samples equals total input samples;
  - final valid samples plus low/high rejected samples equals initially valid
    samples;
  - StackEngine metrics match DQ provenance for input valid/invalid samples.
- Add tests proving DQ-flagged and non-finite input samples are not counted as
  rejection samples, plus a contract drift test for broken input/rejection
  sample closure.
- Keep this gate StackEngine/DQ-contract scoped: no CUDA kernel, runtime default
  change, package build, upload, or real-data benchmark rerun.

### S2-Gate 243: DQ Provenance Sample Closure Handoff

- Carry StackEngine valid/invalid/rejected sample accounting into
  `dq_provenance_summary_from_stack_engine` so pipeline and report artifacts can
  consume the Gate 242 closure fields without opening raw StackEngine
  provenance.
- Add low/high rejected sample totals, final valid sample totals, and a
  `sample_accounting_closure` object to StackEngine DQ summaries.
- Add resident coverage `rounded_sum` statistics and carry optional resident
  pre/post rejection sample closure into `dq_provenance_summary_from_resident`.
- Extend resident result contracts to pass old artifacts with missing closure
  evidence but fail when a supplied resident closure explicitly fails.
- Add DQ provenance and resident result-contract tests for passing and failed
  sample closure evidence.
- Keep this gate DQ/report-contract scoped: no image math, CUDA kernel,
  runtime default change, package build, upload, or real-data benchmark rerun.

### S2-Gate 244: Pipeline Sample Closure Report Surface

- Surface `sample_accounting_closure` in pipeline-contract integration rows so
  auditors can see valid/invalid/rejected sample closure without opening raw DQ
  provenance JSON.
- Add `integration_sample_accounting_closure` to pipeline-contract checks. Old
  artifacts with missing closure remain compatible, but explicitly failed
  closure blocks the pipeline contract.
- Extend pipeline-contract Markdown with an Integration Sample Accounting
  Closure section.
- Extend the main HTML report with pipeline sample-closure rows and add
  valid/invalid/rejected sample columns to DQ provenance tables.
- Add tests for passing closure, failed closure, Markdown output, and HTML
  report visibility.
- Keep this gate report/contract scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, or real-data benchmark rerun.

### S2-Gate 245: Acceptance and Status Sample Closure Handoff

- Carry pipeline `integration_sample_accounting_closure` evidence into
  acceptance-audit release evidence and top-level pipeline-contract summaries.
- Extend acceptance Markdown with a compact Integration Sample Accounting
  Closure section listing failed valid/invalid/rejected sample closure rows.
- Extend `glass phase2-status` with pipeline sample-closure summary fields and a
  `pipeline_sample_accounting_closure_passed` readiness check.
- Extend `glass phase2-status-compare` so candidates cannot silently lose a
  previously present or passing sample-closure contract.
- Keep this gate acceptance/status scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, or real-data benchmark rerun.

### S2-Gate 246: Promotion Sample Closure Blocker

- Carry Phase 2 sample-closure evidence into release/default-promotion
  readiness checks, mirroring the existing rejection-sample accounting blocker.
- Extend release-promotion decisions with
  `pipeline_sample_accounting_closure_passed` so release candidates cannot pass
  when valid/invalid/rejected sample closure fails.
- Extend default-promotion manifests with
  `pipeline_sample_accounting_closure_passed` so default promotion cannot be
  declared ready when Phase 2 status lost or failed sample-closure evidence.
- Extend Markdown summaries with compact sample-closure status lines.
- Keep this gate promotion-readiness scoped: no image math, CUDA kernel,
  runtime default change, package build, upload, Windows release matrix change,
  or real-data benchmark rerun.

### S2-Gate 247: Windows Release Matrix Sample Closure Handoff

- Carry default-promotion `sample_accounting_closure` evidence into
  `glass windows-release-matrix` summaries.
- Add `default_promotion_sample_accounting_closure_passed` so Windows release
  matrices cannot pass when default-promotion manifests lost or failed
  valid/invalid/rejected sample closure evidence.
- Extend Windows release matrix Markdown with compact sample-closure status,
  present-row count, and failed-row count.
- Add focused tests for passing sample closure and blocked closure drift.
- Keep this gate Windows-release-matrix scoped: no image math, CUDA kernel,
  runtime default change, package build, upload, publish-preflight change, or
  real-data benchmark rerun.

### S2-Gate 248: GitHub Release Plan Sample Closure Handoff

- Carry Phase 2 and Windows release-matrix sample-closure evidence into
  `glass windows-github-release-plan`.
- Add publication-plan checks for
  `phase2_pipeline_sample_accounting_closure_passed` and
  `windows_release_matrix_sample_accounting_closure_passed`, mirroring the
  existing rejection-sample blockers.
- Extend release notes, Markdown handoff, and generated PowerShell dry-run
  validation with compact sample-closure status/present/failed evidence.
- Add focused tests for passing sample closure, Phase 2 closure drift, release
  matrix closure drift, CLI output text, and generated script guards.
- Keep this gate GitHub-release-plan scoped: no image math, CUDA kernel,
  runtime default change, package build, upload, publish-preflight change, or
  real-data benchmark rerun.

### S2-Gate 249: Windows Publish Preflight Sample Closure Handoff

- Carry GitHub release-plan, Windows release-matrix, and default-promotion
  sample-closure evidence into `glass windows-publish-preflight`.
- Add hard publish-preflight checks for:
  - GitHub plan Phase 2 sample-closure evidence;
  - GitHub plan release-matrix sample-closure evidence;
  - direct Windows release-matrix sample-closure evidence;
  - direct default-promotion sample-closure evidence;
  - GitHub plan release-matrix sample-closure agreement with the direct matrix
    artifact.
- Extend publish-preflight summaries and Markdown with compact sample-closure
  status across Phase 2, plan-matrix, direct matrix, and default-promotion
  sources.
- Add focused tests for passing closure, Phase 2 drift, matrix drift,
  default-promotion drift, and GitHub-plan/matrix mismatch.
- Keep this gate publish-preflight scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, package release, or real-data benchmark
  rerun.

### S2-Gate 250: Phase 2 Publish-Preflight Sample Closure Status

- Carry final Windows publish-preflight sample-closure evidence into
  `glass phase2-status`.
- Add `windows_publish_preflight_sample_accounting_closure_passed` so Phase 2
  status cannot remain green when publish-preflight sample closure is missing or
  failed.
- Extend Phase 2 Markdown with publish-preflight sample-closure status and
  check summaries beside the existing rejected-sample publication evidence.
- Extend `glass phase2-status-compare` so candidates cannot lose a previously
  passing publish-preflight sample-closure chain.
- Add focused tests for green handoff, missing sample closure, failed sample
  closure, and publish-preflight sample-closure compare regression.
- Keep this gate Phase2-status scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, package release, publish-preflight
  behavior change, or real-data benchmark rerun.

### S2-Gate 251: Phase 2 StackEngine Default Contract Handoff

- Carry StackEngine default-contract audit evidence into `glass phase2-status`.
- Add `stack_engine_default_contract_ready` so Phase 2 status cannot remain
  green when StackEngine default promotion is not ready, when adoption gaps
  remain, or when default-promotion blockers exist.
- Extend Phase 2 Markdown with StackEngine adoption, resident/StackEngine
  surface counts, default-gap count, and default-promotion blocker evidence.
- Extend `glass phase2-status-compare` so candidates cannot lose a previously
  ready StackEngine default contract or increase the recorded default-gap
  count.
- Add focused tests for green handoff, CLI Markdown output, default-contract
  gap blocking, and status-compare regression.
- Keep this gate Phase2-status scoped: no image math, CUDA kernel, runtime
  default change, package build, upload, package release, StackEngine audit
  behavior change, or real-data benchmark rerun.

### S2-Gate 252: Default Promotion StackEngine Contract Handoff

- Carry Phase 2 `stack_engine_contract` evidence into
  `glass default-promotion-manifest`.
- Add `phase2_stack_engine_default_contract_ready` so default-promotion
  manifests cannot pass when Phase 2 lost StackEngine default-contract
  evidence, when default gaps remain, or when default-promotion blockers exist.
- Extend default-promotion Markdown with StackEngine contract presence,
  readiness, Phase2 check state, adoption recommendation, default-gap count,
  and blocker count.
- Add focused tests for ready artifacts, missing StackEngine contract evidence,
  StackEngine default-gap blocking, and CLI Markdown output.
- Keep this gate default-promotion-manifest scoped: no image math, CUDA kernel,
  runtime default change, package build, upload, package release, release-matrix
  behavior change, or real-data benchmark rerun.

### S2-Gate 253: Windows Release Matrix StackEngine Contract Handoff

- Carry default-promotion `stack_engine_contract` evidence into
  `glass windows-release-matrix`.
- Add `default_promotion_stack_engine_contract_ready` so Windows release
  matrices cannot pass when default-promotion manifests lost StackEngine
  default-contract evidence, when default gaps remain, or when StackEngine
  blockers exist.
- Extend Windows release matrix Markdown with StackEngine default-contract
  readiness, Phase2 check state, gap count, and blocker count.
- Add focused tests for ready manifests, missing StackEngine evidence,
  StackEngine default-gap blocking, and CLI Markdown output.
- Keep this gate Windows-release-matrix scoped: no image math, CUDA kernel,
  runtime default change, package build, upload, publish-preflight behavior
  change, or real-data benchmark rerun.

### S2-Gate 254: GitHub Release Plan StackEngine Contract Handoff

- Carry Phase 2 and Windows release-matrix StackEngine default-contract
  evidence into `glass windows-github-release-plan`.
- Add `phase2_stack_engine_default_contract_ready` and
  `windows_release_matrix_stack_engine_contract_ready` so GitHub release plans
  cannot pass when StackEngine default-contract evidence is missing, stale, or
  blocked by default gaps.
- Add `phase2_release_matrix_stack_engine_contract_agree` so supplied Phase 2
  and Windows release-matrix artifacts must agree on zero StackEngine default
  gaps and zero blockers.
- Extend release notes, release-plan Markdown, and the generated PowerShell
  dry-run script with StackEngine default-contract readiness checks.
- Add focused tests for ready handoff, Phase2 StackEngine gap blocking, missing
  release-matrix StackEngine evidence, release-matrix StackEngine gap blocking,
  and CLI Markdown/notes/script output.
- Keep this gate GitHub-release-plan scoped: no image math, CUDA kernel,
  StackEngine audit behavior change, runtime default change, package build,
  upload, package release, publish-preflight behavior change, or real-data
  benchmark rerun.

### S2-Gate 255: Windows Publish Preflight StackEngine Contract Handoff

- Carry GitHub release-plan, Windows release-matrix, and default-promotion
  StackEngine default-contract evidence into `glass windows-publish-preflight`.
- Add final publish-preflight checks for Phase2 StackEngine contract evidence
  from the GitHub release plan, matrix StackEngine evidence from the GitHub
  release plan, direct Windows release-matrix StackEngine evidence, direct
  default-promotion StackEngine evidence, and cross-artifact agreement.
- Extend publish-preflight JSON and Markdown with StackEngine contract status
  and default-gap summaries.
- Add focused tests for green handoff, Phase2 StackEngine gap blocking,
  release-plan matrix StackEngine gap blocking, missing direct matrix
  StackEngine evidence, direct default-promotion StackEngine gap blocking, and
  CLI Markdown output.
- Keep this gate publish-preflight scoped: no image math, CUDA kernel,
  StackEngine audit behavior change, runtime default change, package build,
  upload, package release, GitHub release creation, or real-data benchmark
  rerun.

### S2-Gate 256: Phase 2 Publish-Preflight StackEngine Status Handoff

- Carry final publish-preflight StackEngine default-contract evidence into
  `glass phase2-status`.
- Add `windows_publish_preflight_stack_engine_default_contract_ready` so Phase
  2 status cannot stay green when final publish-preflight StackEngine evidence
  is missing, failed, stale, or disagreeing across GitHub release plan, Windows
  release matrix, and default-promotion artifacts.
- Extend Phase 2 Markdown with publish-preflight StackEngine contract statuses,
  readiness checks, and default-gap summaries.
- Extend `glass phase2-status-compare` so candidates cannot lose a previously
  passing final publish-preflight StackEngine contract chain.
- Add focused tests for green handoff, failed publish-preflight StackEngine
  evidence, CLI Markdown output, preserved compare checks, and publish-preflight
  StackEngine regression detection.
- Keep this gate Phase2-status scoped: no image math, CUDA kernel,
  StackEngine audit behavior change, runtime default change, package build,
  upload, package release, GitHub release creation, or real-data benchmark
  rerun.

### S2-Gate 257: StackEngine Publication Evidence Chain Audit

- Add `glass stack-engine-publication-audit` to audit the complete StackEngine
  default-contract publication evidence chain from source StackEngine contract
  through Phase 2 status, default-promotion manifest, Windows release matrix,
  GitHub release plan, publish preflight, and the Phase 2 publish-preflight
  handoff.
- Require every layer to report ready StackEngine default-contract evidence,
  zero default gaps, zero blockers, and agreement between adjacent artifacts.
- Emit JSON and Markdown audit artifacts with per-layer summaries and failed
  checks for release checklist use.
- Add focused tests for a passing chain, a release-matrix gap/mismatch, and CLI
  output/help behavior.
- Keep this gate audit scoped: no image math, CUDA kernel, StackEngine runtime
  behavior change, default change, package build, upload, GitHub release
  creation, or real-data benchmark rerun.

### S2-Gate 258: Winsorized Sigma Stack Rejection Semantics

- Harden CPU StackEngine `winsorized_sigma` so it is a distinct rejection
  baseline, not a generic sigma alias.
- Use a median/IQR-derived sigma estimate to choose the first winsorization
  bounds, fall back to standard deviation only when the robust scale is zero,
  then compute final mean/std on the winsorized samples for rejection.
- Record the rejection scale estimator and full rejection-policy provenance in
  StackEngine metrics and DQ provenance so report/audit layers can distinguish
  sigma, MAD, percentile, minmax, and winsorized paths.
- Add a low-sample outlier regression test where ordinary sigma keeps the
  sample but `winsorized_sigma` rejects it while preserving sample-accounting
  and result-contract checks.
- Keep this gate CPU StackEngine scoped: no CUDA kernel, resident runtime
  behavior change, runtime default change, package build, upload, GitHub
  release creation, or real-data benchmark rerun.

### S2-Gate 259: CPU Integration Rejection Baseline Unification

- Extract shared rejection-statistics helpers into `glass.engine.rejection`.
- Keep StackEngine and legacy `glass.cpu.integration.weighted_integrate_stack`
  on the same clean-room CPU baseline for sigma, MAD/median sigma, and
  winsorized sigma center/scale estimation.
- Update legacy CPU `winsorized_sigma` from a mean/std first-pass
  approximation to the S2-Gate 258 median/IQR-guided winsorized baseline.
- Add a low-sample CPU integration regression where `sigma_clip` keeps an
  outlier but `winsorized_sigma` rejects it, matching the hardened StackEngine
  behavior.
- Keep this gate CPU baseline scoped: no CUDA kernel, resident runtime behavior
  change, runtime default change, package build, upload, GitHub release
  creation, or real-data benchmark rerun.

### S2-Gate 260: Resident Winsorized Rejection Semantics Disclosure

- Add shared rejection descriptor constants for CPU winsorized sigma and the
  current resident CUDA winsorized approximation.
- Record resident rejection descriptors in `resident_artifacts.json`,
  `integration_results.json` output rows, and top-level integration semantics.
- Extend resident result contracts so resident `winsorized_sigma` outputs must
  explicitly disclose the current mean/std two-stage approximation, the CPU
  median/IQR baseline estimator, `cpu_baseline_parity=false`, and a pending CUDA
  parity status.
- Add contract tests for passing disclosed semantics and failing legacy/missing
  winsorized semantics.
- Keep this gate artifact/contract scoped: no CUDA kernel change, resident
  runtime behavior change, runtime default change, package build, upload,
  GitHub release creation, or real-data benchmark rerun.

### S2-Gate 261: Resident Hardened Winsorized CUDA Parity Prototype

- Add an explicit native `ResidentCalibratedStack.integrate_hardened_winsorized_sigma`
  method for CUDA resident stacks.
- Implement a prototype CUDA kernel that gathers valid per-pixel resident
  samples, sorts up to 256 active frames, computes median/q25/q75 with linear
  percentile interpolation, applies the S2-Gate 258/259 median-IQR winsorized
  rejection baseline, and accumulates weighted mean plus rejection maps.
- Keep the existing resident `integrate_sigma_clip(..., winsorize=true)` fast
  path unchanged and leave runtime defaults untouched.
- Add a CUDA parity test comparing the new native method against
  `glass.cpu.integration.weighted_integrate_stack(..., rejection="winsorized_sigma")`
  on a low-sample outlier case with non-uniform weights.
- Keep this gate CUDA prototype scoped: no resident runtime default change,
  no tile-local/matrix-warped parity migration, no package build/upload, no
  GitHub release creation, and no 200-light real-data benchmark rerun.

### S2-Gate 262: Opt-In Hardened Winsorized Resident Runtime

- Add an explicit resident runtime and CLI mode,
  `--resident-winsorized-mode hardened_cpu_parity`, that calls the S2-Gate 261
  `ResidentCalibratedStack.integrate_hardened_winsorized_sigma` method when
  `--integration-rejection winsorized_sigma` is selected.
- Preserve `fast_approx` as the default mode so the Phase 1/2 resident
  throughput baseline is not silently changed by the correctness prototype.
- Make resident `auto` dispatch choose stack integration for hardened
  winsorized mode, and fail clearly for unsupported fused-matrix or tile-local
  policy combinations.
- Extend resident result contracts to accept either the default fast
  approximation semantics or the opt-in hardened CPU-parity semantics.
- Add a small FITS resident CUDA run test that compares hardened runtime output
  maps against the CPU `weighted_integrate_stack` winsorized baseline.
- Keep this gate scoped to runtime wiring and artifact semantics; no optimized
  200-light hardened benchmark, tile-local parity migration, fused matrix
  parity migration, package build/upload, or release update is required.

### S2-Gate 263: Hardened Winsorized Runtime Guardrails

- Promote the S2-Gate 261 hardened resident frame-count limit into a shared
  Python contract so runtime validation, descriptors, artifacts, and tests all
  report the same capacity boundary.
- Validate `--resident-winsorized-mode hardened_cpu_parity` before allocating
  the resident stack and fail clearly when a filter/shape light group exceeds
  the prototype capacity.
- Record a per-output resident winsorized runtime contract in
  `resident_artifacts.json` and `integration_results.json`, including mode,
  implementation, frame count, frame limit, dispatch requirement, and pass/fail
  booleans.
- Add CPU-only helper tests for over-limit hardened mode and non-applicable
  fast-approx mode, plus a CUDA runtime artifact test for a successful hardened
  stack-dispatch run.
- Keep this gate guardrail scoped: no CUDA kernel rewrite, no 200-light
  benchmark, no package build/upload, no default switch, and no fused-matrix or
  tile-local hardened parity migration.

### S2-Gate 264: Hardened Winsorized Timing Surface

- Add a timed `ResidentCalibratedStack.integrate_hardened_winsorized_sigma_timed`
  Python wrapper around the Gate261 native method.
- Record timing model, native method, resident winsorized mode, frame count,
  image shape, pixel count, sigma thresholds, and total wall time for the
  hardened prototype path.
- Thread this timing block into resident runtime artifacts and integration
  output rows so future 200-light hardened benchmarks can isolate the
  correctness prototype integration cost from broader I/O, calibration,
  registration, local normalization, and output-write timing.
- Add focused CUDA wrapper and resident runtime tests that verify timing
  metadata is emitted without changing output pixels or maps.
- Keep this gate timing-surface scoped: no native CUDA kernel change, no
  benchmark rerun, no package build/upload, no default switch, and no
  fused-matrix or tile-local hardened parity migration.

### S2-Gate 265: Resident Winsorized Microbenchmark Artifact

- Add `glass resident-winsorized-benchmark`, a deterministic synthetic
  microbenchmark for resident CUDA winsorized integration.
- Generate a small in-memory stack with gradients, frame-to-frame variation,
  weights, and low/high outliers without reading user image directories.
- Compare the existing fast resident winsorized approximation, the opt-in
  hardened resident CUDA path, and the CPU `weighted_integrate_stack`
  winsorized baseline.
- Emit JSON and optional Markdown with timing, hardened-vs-CPU map differences,
  fast-approx-vs-CPU context, pass/fail checks, limitations, and CUDA
  unavailable diagnostics.
- Add CPU-only unavailable-path tests, CUDA microbenchmark tests, CLI tests,
  and help-list coverage.
- Keep this gate microbenchmark scoped: it does not replace the 200-light real
  benchmark, change image math, optimize kernels, build/upload packages, or
  change defaults.

### S2-Gate 266: Resident Winsorized Microbenchmark Contract Audit

- Add a machine-readable contract for the Gate265 resident winsorized
  microbenchmark artifact.
- Add `glass resident-winsorized-benchmark-audit` to validate benchmark status,
  CUDA availability, deterministic synthetic configuration, hardened-vs-CPU
  RMS/max-absolute tolerances, required timing metadata, and fast-approximation
  context.
- Emit JSON and optional Markdown with pass/fail checks so hardened winsorized
  parity drift can be caught without rerunning the 200-light benchmark.
- Add focused contract and CLI tests, plus help-list coverage.
- Keep this gate contract scoped: no image math, CUDA kernel, runtime default,
  package build/upload, release update, or real-data benchmark rerun.

### S2-Gate 267: Phase 2 Resident Winsorized Audit Status Handoff

- Carry `glass resident-winsorized-benchmark-audit` evidence into
  `glass phase2-status`.
- Add an optional `--resident-winsorized-benchmark-audit` input and a
  `resident_winsorized_benchmark_audit_passed` status check when the artifact
  is supplied.
- Surface contract name, benchmark path, check count, failed checks,
  hardened-vs-CPU difference metrics, fast-approximation context, and timing
  summary in Phase 2 JSON/Markdown status outputs.
- Add focused API and CLI tests for passing and failed audit handoff.
- Keep this gate status-handoff scoped: no image math, CUDA kernel, runtime
  default, package build/upload, release update, status-compare change, or
  real-data benchmark rerun.

### S2-Gate 268: Resident Winsorized Frame-Count Sweep

- Add `glass resident-winsorized-sweep`, a deterministic synthetic frame-count
  sweep for resident CUDA winsorized integration.
- Reuse the Gate265 single-benchmark path across multiple frame counts,
  including a required 200-frame row by default, so the hardened prototype is
  checked at the Phase 1 200-light sample-count scale on a small in-memory
  image.
- Emit JSON and optional Markdown with per-frame-count timing, hardened-vs-CPU
  differences, fast-approximation context, required-frame-count checks, and
  CUDA-unavailable diagnostics. Use a sweep-scale RMS tolerance that remains
  tighter than `1e-4` while allowing small float32 accumulation differences at
  the required 200-frame row.
- Add focused tests for parsing, CUDA-unavailable behavior, CUDA parity, CLI
  artifact writing, and help-list coverage.
- Keep this gate sweep scoped: it does not replace the 200-light real-data
  benchmark, change image math, optimize kernels, raise the 256-frame prototype
  limit, build/upload packages, change defaults, or rerun real data.

### S2-Gate 269: Resident Winsorized Sweep Contract Audit

- Add a machine-readable contract for the Gate268 resident winsorized
  frame-count sweep artifact.
- Add `glass resident-winsorized-sweep-audit` to validate sweep pass status,
  deterministic configuration, expected frame-count rows, the required
  200-frame row, hardened-vs-CPU RMS/max-absolute tolerances, per-row map
  agreement, required timing metadata, and hardened native method/mode.
- Emit JSON and optional Markdown with pass/fail checks so 200-frame
  sample-count parity drift can be caught without rerunning the full real-data
  benchmark.
- Add focused contract tests for passing, missing required row, RMS drift,
  Markdown writing, CLI artifact writing, and help-list coverage.
- Keep this gate audit scoped: no image math, CUDA kernel, runtime default,
  package build/upload, release update, status handoff, status-compare change,
  or real-data benchmark rerun.

### S2-Gate 270: Phase 2 Resident Winsorized Sweep Audit Status Handoff

- Carry `glass resident-winsorized-sweep-audit` evidence into
  `glass phase2-status`.
- Add an optional `--resident-winsorized-sweep-audit` input and a
  `resident_winsorized_sweep_audit_passed` status check when the artifact is
  supplied.
- Surface contract name, sweep path, check count, failed checks, frame-count
  rows, required 200-frame row status, hardened-vs-CPU difference metrics, and
  required-row timing summary in Phase 2 JSON/Markdown status outputs.
- Add focused API and CLI tests for passing and failed audit handoff.
- Keep this gate status-handoff scoped: no image math, CUDA kernel, runtime
  default, package build/upload, release update, status-compare change, or
  real-data benchmark rerun.

### S2-Gate 271: Phase 2 Resident Winsorized Sweep Status-Compare Guard

- Carry the S2-Gate 270 `resident_winsorized_sweep_audit` summary into
  `glass phase2-status-compare` baseline/candidate summaries.
- Add regression checks so a candidate status cannot lose a previously passing
  resident winsorized sweep audit, lose the required 200-frame row pass, or
  reduce the supplied sweep-audit check count.
- Add focused tests for passing compare fixtures and failed sweep-audit
  regression detection.
- Keep this gate compare-guard scoped: no image math, CUDA kernel, runtime
  default, package build/upload, release update, release-promotion change, or
  real-data benchmark rerun.

### S2-Gate 272: Default Promotion Resident Winsorized Sweep Guard

- Carry the S2-Gate 270 `resident_winsorized_sweep_audit` summary into
  `glass default-promotion-manifest`.
- Require the supplied Phase 2 status to contain a passing resident winsorized
  sweep audit, a passing required 200-frame row, and a sweep-audit check count
  at or above the default contract count.
- Surface the resident winsorized sweep evidence in default-promotion JSON and
  Markdown so hardened winsorized 200-frame parity is a blocker for default
  route promotion, not only a status note.
- Add focused manifest and CLI tests for ready, missing, and failed sweep
  evidence.
- Keep this gate promotion-guard scoped: no image math, CUDA kernel, runtime
  default, package build/upload, release update, release-promotion decision
  change, or real-data benchmark rerun.

### S2-Gate 273: Windows Release Matrix Resident Winsorized Sweep Guard

- Carry the S2-Gate 272 resident winsorized sweep default-promotion evidence
  into `glass windows-release-matrix`.
- Add release-matrix blockers so Windows release readiness requires a passing
  resident winsorized sweep audit, a passing required 200-frame row, and the
  expected sweep-audit check count from the default-promotion manifest.
- Surface the resident winsorized sweep evidence in Windows release matrix JSON
  and Markdown so release packaging cannot ignore hardened winsorized
  200-frame parity blockers.
- Add focused matrix and CLI tests for ready, missing, and failed sweep
  evidence.
- Keep this gate release-matrix scoped: no image math, CUDA kernel, runtime
  default, package build/upload, GitHub release update, publish-preflight
  change, or real-data benchmark rerun.

### S2-Gate 274: Windows Publish Preflight Resident Winsorized Sweep Guard

- Carry the S2-Gate 273 release-matrix/default-promotion resident winsorized
  sweep evidence into `glass windows-publish-preflight`.
- Add publish-preflight blockers so final Windows publication readiness requires
  the supplied matrix to retain a passing resident winsorized sweep audit, a
  passing required 200-frame row, and a non-empty sweep-audit check count.
- Cross-check resident winsorized sweep status, pass flags, required frame
  count, required row pass, and check count between the supplied Windows release
  matrix and default-promotion manifest so stale publication bundles cannot mask
  hardened winsorized parity drift.
- Surface the resident winsorized sweep evidence in publish-preflight JSON and
  Markdown beside release tag, package count, sample accounting, and
  StackEngine contract evidence.
- Add focused publish-preflight tests for ready, missing, failed, and mismatched
  resident winsorized sweep evidence.
- Keep this gate publication-preflight scoped: no image math, CUDA kernel,
  runtime default, package build/upload, GitHub release creation, or real-data
  benchmark rerun.

### S2-Gate 275: Phase 2 Publish Preflight Resident Winsorized Sweep Status Handoff

- Carry the S2-Gate 274 Windows publish-preflight resident winsorized sweep
  evidence into `glass phase2-status`.
- Add a Phase 2 status blocker so publication status cannot remain green when
  publish-preflight is ready but lacks resident winsorized sweep evidence, or
  when publish-preflight records a failed resident winsorized sweep guard.
- Surface matrix/default-promotion sweep status, required 200-frame pass flags,
  and check counts in Phase 2 status JSON and Markdown.
- Extend `glass phase2-status-compare` so a candidate cannot lose a previously
  passing publish-preflight resident winsorized sweep chain, required-frame
  status, or non-empty check-count evidence.
- Add focused tests for green handoff, missing/failed publish-preflight sweep
  evidence, CLI Markdown output, and compare regression detection.
- Keep this gate status-handoff scoped: no image math, CUDA kernel, runtime
  default, package build/upload, GitHub release creation, publish-preflight
  behavior change, or real-data benchmark rerun.

### S2-Gate 276: StackEngine Publication Audit Resident Winsorized Sweep Guard

- Carry the S2-Gate 275 Phase 2 publish-preflight resident winsorized sweep
  evidence into `glass stack-engine-publication-audit`.
- Add publication-audit blockers so StackEngine default publication readiness
  requires both the raw publish-preflight artifact and the Phase 2 status
  handoff to preserve a passing resident winsorized sweep audit, required
  200-frame row pass, and non-empty sweep check count.
- Cross-check resident winsorized sweep statuses, required-frame counts, pass
  flags, check counts, and matrix/default-promotion agreement between the raw
  publish-preflight artifact and the Phase 2 status handoff.
- Surface the resident winsorized sweep publication layers in audit JSON and
  Markdown beside the source StackEngine contract, default-promotion manifest,
  release matrix, GitHub release plan, and publish-preflight StackEngine layers.
- Add focused publication-audit tests for ready evidence, failed resident
  winsorized evidence, and Phase 2/raw publish-preflight mismatch detection.
- Keep this gate publication-audit scoped: no image math, CUDA kernel, runtime
  default, package build/upload, GitHub release creation, publish-preflight
  behavior change, or real-data benchmark rerun.

### S2-Gate 277: Strict StackEngine Master Calibration Default

- Make master calibration StackEngine failures fatal by default instead of
  silently falling back to the legacy streaming accumulator.
- Add `CalibrationPolicy.allow_legacy_stack_fallback`, defaulting to `false`,
  so diagnostic compatibility runs can explicitly request the legacy fallback
  while normal Phase 2 runs preserve StackEngine as the default master-frame
  execution path.
- Apply the same strict default to flat per-frame normalization fallback: a
  failed StackEngine flat master path must not silently downgrade unless the
  policy explicitly allows legacy fallback.
- Preserve the old legacy fallback behavior only under the explicit policy flag,
  and record `legacy_fallback_explicitly_allowed=true` in fallback metrics.
- Add focused tests proving default StackEngine failure is surfaced as an error,
  and explicit fallback still reproduces the legacy streaming accumulator for
  diagnostic runs.
- Keep this gate default-contract scoped: no image math change when StackEngine
  succeeds, no CUDA kernel change, no package build/upload, no publication
  handoff change, and no real-data benchmark rerun.

### S2-Gate 278: Explicit Non-Resident CUDA Integration Fast Path

- Keep non-resident light integration on `stack_engine_cpu` by default, even
  when CUDA is importable and rejection is `none`.
- Add `IntegrationPolicy.allow_cuda_streaming_accumulator_fast_path`, defaulting
  to `false`, so the older non-resident CUDA streaming accumulator can only
  bypass StackEngine when explicitly requested by policy, or when the user
  explicitly chooses `--backend cuda`.
- Record an `integration_engine_policy` artifact summary and per-output
  `engine_selection` details so reports/contracts can audit why a run used
  StackEngine or the explicit CUDA fast path.
- Add synthetic registered-frame tests that monkeypatch a CUDA integration
  module and prove `backend=auto` keeps the StackEngine default while policy
  opt-in enables the CUDA fast path.
- Keep this gate default-route scoped: no resident CUDA path change, no CUDA
  kernel change, no package build/upload, no publication handoff change, and no
  real-data benchmark rerun.

### S2-Gate 279: Pipeline Contract Integration Engine Policy Guard

- Carry the S2-Gate 278 non-resident integration engine-selection policy into
  `glass pipeline-contract`.
- Add a pipeline-contract blocker requiring non-resident integration artifacts
  to record top-level `integration_engine_policy`, per-output
  `engine_selection`, and `default_engine=stack_engine_cpu`.
- Accept non-resident CUDA streaming accumulator outputs only when the artifact
  proves the fast path was explicitly requested by policy or by an explicit
  CUDA backend selection.
- Keep resident CUDA stack outputs exempt from the non-resident default-engine
  guard so the resident all-VRAM path remains governed by its resident result
  contract.
- Surface engine-policy evidence in pipeline-contract JSON and Markdown, and
  add focused tests for CPU StackEngine defaults, explicit CUDA fast-path
  opt-in, and blocked implicit CUDA fast-path artifacts.
- Keep this gate audit-contract scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no publication
  handoff change, and no real-data benchmark rerun.

### S2-Gate 280: Acceptance Audit Integration Engine Policy Handoff

- Carry the S2-Gate 279 pipeline-contract integration engine-policy guard into
  `glass acceptance-audit`.
- Add an acceptance-audit blocker so supplied pipeline contracts must contain a
  passing `integration_default_engine_policy` check; stale contracts that only
  report generic pass/fail status are not sufficient Phase 2 acceptance
  evidence.
- Summarize integration engine-policy status, resident/non-resident output
  counts, failed rows, and failure reasons in acceptance JSON and Markdown.
- Extend benchmark-contract pipeline requirements used in tests so
  `integration_default_engine_policy` is an explicit required pipeline-contract
  check beside calibration, resident light, and resident result-contract
  checks.
- Add focused tests for passing handoff, blocked implicit non-resident CUDA
  fast-path evidence, benchmark-required check propagation, missing contract
  behavior, and Markdown output.
- Keep this gate acceptance-handoff scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no publication
  handoff change beyond acceptance evidence, and no real-data benchmark rerun.

### S2-Gate 281: Phase 2 Status Integration Engine Policy Handoff

- Carry the S2-Gate 280 acceptance-audit integration engine-policy evidence into
  `glass phase2-status`.
- Summarize acceptance-side pipeline integration engine-policy status, required
  check presence, required check result, resident/non-resident counts, and failed
  row counts in status JSON and Markdown.
- Carry raw `glass pipeline-contract` integration engine-policy summaries into
  Phase 2 status so current status artifacts expose the same default-route guard
  without relying only on the acceptance-audit handoff.
- Add green-status blockers for missing or failed acceptance-side and
  pipeline-contract engine-policy evidence.
- Extend `glass phase2-status-compare` so a candidate cannot drop a previously
  passing acceptance handoff, lose the pipeline-contract required check, or
  regress a previously passing pipeline integration engine-policy status.
- Keep this gate status/compare scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no release
  publication change, and no real-data benchmark rerun.

### S2-Gate 282: Default Promotion Integration Engine Policy Guard

- Carry the S2-Gate 281 Phase 2 status integration engine-policy evidence into
  `glass default-promotion-manifest`.
- Require the default-promotion manifest to preserve both acceptance-side
  integration engine-policy handoff evidence and raw pipeline-contract default
  engine-policy evidence before recommending the resident CUDA default route.
- Block stale Phase 2 status artifacts that still report green status but do not
  contain Gate281 `acceptance_pipeline_integration_engine_policy_passed` and
  `pipeline_integration_engine_policy_passed` checks.
- Surface acceptance/pipeline engine-policy status, required check presence,
  required check result, Phase 2 check result, non-resident counts, and failed
  rows in default-promotion JSON and Markdown.
- Add focused default-promotion tests for ready evidence, missing stale policy
  evidence, failed acceptance/pipeline policy evidence, and Markdown output.
- Keep this gate default-promotion scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no release
  publication change, and no real-data benchmark rerun.

### S2-Gate 283: Windows Release Matrix Integration Engine Policy Guard

- Carry the S2-Gate 282 default-promotion integration engine-policy evidence
  into `glass windows-release-matrix`.
- Require Windows release-matrix readiness to preserve both default-promotion
  acceptance-side engine-policy handoff evidence and pipeline-side default
  engine-policy evidence.
- Block default-promotion manifests that report ready status but do not contain
  Gate282 `integration_engine_policy` summaries.
- Surface integration engine-policy readiness, acceptance status, pipeline
  status, required check presence, Phase 2 check result, non-resident counts,
  and failed rows in release-matrix JSON and Markdown.
- Add focused release-matrix tests for ready evidence, missing stale policy
  evidence, failed acceptance/pipeline policy evidence, and Markdown output.
- Keep this gate release-matrix scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  publication change, and no real-data benchmark rerun.

### S2-Gate 284: Windows Publish Preflight Integration Engine Policy Guard

- Carry the S2-Gate 283 release-matrix integration engine-policy evidence into
  `glass windows-publish-preflight`.
- Require final Windows publish preflight readiness to preserve both
  release-matrix and default-promotion integration engine-policy evidence.
- Block stale release-matrix or default-promotion artifacts that still report
  ready status but do not contain the Gate282/Gate283 policy summaries.
- Cross-check acceptance-side status, pipeline-side status, required check
  presence, check pass state, Phase 2 pass state, non-resident counts, and
  failed rows between the release matrix and the default-promotion manifest.
- Surface integration engine-policy readiness and status in preflight JSON and
  Markdown so publication handoff reviewers can see the resident default-route
  policy chain without opening lower-level artifacts.
- Add focused publish-preflight tests for ready evidence, missing stale matrix
  policy evidence, failed default-promotion policy evidence, and Markdown
  output.
- Keep this gate publish-preflight scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  publication change, and no real-data benchmark rerun.

### S2-Gate 285: Phase 2 Publish Preflight Integration Engine Policy Handoff

- Carry the S2-Gate 284 Windows publish-preflight integration engine-policy
  evidence into `glass phase2-status`.
- Require Phase 2 green status to preserve publish-preflight evidence for both
  release-matrix and default-promotion integration engine-policy checks.
- Block stale publish-preflight artifacts that still report ready status but do
  not contain Gate284 policy summary/check fields.
- Extend `glass phase2-status-compare` so candidate status artifacts cannot
  lose a previously passing publish-preflight integration engine-policy chain.
- Surface publish-preflight policy readiness, acceptance/pipeline statuses, and
  check agreement in Phase 2 JSON and Markdown.
- Add focused status and status-compare tests for ready evidence, missing stale
  publish-preflight policy evidence, failed policy evidence, and Markdown
  output.
- Keep this gate status-handoff scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  publication change, and no real-data benchmark rerun.

### S2-Gate 286: StackEngine Publication Audit Integration Engine Policy Guard

- Carry the S2-Gate 285 Phase 2 status handoff and S2-Gate 284 raw
  publish-preflight integration engine-policy evidence into
  `glass stack-engine-publication-audit`.
- Require StackEngine publication readiness to preserve both the raw
  publish-preflight policy checks and the Phase 2 status transcription of those
  checks.
- Block stale publish-preflight artifacts that still report ready status but do
  not contain Gate284 integration engine-policy summaries.
- Block Phase 2 status artifacts whose publish-preflight policy transcription
  is missing, failed, or no longer matches the raw publish-preflight artifact.
- Surface raw and Phase 2 publish-preflight policy layers in publication-audit
  JSON and Markdown.
- Add focused publication-audit tests for ready evidence, missing raw policy
  evidence, failed policy evidence, Phase 2 transcription mismatch, and CLI
  Markdown output.
- Keep this gate publication-audit scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  publication change, and no real-data benchmark rerun.

### S2-Gate 287: Phase 2 StackEngine Publication Audit Handoff

- Carry the S2-Gate 286 StackEngine publication-audit artifact back into
  `glass phase2-status`.
- Add Phase 2 green-status blockers for missing or failed StackEngine
  publication-audit evidence when that artifact is supplied.
- Require the publication-audit handoff to preserve both the integration
  engine-policy chain and resident winsorized sweep chain before Phase 2 status
  can remain green.
- Surface publication-audit status, failed checks, policy-chain checks, and
  resident winsorized chain checks in Phase 2 JSON and Markdown.
- Extend `glass phase2-status-compare` so a candidate cannot drop a previously
  passing StackEngine publication-audit, policy chain, or resident winsorized
  chain.
- Add focused Phase 2 status, CLI Markdown, and status-compare tests for ready
  evidence and publication-audit regressions.
- Keep this gate status/compare scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  publication change, and no real-data benchmark rerun.

### S2-Gate 288: Default Promotion StackEngine Publication Audit Guard

- Carry the S2-Gate 287 Phase 2 StackEngine publication-audit handoff into
  `glass default-promotion-manifest`.
- Require default-promotion readiness to preserve a passing StackEngine
  publication-audit artifact when the Phase 2 status is used for default-route
  promotion.
- Require the default-promotion manifest to preserve both publication-audit
  integration engine-policy chain evidence and resident winsorized sweep chain
  evidence.
- Block stale Phase 2 status artifacts that still report green status but do
  not contain Gate287 publication-audit summaries and checks.
- Surface publication-audit status, failed checks, policy-chain checks, and
  resident winsorized chain checks in default-promotion JSON and Markdown.
- Add focused default-promotion tests for ready evidence, missing stale
  publication-audit evidence, failed policy-chain evidence, and CLI Markdown
  output.
- Keep this gate default-promotion scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  publication change, and no real-data benchmark rerun.

### S2-Gate 289: Windows Release Matrix StackEngine Publication Audit Guard

- Carry the S2-Gate 288 default-promotion StackEngine publication-audit
  evidence into `glass windows-release-matrix`.
- Require Windows release-matrix readiness to preserve the default-promotion
  publication-audit artifact, its Phase 2 audit check, its integration
  engine-policy chain, and its resident winsorized sweep chain before Windows
  CUDA publication can remain green.
- Block stale default-promotion manifests that still report ready status but do
  not contain Gate288 publication-audit summaries and checks.
- Surface publication-audit readiness, failed checks, policy-chain agreement,
  and resident winsorized-chain agreement in release-matrix JSON and Markdown.
- Add focused release-matrix tests for ready evidence, missing stale
  publication-audit evidence, failed policy-chain evidence, failed resident
  winsorized-chain evidence, and CLI Markdown output.
- Keep this gate release-matrix scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  publication change, and no real-data benchmark rerun.

### S2-Gate 290: Windows Publish Preflight StackEngine Publication Audit Guard

- Carry the S2-Gate 289 release-matrix StackEngine publication-audit evidence
  and S2-Gate 288 default-promotion publication-audit evidence into
  `glass windows-publish-preflight`.
- Require final Windows publish-preflight readiness to preserve the
  publication-audit artifact, its integration engine-policy chain, and its
  resident winsorized sweep chain across both release-matrix and
  default-promotion handoffs.
- Block stale release-matrix or default-promotion artifacts that still report
  ready status but do not contain Gate288/Gate289 publication-audit summaries
  and checks.
- Cross-check release-matrix and default-promotion publication-audit status,
  failed checks, policy-chain agreement, and resident winsorized-chain agreement.
- Surface publication-audit readiness and agreement in preflight JSON and
  Markdown so final publication reviewers can audit the StackEngine default
  publication chain without opening lower-level artifacts.
- Add focused publish-preflight tests for ready evidence, missing stale matrix
  evidence, failed default-promotion policy-chain evidence, matrix/default
  resident winsorized-chain mismatch, and CLI Markdown output.
- Keep this gate publish-preflight scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 291: Phase 2 Publish Preflight StackEngine Publication Audit Handoff

- Carry the S2-Gate 290 Windows publish-preflight StackEngine
  publication-audit evidence into `glass phase2-status`.
- Require Phase 2 green status to preserve final publish-preflight evidence for
  both release-matrix and default-promotion publication-audit chains.
- Block stale publish-preflight artifacts that still report ready status but do
  not contain Gate290 publication-audit summary/check fields.
- Extend `glass phase2-status-compare` so a candidate status cannot lose a
  previously passing publish-preflight publication-audit chain.
- Surface publish-preflight publication-audit readiness, policy-chain agreement,
  resident winsorized-chain agreement, and matrix/default-promotion agreement in
  Phase 2 JSON and Markdown.
- Add focused status, CLI Markdown, and status-compare tests for ready evidence,
  missing stale publish-preflight publication evidence, failed policy-chain
  evidence, and candidate regression.
- Keep this gate status/compare scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 292: StackEngine Publication Audit Phase 2 Publish Preflight Handoff

- Carry the S2-Gate 291 Phase 2 publish-preflight StackEngine
  publication-audit handoff back into `glass stack-engine-publication-audit`.
- Require final StackEngine publication-audit readiness to preserve both raw
  Windows publish-preflight publication-audit evidence and the matching Phase 2
  status handoff evidence.
- Block stale publish-preflight or Phase 2 status artifacts that still report
  ready/green status but do not contain Gate290/Gate291 publication-audit
  summary and check fields.
- Cross-check matrix/default-promotion publication-audit status, readiness,
  integration engine-policy agreement, resident winsorized-chain agreement, and
  matrix/default agreement between raw publish-preflight and Phase 2 status.
- Surface the new publish-preflight publication-audit and Phase 2 handoff layers
  in StackEngine publication-audit JSON and Markdown.
- Add focused publication-audit tests for ready evidence, missing raw
  publish-preflight publication evidence, failed Phase 2 handoff evidence, and
  CLI Markdown output.
- Keep this gate publication-audit scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 293: Pipeline Contract StackEngine Runtime Default Surface

- Return from publication-chain closure to runtime artifact hardening by
  extending `glass pipeline-contract` with a single StackEngine runtime-default
  surface summary.
- Require pipeline-contract evidence to show that master calibration surfaces
  use StackEngine CPU or resident CUDA calibration contracts, blocking legacy
  master accumulator artifacts even when their science metadata is otherwise
  well formed.
- Preserve the existing explicit opt-in CUDA streaming accumulator exception for
  non-resident integration while counting it separately from true StackEngine
  default integration outputs.
- Surface counts for StackEngine CPU masters, resident masters, legacy masters,
  StackEngine integration outputs, resident integration outputs, explicit CUDA
  fast-path outputs, and failed runtime-default rows in JSON and Markdown.
- Add focused pipeline-contract tests for a real synthetic CPU audit run, an
  explicit non-resident CUDA fast-path artifact, and a malformed legacy-master
  runtime-default regression.
- Keep this gate runtime-contract scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 294: Acceptance/Phase2 StackEngine Runtime Default Handoff

- Carry the S2-Gate 293 `stack_engine_runtime_default_path` pipeline-contract
  evidence into `glass acceptance-audit` and `glass phase2-status`.
- Require acceptance evidence to preserve a present and passing
  runtime-default check, including zero legacy master rows and zero failed
  runtime-default integration rows.
- Require Phase 2 green status to preserve the same acceptance-side
  runtime-default handoff and, when a direct pipeline contract is supplied, the
  direct pipeline-contract runtime-default summary.
- Extend `glass phase2-status-compare` so candidate status artifacts cannot
  drop or fail a previously passing acceptance or direct pipeline
  runtime-default check.
- Surface runtime-default master/integration counts, explicit CUDA fast-path
  counts, legacy master counts, and failed row details in JSON and Markdown.
- Add focused acceptance and Phase 2 tests for passing evidence, legacy-master
  runtime drift, direct pipeline-contract runtime drift, and compare
  regressions.
- Keep this gate status/acceptance scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 295: Default Promotion StackEngine Runtime Default Guard

- Carry the S2-Gate 294 Phase 2 runtime-default handoff into
  `glass default-promotion-manifest`.
- Require default-promotion readiness to preserve both acceptance-side and
  direct pipeline-contract `stack_engine_runtime_default_path` evidence before
  a resident CUDA default promotion can remain green.
- Block stale Phase 2 status artifacts that still report green status but do
  not contain Gate294 runtime-default summaries and checks.
- Block acceptance-side legacy master drift, pipeline-side failed integration
  runtime-default rows, missing runtime-default checks, and failed Phase 2
  runtime-default handoff checks.
- Surface acceptance and pipeline runtime-default status, check state, master
  counts, legacy master counts, failed master/output counts, explicit CUDA
  fast-path counts, and failed row details in default-promotion JSON and
  Markdown.
- Add focused default-promotion tests for ready evidence, missing stale
  runtime-default evidence, acceptance-side legacy-master drift,
  pipeline-side runtime-default drift, and CLI Markdown output.
- Keep this gate default-promotion scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 296: Windows Release Matrix StackEngine Runtime Default Guard

- Carry the S2-Gate 295 default-promotion StackEngine runtime-default evidence
  into `glass windows-release-matrix`.
- Require Windows CUDA release-matrix readiness to preserve both
  acceptance-side and direct pipeline runtime-default handoff evidence from the
  default-promotion manifest.
- Block stale default-promotion manifests that still report ready status but do
  not contain Gate295 runtime-default summaries and checks.
- Block acceptance-side legacy master drift, pipeline-side failed integration
  runtime-default rows, missing runtime-default checks, and failed
  default-promotion runtime-default handoff checks before Windows release
  readiness can remain green.
- Surface runtime-default readiness, acceptance/pipeline status, legacy master
  counts, failed master/output counts, explicit CUDA fast-path counts, and
  failed row details in release-matrix JSON and Markdown.
- Add focused release-matrix tests for ready evidence, missing stale
  runtime-default evidence, acceptance-side legacy-master drift,
  pipeline-side failed runtime-default output drift, and CLI Markdown output.
- Keep this gate release-matrix scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 297: Windows Publish Preflight StackEngine Runtime Default Guard

- Carry the S2-Gate 296 Windows release-matrix StackEngine runtime-default
  evidence and S2-Gate 295 default-promotion runtime-default evidence into
  `glass windows-publish-preflight`.
- Require final Windows publish-preflight readiness to preserve both
  release-matrix and default-promotion runtime-default evidence for
  acceptance-side master calibration and pipeline-side light integration
  surfaces.
- Block stale release-matrix or default-promotion manifests that still report
  ready status but do not contain runtime-default summaries and checks.
- Block release-matrix or default-promotion legacy master drift, failed
  runtime-default output rows, missing runtime-default checks, and
  matrix/default-promotion runtime-default mismatches.
- Surface matrix/default-promotion runtime-default readiness, side status,
  legacy master counts, failed output counts, and drift counters in
  publish-preflight JSON and Markdown.
- Add focused publish-preflight tests for ready evidence, missing matrix
  runtime-default evidence, failed matrix runtime-default evidence, failed
  default-promotion runtime-default evidence, and CLI Markdown output.
- Keep this gate publish-preflight scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 298: Phase 2 Publish Preflight Runtime Default Handoff

- Carry the S2-Gate 297 final Windows publish-preflight StackEngine
  runtime-default evidence back into `glass phase2-status`.
- Require Phase 2 green status to preserve matrix-side and default-promotion
  runtime-default readiness, acceptance/pipeline statuses, zero legacy master
  drift, zero failed runtime-default output drift, and matrix/default-promotion
  agreement checks.
- Block stale publish-preflight artifacts that still report
  `publish_preflight_ready` but do not contain the Gate297 runtime-default
  summary and checks.
- Extend `glass phase2-status-compare` so candidate status artifacts cannot
  drop or fail a previously passing final publish-preflight runtime-default
  chain.
- Surface runtime-default readiness, side statuses, check results, legacy
  master counts, and failed output counts in JSON and Markdown.
- Add focused Phase 2 tests for passing evidence, missing stale
  runtime-default evidence, matrix-side runtime-default failure,
  default-promotion runtime-default failure, CLI Markdown output, and compare
  regression.
- Keep this gate status/compare scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 299: StackEngine Publication Audit Runtime Default Handoff

- Carry the S2-Gate 298 Phase 2 publish-preflight StackEngine
  runtime-default handoff back into `glass stack-engine-publication-audit`.
- Require final StackEngine publication-audit readiness to preserve both raw
  Windows publish-preflight runtime-default evidence and the matching Phase 2
  status handoff evidence.
- Block stale publish-preflight or Phase 2 status artifacts that still report
  ready/green status but do not contain Gate297/Gate298 runtime-default summary
  and check fields.
- Cross-check matrix/default-promotion runtime-default readiness,
  acceptance/pipeline statuses, legacy master drift counters, failed output
  counters, and matrix/default-promotion agreement between raw publish-preflight
  and Phase 2 status.
- Surface the new publish-preflight runtime-default and Phase 2 handoff layers
  in StackEngine publication-audit JSON and Markdown.
- Add focused publication-audit tests for ready evidence, missing raw
  publish-preflight runtime-default evidence, failed raw runtime-default
  evidence, missing Phase 2 runtime-default evidence, failed Phase 2 handoff
  evidence, and CLI Markdown output.
- Keep this gate publication-audit scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 300: Release Decision Publication Runtime Default Guard

- Carry the S2-Gate 299 StackEngine publication-audit runtime-default handoff
  into `glass release-promotion-decision`.
- Allow existing release-decision workflows to remain usable without the new
  optional publication-audit input, but require the handoff when
  `--stack-engine-publication-audit` is supplied.
- Block release-candidate/default-change readiness when the supplied
  publication-audit artifact is stale, lacks publish-preflight runtime-default
  layers/checks, or reports failed raw/Phase2 runtime-default evidence.
- Surface publication runtime-default status, raw/Phase2 readiness,
  Phase2-check state, legacy master drift, failed output drift, and failed
  publication checks in release-decision JSON and Markdown.
- Add focused release-decision tests for passing evidence, failed raw
  publication runtime-default evidence, stale missing runtime-default evidence,
  and CLI Markdown output.
- Keep this gate release-decision scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 301: Release Decision Sample Accounting Scope Guard

- Harden `glass release-promotion-decision` so pipeline rejection sample
  accounting and integration sample-closure checks distinguish three release
  states: `passed`, explicitly `not_required`, and missing/stale required
  evidence.
- Require the pipeline contract check to be present and passing before release
  readiness can accept either `passed` or `not_required` sample-accounting
  scope.
- Detect stale pixel-verification artifacts where low/high rejection count maps
  are required but the `rejection_sample_accounting` row is missing, and report
  those rows as `missing_required` instead of generic `not_available`.
- Surface sample-accounting release scope, readiness, required counts,
  verified counts, present counts, and failed rows in release-decision JSON and
  Markdown.
- Add release-decision tests for not-required sample scopes, missing required
  rejection-sample rows, failed sample-count drift, and failed sample-closure
  drift.
- Keep this gate release-decision scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 302: Resident Winsorized Semantics Handoff Backfill

- Harden resident result-contract audits so old resident CUDA runs that omitted
  `integration_results.json` per-output winsorized disclosure can recover
  same-run semantics from `resident_artifacts.json`.
- Allow compatibility completion only when the same run's resident artifact
  contains a `winsorized_sigma` `integration_rejection` descriptor whose
  algorithm matches a known GLASS resident winsorized implementation.
- Complete missing legacy descriptor fields from canonical GLASS constants and
  record the audit source, raw descriptor, completed descriptor,
  `legacy_completion_applied`, and `legacy_completion_source`.
- Preserve the strict Gate260 behavior for artifacts with no integration output
  descriptor and no same-run resident-artifact descriptor; those must still fail
  the resident result contract.
- Re-run the 200-light resident pipeline contract against the existing
  read-only run artifacts and require the release-decision handoff to become
  `default_change_ready` without modifying image outputs.
- Keep this gate resident-contract/audit scoped: no image math change, no CUDA
  kernel change, no runtime default change, no package build/upload, no GitHub
  release creation, and no real-data benchmark rerun.

### S2-Gate 303: Release/Default Promotion Resident Winsorized Visibility

- Surface the Gate302 resident winsorized semantics handoff in
  `release-promotion-decision` as first-class release evidence instead of
  relying only on the aggregate `pipeline_result_contracts_passed` flag.
- Preserve descriptor source, integration-results descriptor presence,
  resident-artifacts descriptor presence, legacy completion count,
  `resident_winsorized_mode`, algorithm, scale estimator, parity status, and
  approximation flags in JSON and Markdown outputs.
- Treat failed required resident winsorized semantics as release blockers while
  keeping sparse historical fixtures compatible when no resident semantics are
  supplied.
- Copy the same release-level resident winsorized summary into
  `default-promotion-manifest` so Windows/default-route publication evidence can
  explain why the resident winsorized path is promotion-ready.
- Generate Gate303 release-decision, Phase2 status, default-promotion manifest,
  and checkpoint artifacts from existing 200-light run evidence.
- Keep this gate visibility/audit scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

### S2-Gate 304: Pipeline Resident Calibration Direct Visibility

- Make `pipeline-contract` directly surface resident calibration visibility
  from `resident_artifacts.json` when a resident-only run has no
  `calibration_artifacts.json` file on disk.
- Build the resident calibration summary in memory only; do not write back to
  the run directory and do not modify image outputs.
- Preserve release/default-promotion fields in the pipeline contract itself:
  resident calibration artifact present, resident calibrated light count,
  resident master surfaces, and resident calibrated-light contracts.
- Require the real 200-light resident run at
  `C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident` to pass
  `pipeline-contract --pixel-verify` without a Gate303 pipeline handoff bundle.
- Re-run release-decision, Phase2 status, and default-promotion manifest using
  the direct Gate304 pipeline contract and require all three to remain ready.
- Keep this gate pipeline-contract scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun. The acceptance fastpath handoff is
  intentionally left for a later gate.

### S2-Gate 305: Acceptance Direct Fastpath Runtime-Default Evidence

- Add an explicit `acceptance-audit --resident-registration-fastpath-json`
  input that can read either a resident fastpath summary or a
  `resident_artifacts.json` file.
- Preserve the existing default behavior: without the explicit input,
  acceptance audit still collects fastpath evidence from `--glass-run`.
- Use the explicit fastpath evidence with the existing benchmark-contract
  fastpath checks so the acceptance artifact records
  `resident_registration_fastpath_contract_status=passed` directly.
- Re-run the real 200-light acceptance audit with:
  - Gate304 direct pipeline contract,
  - Gate211 StackEngine contract,
  - benchmark `benchmarks/phase2_m38_h_200_contract.json`,
  - explicit real-run `resident_artifacts.json` fastpath evidence.
- Require Phase2 status and default-promotion manifest to remain green/ready
  without the Gate303 acceptance handoff bundle.
- Keep this gate acceptance/report scoped: no image math change, no CUDA kernel
  change, no runtime default change, no package build/upload, no GitHub release
  creation, and no real-data benchmark rerun.

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
