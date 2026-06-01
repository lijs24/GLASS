# S2-Gate 133 Status: Tile-Local Policy Replay

## Gate

- Gate: S2-Gate 133
- Name: Tile-Local Policy Replay
- Status: green
- Completed at: 2026-06-01

## Completed Content

- Added `glass tile-local-policy-replay`.
- Added `src/glass/report/tile_local_policy_replay.py`.
- Added unit and CLI tests for summary-level tile-local replay.
- Updated `docs/phase2_algorithm_hardening.md` and `docs/algorithm_sources.md`.
- Generated real-data replay artifacts from the S2-Gate 131 resident contribution artifact and S2-Gate 132 policy proposals:
  - `C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.json`
  - `C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.md`
  - `C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_tail_replay.json`
  - `C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_tail_replay.md`

## Real-Data Result

- Signed-mean replay recommendation: `tile_local_replay_promising`.
- Signed-mean tiles moving toward reference: 3 / 3.
- Signed-mean mean abs residual before / after: `0.00022419545100954487` / `0.00017668149320412265`.
- Tail replay recommendation: `tile_local_replay_promising`.
- Tail tiles moving toward reference: 3 / 3.
- Tail mean abs residual before / after: `0.0010444056136785509` / `0.0009968916558731288`.
- All three replayed tiles found 11 selected F000100-F000110 focus frame rows.
- Per-frame contribution sums matched canonical proposal contributions for the signed-mean replay.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_policy_replay.py tests\test_tile_local_policy_replay.py src\glass\cli.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_policy_replay.py tests\test_tile_local_policy.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_policy_replay.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe tile-local-policy-replay --help
.\.venv\Scripts\glass.exe tile-local-policy-replay --contribution C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.json --proposal C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_signed_mean_policy.json --out C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.json --markdown C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.md
.\.venv\Scripts\glass.exe tile-local-policy-replay --contribution C:\glass_runs\phase2_s2_gate_131_resident_tile_contribution\agr0p5_f100_f110_resident_contribution.json --proposal C:\glass_runs\phase2_s2_gate_132_tile_local_policy\f100_f110_tail_policy.json --out C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_tail_replay.json --markdown C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_tail_replay.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_133_doctor.json --allow-cpu-only
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused ruff: passed.
- Focused tests: `6 passed in 0.40s`.
- CLI help focused test: `3 passed in 0.75s`.
- Full ruff: passed.
- Full pytest: `354 passed in 22.01s`.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_133_doctor.json`.

## Known Limitations

- This gate replays policy summaries only; it does not modify production integration output.
- It does not write image pixels and is not a per-pixel resident native integration replay.
- The promising result is directional evidence for a future native tile-local integration gate, not a promoted default.

## Next Step

- Implement an opt-in native/resident tile-local integration experiment that applies localized multipliers during accumulation while preserving DQ, coverage, rejection maps, timing diagnostics, and the existing default behavior.

## Clean-Room Constraint

- This gate consumed GLASS-generated resident contribution and policy artifacts only.
- No official PixInsight or WBPP/PJSR source code was read, copied, summarized, or reworked.
- Input image directories were not modified.
