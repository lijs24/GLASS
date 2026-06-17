# S2-Gate 137 Status: Bounded 200-Light Tile-Local Apply Experiment

## Gate

S2-Gate 137: Bounded 200-Light Tile-Local Apply Experiment.

## Completed

- Added `glass tile-local-apply-experiment`.
- The command audits a baseline resident CUDA run, a candidate tile-local `apply`
  run, the replay contract, benchmark contract checks, reference compare metrics,
  and candidate-vs-baseline drift.
- Fixed resident DQ provenance so `rejected_sample_count` is sourced from the
  rounded low/high rejection count maps when those maps are available. This keeps
  provenance aligned with the FITS count maps used by acceptance audit.
- Fixed tile-local apply metadata so winsorized/sigma rejection runs record
  `ResidentCalibratedStack.integrate_tile_local_sigma_clip` as the native method.
- Ran a real M38 H-alpha 200-light CUDA resident candidate with tile-local
  `apply` and winsorized sigma rejection.

## Real-Data Artifacts

- Candidate run:
  `C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3`
- Non-overlap replay contract:
  `C:\glass_runs\phase2_s2_gate_137_tile_local_apply\f100_f110_signed_mean_replay_tile0_nonoverlap.json`
- Gate137 audit:
  `C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\tile_local_apply_experiment.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\acceptance_audit.json`
- Candidate vs reference compare:
  `C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\compare_vs_reference_scaled_coverage190.json`
- Candidate vs Gate119 baseline compare:
  `C:\glass_runs\phase2_s2_gate_137_tile_local_apply\agr0p8_apply_signed_mean_tile0_v3\compare_vs_gate119_agr0p8_baseline_coverage190.json`
- Doctor:
  `runs/checkpoints/s2_gate_137_doctor.json`

## Commands

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_apply_experiment.py tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_apply_experiment.py tests\test_tile_local_apply_experiment.py src\glass\cli.py`
- `.\.venv\Scripts\glass.exe run ... --resident-tile-local-policy-replay C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.json --resident-tile-local-policy-mode apply`
- `.\.venv\Scripts\glass.exe run ... --resident-tile-local-policy-replay C:\glass_runs\phase2_s2_gate_137_tile_local_apply\f100_f110_signed_mean_replay_tile0_nonoverlap.json --resident-tile-local-policy-mode apply`
- `.\.venv\Scripts\glass.exe compare ... --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190`
- `.\.venv\Scripts\glass.exe tile-local-apply-experiment ... --fail-on-failed`
- `.\.venv\Scripts\glass.exe acceptance-audit ... --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_137_doctor.json`

## Test Results

- Focused tests: 3 passed.
- Resident/DQ/acceptance focused tests: 12 passed.
- Full suite: 362 passed in 24.16 s.
- Ruff: all checks passed.

## Real-Data Results

- Candidate elapsed: 23.48067960003391 s.
- Reference elapsed: 1092.541 s.
- Speedup vs reference: 46.529360248943654x.
- Frame accounting: 200 input light frames, 193 integrated frames, 7 zero-weight
  frames, 193 registration-accepted frames.
- Tile-local application: `applied_winsorized_sigma`.
- Native tile-local method:
  `ResidentCalibratedStack.integrate_tile_local_sigma_clip`.
- Native tile-local timing: 0.3179596 s.
- Applied scope: 1 non-overlapping tile, 11 target frames.
- Candidate vs reference: shape match true, RMS 0.0014935396635808284,
  abs diff p99 0.00043025553924963024, coverage fraction
  0.9577924192878646.
- Candidate vs Gate119 baseline: shape match true, RMS 0.4234982793915014 ADU,
  relative RMS 0.0016893856378692035, abs diff p99 0.0.
- Acceptance audit: passed.
- Gate137 audit: passed, recommendation `promote_to_bounded_policy_sweep`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native CUDA backend: loaded.

## Known Limitations

- The original three-tile F000100-F000110 replay contract had overlapping tile
  extents and was correctly rejected by the native apply contract. Gate137 used
  a single-tile non-overlap subset for the bounded real experiment.
- The bounded replay predicts localized residual improvement; a broader
  localized post-apply residual package is still needed before enabling any
  automatic multi-tile/global policy.
- Tile-local apply remains opt-in. The resident default is still `record`.
- Candidate runtime is slower than the Gate119 no-apply baseline because this
  gate adds a rejection-aware tile-local native pass and full audit maps, but it
  remains within the release benchmark contract and above the speedup floor.

## Next Step

S2-Gate 138 should generate non-overlapping tile-local policy subsets
automatically, run a bounded policy sweep over more residual tiles, and add
localized post-apply residual verification instead of relying only on replay
prediction.

## Clean-Room Compliance

Compliant. This gate used GLASS artifacts, user-generated black-box reference
outputs, benchmark contracts, and image comparisons only. It did not read,
copy, summarize, or rework proprietary implementation source.
