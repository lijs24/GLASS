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
