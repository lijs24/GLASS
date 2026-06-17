# S2-Gate 145 Status - New-Region Tile-Local Proposal Replay

## Gate

S2-Gate 145: new-region tile-local policy proposal and summary replay.

## Completed

- Ran `glass tile-local-policy-proposal` on the S2-Gate 144 new-region
  resident contribution artifact.
- Used the F000100-F000110 focus group, tail-signed-mean residuals, and the
  current GLASS scale factor for proposal replay.
- Ran `glass tile-local-policy-replay` to measure before/after residual
  movement over all selected new-region tiles.
- Updated Phase 2 planning documentation and algorithm-source notes.
- Kept this as a proposal/replay gate only. No image pixels were changed and
  no default policy was promoted.

## Real-Data Artifacts

- Proposal JSON:
  `C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_proposal.json`
- Proposal Markdown:
  `C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_proposal.md`
- Replay JSON:
  `C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_replay.json`
- Replay Markdown:
  `C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_replay.md`
- Doctor report:
  `runs\checkpoints\s2_gate_145_doctor.json`

## Real-Data Results

- Proposal recommendation: `tile_local_policy_candidate`.
- Replay recommendation: `tile_local_replay_promising`.
- Tiles moving toward reference: `8`.
- Tiles moving away from reference: `0`.
- Boost tiles: `8`.
- Downweight tiles: `0`.
- Clamped tiles: `8`.
- Mean absolute residual before replay: `0.005786728459787161`.
- Mean absolute residual after replay: `0.005742790954133888`.
- Mean residual reduction fraction: `0.009474284284345911`.
- Canonical delta contribution mean: `5.013158962130547 ADU`.
- Multiplier mean/min/max: `2.0` / `2.0` / `2.0`.

The direction is consistent across all new-region tiles, but the measured
summary-level reduction is small and every tile hits the maximum boost
multiplier. This is useful evidence, but not enough to promote the policy to a
native default apply path.

## Commands Run

```powershell
.\.venv\Scripts\glass.exe tile-local-policy-proposal --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --tile-pack C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json --out C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_proposal.json --markdown C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_proposal.md --target-group focus --residual-stat tail_signed_mean --min-multiplier 0.0 --max-multiplier 2.0 --glass-scale 8.764434957115609e-06
.\.venv\Scripts\glass.exe tile-local-policy-replay --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --proposal C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_proposal.json --out C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_replay.json --markdown C:\glass_runs\phase2_s2_gate_145_new_region_policy\new_region_policy_replay.md
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_145_doctor.json
```

## Test Results

- Full pytest: `374 passed in 25.19s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_145_doctor.json`.

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

- This gate is a summary replay over GLASS-owned contribution artifacts. It is
  not a native resident integration apply experiment.
- All selected tiles clamp to the configured maximum boost multiplier, so the
  multiplier policy is not yet well calibrated.
- Mean residual reduction is only about `0.95%`, which is directionally useful
  but too small for promotion.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 146 should either run a bounded native apply experiment for the
new-region proposal or derive a better multiplier policy that avoids universal
max-boost clamping. The key acceptance question is whether a real integration
artifact improves residual tails without hurting the already-good agreement
regions or runtime profile.

## Clean-Room Compliance

Compliant. This gate consumes GLASS candidate, resident contribution, proposal,
and replay artifacts only. No proprietary implementation source was read,
copied, summarized, or reworked.
