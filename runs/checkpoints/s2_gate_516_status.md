# S2-Gate 516 Status: Resident Surface Contract Stats Reuse

Gate: S2-Gate 516

Status: passed

Date: 2026-06-23 local

## Objective

Return to the Phase 2 performance mainline by removing a real 200-light
warm-path bottleneck: repeated full-frame output-map scans inside the resident
StackEngine surface-contract builder.

## Completed

- Profiled the current default warm 200-light route and confirmed the largest
  unaccounted Python cost was resident surface-contract construction, not the
  registration kernels.
- Added optional precomputed map-stat support to
  `build_resident_integration_stack_surface_contract`.
- Kept the old full-scan behavior as the default builder behavior when no
  precomputed stats are supplied.
- Made resident CUDA runs provide surface-contract statistics from evidence
  already produced during the same resident pass:
  - master: output diagnostics;
  - weight: output diagnostics;
  - coverage: DQ coverage provenance;
  - low/high rejection maps: one resident count-map statistics pass;
  - DQ: DQ summary created when the DQ map was built.
- Preserved the independent disk-backed audit path through
  `glass resident-result-contract --pixel-verify`.
- Added a unit test proving the precomputed surface-contract path does not call
  the full `_finite_stats` scan.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Code Files

- `src/glass/engine/resident_stack_surface.py`
- `src/glass/engine/resident_cuda.py`
- `tests/test_resident_stack_surface.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`
- `runs/checkpoints/s2_gate_516_surface_contract_stats_reuse_summary.json`

## Real 200-Light Dataset

- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Manifest: `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
- Frames: 200 light, 20 bias, 20 dark, 20 flat
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- Pre-change current-default A/B root:
  `C:\glass_runs\phase2_s2_gate516_current_default_ab\runs_20260623_072959`
- Optimized run root:
  `C:\glass_runs\phase2_s2_gate516_surface_contract_stats_reuse\runs_20260623_073659`

## Commands

- `python -m ruff check src\glass\engine\resident_stack_surface.py src\glass\engine\resident_cuda.py tests\test_resident_stack_surface.py`
- `python -m pytest -q tests/test_resident_stack_surface.py`
- `python -m pytest -q tests/test_resident_cuda_run.py tests/test_resident_stack_surface.py tests/test_stack_engine_contract.py tests/test_pipeline_contract.py::test_pipeline_contract_passes_resident_result_contract tests/test_pipeline_contract.py::test_pipeline_contract_pixel_verification_reports_resident_rejection_sample_accounting tests/test_acceptance_audit.py::test_acceptance_audit_applies_dq_provenance_contract`
- Pre-change current-default cold/warm real 200-light `glass run` commands under
  `C:\glass_runs\phase2_s2_gate516_current_default_ab\runs_20260623_072959`.
- Optimized cold/warm real 200-light `glass run` commands under
  `C:\glass_runs\phase2_s2_gate516_surface_contract_stats_reuse\runs_20260623_073659`.
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
- Resident surface contract pytest: `3 passed in 0.04 s`.
- Focused resident/contract pytest: `101 passed in 8.98 s`.
- Resident result-contract pytest: `15 passed in 0.40 s`.
- Full pytest: `1159 passed in 42.43 s`.
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

- Pre-change current-default warm internal elapsed:
  `16.68259979999857 s`.
- Gate515 warm internal elapsed:
  `16.721956100023817 s`.
- Optimized cold internal elapsed:
  `15.793169700016733 s`.
- Optimized warm internal elapsed:
  `11.345701600017492 s`.
- Optimized cold shell elapsed:
  `16.184504 s`.
- Optimized warm shell elapsed:
  `11.712763 s`.
- Optimized warm vs pre-change current-default internal speedup:
  `1.4703894380558054x`.
- Optimized warm vs Gate515 internal speedup:
  `1.4738582671694835x`.
- WBPP black-box elapsed: `1092.541 s`.
- Optimized warm speedup vs WBPP:
  - internal: `96.29558739657982x`;
  - shell: `93.27782010102995x`.

## Timing Evidence

Optimized warm component timings:

- master build/load: `0.4150375999743119 s`
- light read/upload/calibrate: `2.5498815999599174 s`
- resident registration component accounted:
  `1.9595927005411453 s`
- resident registration warp: `0.47263460024259984 s`
- resident integration: `0.3089101000223309 s`
- output write: `0.2958422999945469 s`

Surface-contract evidence:

- `stack_engine_surface_contract.passed`: `true`
- `dq_summary_matches_dq_map` source:
  `trusted_precomputed_dq_summary`
- `master_is_finite` source: `resident_output_diagnostics`
- map stats sources:
  - master: `resident_output_diagnostics`
  - weight: `resident_output_diagnostics`
  - coverage: `resident_dq_coverage_provenance`
  - low rejection: `resident_precomputed_count_map`
  - high rejection: `resident_precomputed_count_map`
  - DQ: `resident_dq_summary`

## Numerical Evidence

- Optimized warm vs cold master:
  - bitwise equal: `true`;
  - RMS: `0`;
  - max absolute difference: `0`;
  - p99 absolute difference: `0`.
- Optimized warm master vs WBPP coverage>=190:
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
  `runs/checkpoints/s2_gate_516_surface_contract_stats_reuse_summary.json`
- Optimized cold/warm bitwise comparison:
  `C:\glass_runs\phase2_s2_gate516_surface_contract_stats_reuse\runs_20260623_073659\cold_warm_master_compare.json`
- Optimized warm compare report:
  `C:\glass_runs\phase2_s2_gate516_surface_contract_stats_reuse\runs_20260623_073659\warm_auto\s2_gate_516_compare_vs_wbpp.html`
- Optimized warm acceptance audit:
  `C:\glass_runs\phase2_s2_gate516_surface_contract_stats_reuse\runs_20260623_073659\warm_auto\phase2_contract_acceptance_audit_s2_gate_516.json`
- Optimized warm acceptance markdown:
  `C:\glass_runs\phase2_s2_gate516_surface_contract_stats_reuse\runs_20260623_073659\warm_auto\phase2_contract_acceptance_audit_s2_gate_516.md`

## Known Limitations

- This gate optimizes contract construction. It does not change calibration,
  registration, warp, rejection, DQ, integration, or output pixels.
- The independent disk-backed pixel verifier remains required for strict audit
  evidence when publishing benchmark claims.
- Local normalization remains off for this 200-light benchmark route.
- Resident winsorized sigma remains the documented GLASS fast approximation,
  not a claim of exact external algorithm identity.

## Next Step

Return to the two remaining substantive warm-path costs: light
read/upload/calibration overlap and resident registration/warp residency.

## Clean-Room Compliance

Compliant. This gate used GLASS source, GLASS artifacts, user-staged M38
H-alpha benchmark inputs, and user-generated WBPP black-box timing/reference
outputs. No official PixInsight/WBPP/PJSR implementation source was read,
copied, summarized, or modified. Original image directories remained read-only.
