# S2-Gate 517 Status: Resident DQ Provenance Fast Path

Gate: S2-Gate 517

Status: passed

Date: 2026-06-23 local

## Objective

Reduce the post-Gate516 real 200-light warm-path overhead in the resident
DQ/provenance path without changing calibration, registration, warp, rejection,
integration, DQ flag semantics, output maps, or final pixels.

## Completed

- Profiled the Gate516 warm-cache route and identified the remaining Python
  DQ/provenance map-pass costs:
  - `_resident_dq_map`;
  - `_output_diagnostics`;
  - `_resident_dq_coverage_provenance`;
  - `_resident_count_map_array_stats`.
- Batched output diagnostic percentiles into one `np.percentile` call.
- Reused clipping masks/counts in output diagnostics instead of recomputing
  boolean reductions.
- Made `_resident_dq_map` emit a resident fast DQ summary from the masks used to
  build the map, avoiding a full `DQMask.summary()` pass over all defined flags.
- Made count-map stats record contract fields with a `count_map_contract_fields`
  profile.
- Made DQ coverage provenance reuse geometric warp coverage as finite
  pre-rejection coverage when source-DQ applied zero invalid samples.
- Kept fallback to the previous `post_rejection_coverage + low/high rejection
  maps` path when source-DQ changes samples.
- Added DQ/provenance tests for the geometric fast path and source-DQ fallback.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Code Files

- `src/glass/engine/resident_cuda.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `runs/checkpoints/s2_gate_517_dq_provenance_fastpath_summary.json`

## Real 200-Light Dataset

- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Manifest: `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
- Frames: 200 light, 20 bias, 20 dark, 20 flat
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- Profile run root:
  `C:\glass_runs\phase2_s2_gate517_profile\runs_20260623_074248`
- Optimized run root:
  `C:\glass_runs\phase2_s2_gate517_dq_provenance_fastpath\runs_20260623_074736`

## Commands

