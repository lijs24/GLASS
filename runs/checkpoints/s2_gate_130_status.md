# S2 Gate 130 Status

## Gate

S2-Gate 130: Frame-Weight Proposal Direction Audit

## Completed

- Added `glass frame-weight-proposal-audit`.
- The command joins a localized `compare-tile-integration` audit, a
  frame-weight proposal, and a matching tile-pack manifest.
- The audit estimates whether the proposal's focus-family multiplier would move
  each localized signed residual tile toward or away from the reference.
- The audit records predicted master delta in GLASS ADU, transformed reference
  units, before/after signed residual estimates, and per-tile direction flags.
- Added CLI help coverage and focused tests.
- Updated Phase 2 hardening and algorithm source documentation.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\cli.py src\glass\report\frame_weight_proposal_audit.py tests\test_frame_weight_proposal_audit.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_frame_weight_proposal_audit.py tests\test_cli_smoke.py::test_cli_help_commands`
- `.\.venv\Scripts\glass.exe frame-weight-proposal-audit --integration-audit C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.json --proposal C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_control_ratio_proposal.json --out C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_direction_audit.json --markdown C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_direction_audit.md`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_130_doctor.json`
- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`

## Test Results

- Focused ruff: passed.
- Focused tests: `4 passed in 0.84s`.
- Full ruff: passed.
- Full pytest: `346 passed in 34.65s`.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor report: `runs/checkpoints/s2_gate_130_doctor.json`.

## Real Direction Audit

- Input integration audit:
  `C:\glass_runs\phase2_s2_gate_127_tile_integration\agr0p5_f100_f110_integration_audit.json`.
- Input proposal:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_control_ratio_proposal.json`.
- Direction-audit JSON:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_direction_audit.json`.
- Direction-audit Markdown:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\f100_f110_direction_audit.md`.
- Recommendation: `reject_downweight_direction`.
- Mean residual direction: 0 tiles toward, 3 tiles away.
- Tail residual direction: 0 tiles toward, 3 tiles away.
- Example tile 0:
  signed mean `-0.0003904426131072114`, predicted proposal delta
  `-3.267788048924268e-05`, predicted after
  `-0.00042312049359645405`.

## Interpretation

The S2-Gate 129 negative candidate was directionally predictable before a full
200-light rerun: the localized residual tiles were already negative in
GLASS-minus-reference units, and downweighting the positive focus-family
contribution was predicted to make those residuals more negative. This is a
strong guardrail against repeating global frame-wide downweight experiments
without checking residual sign first.

## Known Limitations

- This is a first-order summary audit, not a full reintegration.
- It uses tile-level contribution means, not per-pixel native integration
  contributions.
- It judges proposal direction, not absolute scientific correctness.
- It currently supports the S2-Gate 129 proposal shape and tile-pack residual
  manifests.

## Next Step

S2-Gate 131 should implement a native or near-native tile-local contribution
capture path for the resident integration kernel. That should expose per-frame
accepted contribution and rejection state inside selected tiles without relying
on summary-level first-order approximations.

## Clean-Room Compliance

Compliant. The gate uses only GLASS diagnostic artifacts, GLASS comparison tile
packs, GLASS frame-weight proposal JSON, and user-generated reference outputs.
No proprietary implementation source code was read, copied, summarized, or
reworked.
