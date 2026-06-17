# S2-Gate 138 Status: Non-Overlapping Tile-Local Policy Subsets

## Gate

S2-Gate 138: Non-Overlapping Tile-Local Policy Subsets.

## Completed

- Added `glass tile-local-policy-subset`.
- The command converts a `tile_local_policy_replay` artifact into a native
  apply-compatible non-overlapping subset while preserving the replay artifact
  type.
- Added greedy selection strategies:
  `canonical_delta_abs`, `residual_reduction`, and `tile_index`.
- Added optional `--max-tiles`.
- The subset artifact records source replay, strategy, original tile count,
  selected tile count, overlap drops, limit drops, recalculated replay summary,
  and Markdown output.
- Fixed resident tile-local apply metadata so rejection-aware apply records
  `ResidentCalibratedStack.integrate_tile_local_sigma_clip`.
- Preserved S2-Gate 137 DQ provenance fix where rejected sample count is sourced
  from rounded low/high rejection maps.

## Real-Data Artifacts

- Subset replay:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\f100_f110_signed_mean_nonoverlap_subset.json`
- Candidate run:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2`
- Gate138 audit:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\tile_local_apply_experiment.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\acceptance_audit.json`
- Candidate vs reference compare:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\compare_vs_reference_scaled_coverage190.json`
- Candidate vs Gate119 baseline compare:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\compare_vs_gate119_agr0p8_baseline_coverage190.json`
- Doctor:
  `runs/checkpoints/s2_gate_138_doctor.json`

## Commands

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_policy_subset.py tests\test_cli_smoke.py::test_cli_help_commands tests\test_resident_cuda_run.py::test_cli_resident_cuda_tile_local_policy_apply_winsorized_sigma_records_rejection_maps`
- `.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_policy_subset.py tests\test_tile_local_policy_subset.py src\glass\cli.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\glass.exe tile-local-policy-subset --replay C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.json --out C:\glass_runs\phase2_s2_gate_138_tile_local_subset\f100_f110_signed_mean_nonoverlap_subset.json --markdown C:\glass_runs\phase2_s2_gate_138_tile_local_subset\f100_f110_signed_mean_nonoverlap_subset.md --strategy canonical_delta_abs`
- `.\.venv\Scripts\glass.exe run ... --resident-tile-local-policy-replay C:\glass_runs\phase2_s2_gate_138_tile_local_subset\f100_f110_signed_mean_nonoverlap_subset.json --resident-tile-local-policy-mode apply`
- `.\.venv\Scripts\glass.exe compare ... --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --min-coverage 190`
- `.\.venv\Scripts\glass.exe tile-local-apply-experiment ... --fail-on-failed`
- `.\.venv\Scripts\glass.exe acceptance-audit ... --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_138_doctor.json`

## Test Results

- Focused tests: 4 passed.
- Full suite: 364 passed in 20.97 s.
- Ruff: all checks passed.

## Real-Data Results

- Source replay tiles: 3.
- Selected non-overlapping tiles: 2 (`tile_index` 0 and 1).
- Dropped overlap tiles: 1 (`tile_index` 2 overlapped selected tile 0).
- Replay-predicted mean abs residual before: 0.0002566484785796774.
- Replay-predicted mean abs residual after: 0.00020892611227803543.
- Candidate elapsed: 24.03055700007826 s.
- Reference elapsed: 1092.541 s.
- Speedup vs reference: 45.46465568802429x.
- Frame accounting: 200 input light frames, 193 integrated frames, 7 zero-weight
  frames, 193 registration-accepted frames.
- Tile-local application: `applied_winsorized_sigma`.
- Native tile-local method:
  `ResidentCalibratedStack.integrate_tile_local_sigma_clip`.
- Native tile-local timing: 0.4166845 s.
- Applied scope: 2 non-overlapping tiles, 11 target frames.
- Candidate vs reference: shape match true, RMS 0.0014935039757264037,
  abs diff p99 0.0004277635575272148, coverage fraction
  0.9577924192878646.
- Candidate vs Gate119 baseline: shape match true, RMS 0.5905409370490585 ADU,
  relative RMS 0.002355738916006848, abs diff p99 4.372062683105469 ADU.
- Acceptance audit: passed.
- Gate138 audit: passed, recommendation `promote_to_bounded_policy_sweep`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native CUDA backend: loaded.

## Known Limitations

- Subset selection is greedy. It is deterministic, auditable, and native-safe,
  but not globally optimal.
- The selected 2-tile policy still relies on replay-predicted localized
  improvement. A post-apply localized residual package is still required before
  global policy promotion.
- Tile-local apply remains opt-in. The resident default remains `record`.
- Candidate runtime includes full audit maps and the rejection-aware tile-local
  native pass; it remains within the release benchmark contract and above the
  speedup floor.

## Next Step

S2-Gate 139 should add localized post-apply residual verification for selected
tile-local policies: compare candidate, baseline, and reference cutouts for the
selected tiles and verify measured residual movement rather than relying only on
the replay prediction.

## Clean-Room Compliance

Compliant. This gate used GLASS artifacts, user-generated black-box reference
outputs, benchmark contracts, and image comparisons only. It did not read,
copy, summarize, or rework proprietary implementation source.
