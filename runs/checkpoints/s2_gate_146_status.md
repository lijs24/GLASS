# S2-Gate 146 Status - Tile-Local Multiplier Saturation Diagnostics

## Gate

S2-Gate 146: tile-local multiplier saturation diagnostics.

## Completed

- Extended `tile-local-policy-proposal` summary output with explicit
  saturation diagnostics.
- Added summary fields for unconstrained multiplier stats, applied multiplier
  stats, required boost/downweight stats, applied-to-required boost ratio,
  downweight depth ratio, clamped fraction, clamped boost/downweight counts,
  saturation-limited status, and mean residual reduction fraction.
- Added focused unit coverage for clamped boost and zero downweight cases.
- Re-ran the S2-Gate 145 new-region proposal and replay with the richer
  diagnostic summary.
- Updated Phase 2 planning and algorithm-source documentation.

## Real-Data Artifacts

- Saturation proposal JSON:
  `C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_proposal_with_saturation.json`
- Saturation proposal Markdown:
  `C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_proposal_with_saturation.md`
- Compatibility replay JSON:
  `C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_replay_with_saturation.json`
- Compatibility replay Markdown:
  `C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_replay_with_saturation.md`
- Doctor report:
  `runs\checkpoints\s2_gate_146_doctor.json`

## Real-Data Results

- Proposal recommendation: `tile_local_policy_candidate`.
- Replay recommendation: `tile_local_replay_promising`.
- Known direction tiles: `8`.
- Tiles moving toward reference: `8`.
- Clamped tiles: `8`.
- Clamped fraction: `1.0`.
- Saturation limited: `true`.
- Mean residual reduction fraction: `0.009474284284345911`.
- Required boost multiplier stats:
  - Min: `56.52852889405308`.
  - Median: `113.66194787660535`.
  - Mean: `132.90431578176043`.
  - Max: `286.2918427229844`.
- Applied-to-required boost ratio stats:
  - Min: `0.006985878399389804`.
  - Median: `0.017653650954764`.
  - Mean: `0.018736000426309976`.
  - Max: `0.03538036526208635`.

The new diagnostics explain the S2-Gate 145 result: the proposal is
directionally consistent, but the configured `2.0` boost cap reaches only about
`1.87%` of the estimated required boost on average. This argues against simply
promoting the clamped proposal and points to either a different model or a
bounded native apply experiment.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_policy.py
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_policy.py tests\test_tile_local_policy.py
.\.venv\Scripts\glass.exe tile-local-policy-proposal --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --tile-pack C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json --out C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_proposal_with_saturation.json --markdown C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_proposal_with_saturation.md --target-group focus --residual-stat tail_signed_mean --min-multiplier 0.0 --max-multiplier 2.0 --glass-scale 8.764434957115609e-06
.\.venv\Scripts\glass.exe tile-local-policy-replay --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --proposal C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_proposal_with_saturation.json --out C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_replay_with_saturation.json --markdown C:\glass_runs\phase2_s2_gate_146_multiplier_saturation\new_region_policy_replay_with_saturation.md
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_146_doctor.json
```

## Test Results

- Focused pytest: `4 passed in 0.20s`.
- Full pytest: `374 passed in 28.12s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_146_doctor.json`.

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

- This gate adds diagnostics only. It does not run a native tile-local apply
  experiment and does not change output images.
- The unconstrained multiplier estimate still uses tile-level contribution and
  residual means, not a per-pixel resident solve.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 147 should decide between two paths:

- derive a corrected policy model that explains why the required multipliers
  are so large, or
- run a tightly bounded native apply experiment over selected high-signal tiles
  with explicit artifact comparison against both the baseline GLASS master and
  the reference master.

## Clean-Room Compliance

Compliant. This gate uses GLASS contribution, proposal, replay, and diagnostic
artifacts only. No proprietary implementation source was read, copied,
summarized, or reworked.
