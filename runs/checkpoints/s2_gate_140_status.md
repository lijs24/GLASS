# S2-Gate 140 Status: Measured Tile-Local Policy Decision

## Gate

S2-Gate 140: Measured Tile-Local Policy Decision.

## Completed

- Added `glass tile-local-policy-decision`.
- The command ranks one or more `tile-local-apply-verify` artifacts.
- It gates the top measured candidate with optional `tile-local-apply-experiment`
  and `acceptance-audit` artifacts.
- It emits per-candidate checks, global checks, score, failed reasons, top
  candidate, accepted/rejected status, and Markdown output.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md` for S2-Gates 137-140.

## Real-Data Artifacts

- Decision JSON:
  `C:\glass_runs\phase2_s2_gate_140_policy_decision\subset2_policy_decision.json`
- Decision Markdown:
  `C:\glass_runs\phase2_s2_gate_140_policy_decision\subset2_policy_decision.md`
- Verification input:
  `C:\glass_runs\phase2_s2_gate_139_tile_local_verify\subset2_local_verify.json`
- Apply experiment input:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\tile_local_apply_experiment.json`
- Acceptance audit input:
  `C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\acceptance_audit.json`
- Doctor:
  `runs/checkpoints/s2_gate_140_doctor.json`

## Commands

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_policy_decision.py tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_policy_decision.py tests\test_tile_local_policy_decision.py src\glass\cli.py`
- `.\.venv\Scripts\glass.exe tile-local-policy-decision --verification C:\glass_runs\phase2_s2_gate_139_tile_local_verify\subset2_local_verify.json --apply-experiment C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\tile_local_apply_experiment.json --acceptance-audit C:\glass_runs\phase2_s2_gate_138_tile_local_subset\agr0p8_apply_signed_mean_subset2\acceptance_audit.json --out C:\glass_runs\phase2_s2_gate_140_policy_decision\subset2_policy_decision.json --markdown C:\glass_runs\phase2_s2_gate_140_policy_decision\subset2_policy_decision.md --fail-on-rejected`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_140_doctor.json`

## Test Results

- Focused tests: 3 passed.
- Full suite: 368 passed in 20.50 s.
- Ruff: all checks passed.

## Real-Data Results

- Decision status: accepted.
- Recommendation: `promote_measured_subset_to_sweep_candidate`.
- Candidate count: 1.
- Accepted candidate count: 1.
- Top score: 1570.7282781537629.
- Failed reasons: none.
- Thresholds:
  - min signed-mean improved fraction: 1.0.
  - min RMS improved fraction: 1.0.
  - min mean-absolute-residual improved fraction: 0.0.
  - require aggregate mean-absolute-residual improvement: true.
  - require aggregate RMS improvement: true.
- Verification checks:
  - tile count: 2.
  - signed mean improved fraction: 1.0.
  - RMS improved fraction: 1.0.
  - mean absolute residual improved fraction: 0.5.
  - aggregate mean absolute residual delta: -0.000009752933569670108.
  - aggregate RMS delta: -0.000010975344584092687.
- Global checks:
  - apply experiment passed.
  - acceptance audit passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native CUDA backend: loaded.

## Known Limitations

- This is a promotion-control artifact only. It does not mutate pipeline outputs
  and does not enable tile-local apply by default.
- The accepted subset is a measured sweep candidate, not a globally promoted
  policy.
- Current scoring is intentionally simple and auditable. It ranks by pass state,
  improvement fractions, and aggregate residual deltas, not by a trained or
  optimized scientific objective.

## Next Step

S2-Gate 141 should run a small measured sweep over subset strategy and
`max_tiles`, then produce a sweep summary using `tile-local-policy-decision` for
each candidate.

## Clean-Room Compliance

Compliant. This gate used GLASS JSON artifacts, GLASS benchmark contracts, and
user-generated black-box reference outputs only. It did not read, copy,
summarize, or rework proprietary implementation source.
