# S2-Gate 142 Status - Tile-Local Sweep Plan And Alternate Non-Overlap Candidate

## Gate

S2-Gate 142: tile-local sweep plan and broader measured candidate.

## Completed

- Added `glass tile-local-sweep-plan`.
- The command emits a reproducible command queue for tile-local policy subset,
  resident run, reference compare, baseline compare, apply-experiment,
  acceptance-audit, local verification, policy decision, and final sweep.
- Generated a real sweep plan from the F000100-F000110 signed-mean tile-local
  replay.
- Tested the requested max-three-tile expansion under the non-overlap safety
  rule.
- Found that the source replay has three tiles but only two can be applied
  together safely because tile `0` overlaps tile `2`.
- Measured an alternate non-overlap two-tile candidate selected by
  `residual_reduction`: tiles `[1, 2]`.
- Ran the alternate candidate through resident CUDA 200-light integration,
  compare, apply-experiment, acceptance-audit, local verification, policy
  decision, and final sweep.

## Real-Data Artifacts

- Sweep plan:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\sweep_plan.json`
- Sweep plan Markdown:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\sweep_plan.md`
- Canonical max-three subset attempt:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\replays\f100_f110_canonical_delta_abs_tiles3.json`
- Alternate measured replay:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\replays\f100_f110_residual_reduction_tiles3.json`
- Alternate measured run:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3`
- Alternate local verification:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\verification\f100_f110_residual_reduction_tiles3_verify.json`
- Alternate decision:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\decisions\f100_f110_residual_reduction_tiles3_decision.json`
- Final sweep:
  `C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\policy_sweep.json`
- Doctor report:
  `runs\checkpoints\s2_gate_142_doctor.json`

## Real-Data Results

- Source replay tile count: `3`.
- Canonical max-three request selected tiles `[0, 1]` and dropped tile `2`
  because it overlaps tile `0`.
- Residual-reduction max-three request selected the new non-overlap pair
  `[1, 2]` and dropped tile `0` because it overlaps tile `2`.
- Alternate candidate resident CUDA runtime: `29.755390100181103 s`.
- Alternate candidate acceptance status: `passed`.
- Alternate candidate speedup vs black-box WBPP timing: `36.717414771629905`.
- Alternate candidate reference compare:
  - RMS diff: `0.001493568961548754`.
  - P99 abs diff: `0.0004330911836586907`.
- Alternate local verification: `passed`.
- Alternate local mean-absolute residual delta:
  `-5.6820524454927364e-08`.
- Alternate local RMS delta: `-1.435975460531327e-05`.
- Alternate decision: `accepted`.
- Alternate score: `1564.4165751297683`.
- Final measured sweep:
  - Accepted decisions: `3 / 3`.
  - Top decision:
    `C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.json`
  - Top score: `1648.4195944947762`.
  - Ranking:
    1. Single tile `[0]`: score `1648.4195944947762`.
    2. Canonical two-tile `[0, 1]`: score `1570.7282781537629`.
    3. Alternate two-tile `[1, 2]`: score `1564.4165751297683`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_sweep_plan.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_sweep_plan.py tests\test_tile_local_sweep_plan.py src\glass\cli.py
.\.venv\Scripts\glass.exe tile-local-sweep-plan --replay C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.json --root C:\glass_runs\phase2_s2_gate_142_tile_local_sweep --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\sweep_plan.json --markdown C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\sweep_plan.md --max-tiles 3 --strategy residual_reduction --candidate-prefix f100_f110 --base-run-command C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\run_command.txt --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --baseline-run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --baseline-master C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190 --existing-decision C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.json --existing-decision C:\glass_runs\phase2_s2_gate_140_policy_decision\subset2_policy_decision.json
.\.venv\Scripts\glass.exe tile-local-policy-subset --replay C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.json --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\replays\f100_f110_residual_reduction_tiles3.json --markdown C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\replays\f100_f110_residual_reduction_tiles3.md --strategy residual_reduction --max-tiles 3
.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3 --backend cuda --until-stage integration --memory-mode resident --resident-master-cache-dir C:\glass_runs\phase2_s2_gate_15_200\resident_master_cache --resident-registration similarity_cuda_triangle --resident-warp-interpolation lanczos3 --resident-warp-clamping-threshold 0.3 --resident-star-threshold 350 --resident-star-max-candidates 48 --reference-frame-id F000196 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-output-maps audit --flat-floor 0.05 --resident-tile-local-policy-replay C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\replays\f100_f110_residual_reduction_tiles3.json --resident-tile-local-policy-mode apply
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\compare_vs_reference_scaled_coverage190.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\compare_vs_baseline_coverage190.html --glass-coverage-map C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\integration\resident_coverage_map_H.fits --min-coverage 190
.\.venv\Scripts\glass.exe tile-local-apply-experiment --baseline-run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --candidate-run C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3 --replay C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\replays\f100_f110_residual_reduction_tiles3.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --candidate-compare-json C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\compare_vs_reference_scaled_coverage190.json --candidate-vs-baseline-json C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\compare_vs_baseline_coverage190.json --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\tile_local_apply_experiment.json --markdown C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\tile_local_apply_experiment.md --fail-on-failed
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\compare_vs_reference_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\acceptance_audit.json --markdown C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\acceptance_audit.md --benchmark-contract benchmarks\phase2_m38_h_200_contract.json
.\.venv\Scripts\glass.exe tile-local-apply-verify --baseline C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --candidate C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --replay C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\replays\f100_f110_residual_reduction_tiles3.json --coverage-map C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\verification\f100_f110_residual_reduction_tiles3_verify.json --markdown C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\verification\f100_f110_residual_reduction_tiles3_verify.md --fail-on-failed
.\.venv\Scripts\glass.exe tile-local-policy-decision --verification C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\verification\f100_f110_residual_reduction_tiles3_verify.json --apply-experiment C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\tile_local_apply_experiment.json --acceptance-audit C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\runs\f100_f110_residual_reduction_tiles3\acceptance_audit.json --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\decisions\f100_f110_residual_reduction_tiles3_decision.json --markdown C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\decisions\f100_f110_residual_reduction_tiles3_decision.md --fail-on-rejected
.\.venv\Scripts\glass.exe tile-local-policy-sweep --decision C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.json --decision C:\glass_runs\phase2_s2_gate_140_policy_decision\subset2_policy_decision.json --decision C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\decisions\f100_f110_residual_reduction_tiles3_decision.json --out C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\policy_sweep.json --markdown C:\glass_runs\phase2_s2_gate_142_tile_local_sweep\policy_sweep.md --fail-on-no-accepted
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_142_doctor.json
```

## Test Results

- Focused pytest: `3 passed`.
- Full pytest: `372 passed in 21.18s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_142_doctor.json`.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Recommended package: `cuda`.

## Known Limitations

- No legal three-tile non-overlap candidate exists in the current
  F000100-F000110 replay because tile `0` overlaps tile `2`.
- The alternate `[1, 2]` candidate is safe and accepted but has much weaker
  local mean-absolute residual improvement than the single-tile and canonical
  two-tile candidates.
- The new plan command generates command queues; it does not execute them and
  does not enable tile-local apply by default.

## Next Step

S2-Gate 143 should mine additional localized residual families or generate a
larger non-overlapping tile pack, because this replay has reached its
non-overlap ceiling. The next useful promotion evidence needs more independent
tiles, not more reshuffling of the same three tile extents.

## Clean-Room Compliance

Compliant. This gate consumes GLASS replay/decision/run artifacts and
user-generated reference outputs only. No proprietary implementation source was
read, copied, summarized, or reworked.
