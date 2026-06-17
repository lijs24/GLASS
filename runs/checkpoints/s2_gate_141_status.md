# S2-Gate 141 Status - Measured Tile-Local Policy Sweep Summary

## Gate

S2-Gate 141: measured tile-local policy sweep summary.

## Completed

- Added `glass tile-local-policy-sweep` for ranking measured
  `tile-local-policy-decision` artifacts.
- Added a sweep-summary JSON/Markdown writer with accepted/rejected counts,
  top decision, top score, top tile count, and per-decision residual summary
  fields.
- Added focused tests for sweep ranking and CLI output.
- Updated Phase 2 planning and algorithm-source documentation.
- Ran a real-data measured sweep over:
  - Single-tile Gate137 candidate decision generated in this gate.
  - Two-tile Gate140 subset decision.

## Real-Data Artifacts

- Single-tile verification:
  `C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_local_verify.json`
- Single-tile decision:
  `C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.json`
- Sweep summary:
  `C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_vs_subset2_sweep.json`
- Sweep Markdown:
  `C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_vs_subset2_sweep.md`
- Doctor report:
  `runs\checkpoints\s2_gate_141_doctor.json`

## Real-Data Results

- Sweep status: `accepted_candidate_available`.
- Recommendation: `run_broader_measured_sweep`.
- Accepted decisions: `2 / 2`.
- Top decision:
  `C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.json`
- Top score: `1648.4195944947762`.
- Top tile count: `1`.
- Ranked candidates:
  - Single-tile candidate: score `1648.4195944947762`, mean-absolute
    residual delta `-3.508457759369976e-05`, RMS delta
    `-1.3335016901076411e-05`.
  - Two-tile subset candidate: score `1570.7282781537629`, mean-absolute
    residual delta `-9.752933569670108e-06`, RMS delta
    `-1.0975344584092687e-05`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_policy_sweep.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_policy_sweep.py tests\test_tile_local_policy_sweep.py src\glass\cli.py
.\.venv\Scripts\glass.exe tile-local-apply-verify --baseline C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --candidate C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --replay C:\glass_runs\phase2_s2_gate_137_tile_local_apply\f100_f110_signed_mean_replay_tile0_nonoverlap.json --coverage-map C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\integration\resident_coverage_map_H.fits --min-coverage 190 --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --out C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_local_verify.json --markdown C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_local_verify.md --fail-on-failed
.\.venv\Scripts\glass.exe tile-local-policy-decision --verification C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_local_verify.json --apply-experiment C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\tile_local_apply_experiment.json --acceptance-audit C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\acceptance_audit.json --out C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.json --markdown C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.md --fail-on-rejected
.\.venv\Scripts\glass.exe tile-local-policy-sweep --decision C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_policy_decision.json --decision C:\glass_runs\phase2_s2_gate_140_policy_decision\subset2_policy_decision.json --out C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_vs_subset2_sweep.json --markdown C:\glass_runs\phase2_s2_gate_141_policy_sweep\tile0_vs_subset2_sweep.md --fail-on-no-accepted
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_141_doctor.json
```

## Test Results

- Focused pytest: `3 passed`.
- Full pytest: `370 passed in 20.54s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_141_doctor.json`.

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

- The sweep ranks existing measured policy-decision artifacts only.
- It does not run new image processing and does not enable tile-local apply by
  default.
- The top single-tile candidate still needs a broader measured sweep before any
  production policy promotion.

## Next Step

S2-Gate 142 should broaden the measured tile-local sweep across more
non-overlapping residual tiles and frame-family candidates, then compare
whether single-tile or multi-tile policies remain globally safe.

## Clean-Room Compliance

Compliant. This gate consumes GLASS JSON/FITS/XISF artifacts and
user-generated reference outputs only. No proprietary implementation source was
read, copied, summarized, or reworked.
