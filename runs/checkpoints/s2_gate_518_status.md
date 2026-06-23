# S2-Gate 518 Status: Resident DQ Stats Reuse In Provenance

Gate: S2-Gate 518

Status: passed

Date: 2026-06-23 local

## Objective

Continue the Phase 2 DQ/mask pipeline contract work by reducing repeated
resident DQ/provenance full-frame map scans. This gate is a substantive
runtime contract optimization, not a report/default-promotion-only gate.

## Completed

- Added `_resident_dq_map(..., return_stats=True)` for the resident pipeline.
- The returned stats payload records:
  - post-rejection coverage stats;
  - geometric warp coverage stats;
  - geometric zero/partial/full pixel counts;
  - low/high rejection-map contract stats;
  - low/high rejection mask union counts.
- Added `precomputed_dq_stats` to `_resident_dq_coverage_provenance`.
- Reused the DQ-map stats for the source-DQ-off geometric provenance fast path.
- Kept the older provenance reconstruction path for source-DQ-modified runs or
  callers that do not provide precomputed stats.
- Added a focused synthetic test proving precomputed DQ stats feed geometric
  provenance while preserving the existing `_resident_dq_map()` two-value API.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Code Files

- `src/glass/engine/resident_cuda.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `runs/checkpoints/s2_gate_518_dq_stats_reuse_summary.json`

## Real 200-Light Dataset

- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Manifest: `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
- Frames: 200 light, 20 bias, 20 dark, 20 flat
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- Current HEAD pre-change profile:
  `C:\glass_runs\phase2_s2_gate518_profile_current\runs_20260623_094158`
- Gate518 run root:
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619`

## Commands

- `python -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests/test_resident_cuda_run.py -k "dq_map or dq_coverage_provenance"`
- `python -m pytest -q tests/test_resident_cuda_run.py tests/test_resident_stack_surface.py tests/test_stack_engine_contract.py`
- Gate518 real 200-light cold/warm/repeat `glass run` commands under
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619`
- Current HEAD pre-change and after-patch `cProfile` runs.
- Cold/warm FITS bitwise comparison script.
- `glass compare` warm Gate518 master vs WBPP black-box master.
- `glass resident-calibration-contract --fail-on-failed`
- `glass resident-result-contract --pixel-verify --fail-on-failed`
- `glass pipeline-contract --pixel-verify`
- `glass stack-engine-contract --expected-integration-engine cuda_resident_stack --require-default-ready`
- `glass acceptance-audit --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json`
- `python -m pytest -q`
- `glass doctor`

## Test Results

- Focused ruff: passed.
- Focused DQ/provenance pytest: `6 passed, 76 deselected in 0.57 s`.
- Resident CUDA/StackEngine pytest: `100 passed in 11.21 s`.
- Full pytest: `1161 passed in 42.64 s`.
- `glass doctor`: passed.
- Real 200-light cold/warm/repeat runs: passed.
- Warm acceptance audit: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- `nvidia-smi` sampled the GPU at 76% utilization after the Gate518 runs,
  so the slower non-profiled registration timings are recorded as
  contended/variable.

## Real A/B Results

- Pre-change profiled warm internal elapsed: `11.682714099995792 s`.
- After-patch profiled warm internal elapsed: `10.030273599957582 s`.
- Profiled speedup after vs before: `1.164745306652971x`.
- Gate518 cold internal elapsed: `14.709655200014822 s`.
- Gate518 cold shell elapsed: `15.127617 s`.
- Gate518 warm internal elapsed: `9.321247900021262 s`.
- Gate518 warm shell elapsed: `9.754701 s`.
- Gate518 warm-repeat shell elapsed: `9.735261 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Gate518 warm speedup vs WBPP:
  - internal: `117.2097354043666x`;
  - shell: `112.00047033717387x`.

## Timing Evidence

Gate518 warm component timings:

- master build/load: `0.43099960003746673 s`
- light read/upload/calibrate: `2.662712100020144 s`
- resident registration component accounted:
  `3.8077909993264334 s`
- resident registration warp: `0.8559001002577133 s`
- resident integration: `0.45532220002496615 s`
- output write: `0.3431183000211604 s`

DQ/provenance stats-reuse evidence:

- `precomputed_dq_stats_used`: `true`
- `finite_pre_rejection_source`: `geometric_warp_coverage`
- `rejection_reduced_pixels_source`: `low_high_rejection_masks`
- `rejected_sample_count_source`: `low_high_rejection_maps`

## Numerical Evidence

- Gate518 warm vs cold master:
  - bitwise equal: `true`;
  - RMS: `0`;
  - max absolute difference: `0`;
  - p99 absolute difference: `0`.
- Gate518 warm master vs WBPP coverage>=190:
  - shape match: `true`;
  - RMS diff: `0.0017794216505176163`;
  - p99 absolute diff: `0.00042621337808668863`;
  - coverage fraction: `0.960532609259836`.

## Contract Results

- Resident calibration contract: passed.
- Resident result contract: passed with pixel verification.
- Pipeline contract: passed with pixel verification.
- StackEngine contract: passed and default-promotion ready.
- Acceptance audit: passed.

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_518_dq_stats_reuse_summary.json`
- Gate518 cold/warm bitwise comparison:
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\cold_warm_master_compare.json`
- Gate518 warm compare report:
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\warm_auto\s2_gate_518_compare_vs_wbpp.html`
- Gate518 warm acceptance audit:
  `C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\warm_auto\phase2_contract_acceptance_audit_s2_gate_518.json`

## Known Limitations

- This gate optimizes CPU-side DQ/provenance map-pass accounting. It does not
  move DQ map construction itself to CUDA.
- The precomputed stats path is used for the source-DQ-off geometric fast path.
  Source-DQ-modified runs still use the older reconstruction path.
- The non-profiled warm run is slower than Gate517 because the resident
  registration component varied upward under observed GPU utilization; the
  profiled before/after evidence still shows the DQ/provenance path improved.
- Local normalization remains off for this 200-light benchmark route.
- Resident winsorized sigma remains the documented GLASS fast approximation,
  not a claim of exact external algorithm identity.

## Next Step

Return to the now-dominant substantive targets with a quieter GPU: resident
registration/warp residency and light read/upload/calibration overlap.

## Clean-Room Compliance

Compliant. This gate used GLASS source, GLASS artifacts, user-staged M38
H-alpha benchmark inputs, and user-generated WBPP black-box timing/reference
outputs. No official PixInsight/WBPP/PJSR implementation source was read,
copied, summarized, or modified. Original image directories remained read-only.
