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