- `python -m ruff check src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- Focused DQ/provenance tests:
  `python -m pytest -q tests/test_resident_cuda_run.py::test_resident_dq_map_marks_no_data_and_rejections tests/test_resident_cuda_run.py::test_resident_dq_map_marks_geometric_warp_edges_without_no_data tests/test_resident_cuda_run.py::test_resident_dq_coverage_provenance_separates_rejection_from_pre_rejection tests/test_resident_cuda_run.py::test_resident_dq_coverage_provenance_includes_geometric_warp_coverage tests/test_resident_cuda_run.py::test_resident_dq_coverage_provenance_falls_back_when_source_dq_changes_samples tests/test_resident_result_contract.py tests/test_pipeline_contract.py::test_pipeline_contract_pixel_verification_reports_resident_rejection_sample_accounting`
- `python -m pytest -q tests/test_resident_cuda_run.py tests/test_resident_stack_surface.py tests/test_stack_engine_contract.py`
- Optimized cold/warm real 200-light `glass run` commands under
  `C:\glass_runs\phase2_s2_gate517_dq_provenance_fastpath\runs_20260623_074736`.
- Cold/warm FITS bitwise comparison script.
- `glass compare` warm optimized master vs WBPP black-box master.
- `glass resident-calibration-contract --fail-on-failed`
- `glass resident-result-contract --pixel-verify --fail-on-failed`
- `glass pipeline-contract --pixel-verify`
- `glass stack-engine-contract --expected-integration-engine cuda_resident_stack --require-default-ready`
- `glass acceptance-audit --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json`
- `python -m pytest -q`
- `glass doctor`

## Test Results

- Focused ruff: passed.
- Focused DQ/provenance/result-contract pytest: `21 passed in 0.67 s`.
- Resident CUDA/StackEngine pytest: `99 passed in 8.88 s`.
- Full pytest: `1160 passed in 42.39 s`.
- `glass doctor`: passed.
- Real 200-light cold/warm optimized runs: passed.
- Warm acceptance audit: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real A/B Results

- Gate516 warm internal elapsed: `11.345701600017492 s`.
- Gate516 warm shell elapsed: `11.712763 s`.
- Gate517 cold internal elapsed: `12.870977100043092 s`.
- Gate517 warm internal elapsed: `8.503292900044471 s`.
- Gate517 cold shell elapsed: `13.25686 s`.
- Gate517 warm shell elapsed: `8.854115 s`.
- Gate517 warm vs Gate516 internal speedup:
  `1.3342715267350318x`.
- Gate517 warm vs Gate516 shell speedup:
  `1.3228609522239094x`.
- WBPP black-box elapsed: `1092.541 s`.
- Gate517 warm speedup vs WBPP:
  - internal: `128.48446041348123x`;
  - shell: `123.39358592021901x`.

## Timing Evidence

Optimized warm component timings:

- master build/load: `0.40851680003106594 s`
- light read/upload/calibrate: `2.542228999955114 s`
- resident registration component accounted:
  `1.9585369000975243 s`
- resident registration warp: `0.4736267992993817 s`
- resident integration: `0.303468799975235 s`
- output write: `0.3315862999879755 s`

DQ/provenance fast-path evidence:

- `finite_pre_rejection_source`: `geometric_warp_coverage`
- `source_dq_applied_invalid_samples`: `0`
- low/high rejection stats profile: `count_map_contract_fields`
- `stack_engine_surface_contract.passed`: `true`

## Numerical Evidence

- Gate517 warm vs cold master:
  - bitwise equal: `true`;
  - RMS: `0`;
  - max absolute difference: `0`;
  - p99 absolute difference: `0`.
- Gate517 warm master vs WBPP coverage>=190:
  - shape match: `true`;
  - RMS diff: `0.0017794216505176163`;
  - p99 absolute diff: `0.00042621337808668863`;
  - coverage fraction: `0.960532609259836`;
  - coverage max/median: `193` / `192`.

## Contract Results

- Resident calibration contract: passed.
- Resident result contract: passed with pixel verification.
- Pipeline contract: passed with pixel verification.
- StackEngine contract: passed and default-promotion ready.
- Acceptance audit: passed.

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_517_dq_provenance_fastpath_summary.json`
- Gate517 cold/warm bitwise comparison:
  `C:\glass_runs\phase2_s2_gate517_dq_provenance_fastpath\runs_20260623_074736\cold_warm_master_compare.json`
- Gate517 warm compare report:
  `C:\glass_runs\phase2_s2_gate517_dq_provenance_fastpath\runs_20260623_074736\warm_auto\s2_gate_517_compare_vs_wbpp.html`
- Gate517 warm acceptance audit:
  `C:\glass_runs\phase2_s2_gate517_dq_provenance_fastpath\runs_20260623_074736\warm_auto\phase2_contract_acceptance_audit_s2_gate_517.json`
- Gate517 warm acceptance markdown:
  `C:\glass_runs\phase2_s2_gate517_dq_provenance_fastpath\runs_20260623_074736\warm_auto\phase2_contract_acceptance_audit_s2_gate_517.md`

## Known Limitations

- This gate optimizes resident DQ/provenance CPU-side map passes. It does not
  move DQ map construction to CUDA yet.
- The geometric pre-rejection fast path is used only when source-DQ has applied
  zero invalid samples. Source-DQ-modified runs fall back to the older
  coverage+rejection-map reconstruction.
- Local normalization remains off for this 200-light benchmark route.
- Resident winsorized sigma remains the documented GLASS fast approximation,
  not a claim of exact external algorithm identity.

## Next Step

Return to the now-dominant warm-path costs: light read/upload/calibration
overlap and resident registration/warp residency.

## Clean-Room Compliance

Compliant. This gate used GLASS source, GLASS artifacts, user-staged M38
H-alpha benchmark inputs, and user-generated WBPP black-box timing/reference
outputs. No official PixInsight/WBPP/PJSR implementation source was read,
copied, summarized, or modified. Original image directories remained read-only.
