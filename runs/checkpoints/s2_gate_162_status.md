# S2-Gate 162 Status: Resident Runtime Repeat Plan

## Gate

S2-Gate 162: Resident Runtime Repeat Plan

## Completed

- Added `glass resident-runtime-repeat-plan`.
- Added `src/glass/report/resident_runtime_repeat_plan.py`.
- Added focused tests in `tests/test_resident_runtime_repeat_plan.py`.
- Added CLI help coverage for `resident-runtime-repeat-plan`.
- Generated a real three-repeat plan from the Gate160 `throughput-v1`
  `run_command.txt`.
- Updated Phase 2 and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_runtime_repeat_plan.py tests/test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\glass.exe resident-runtime-repeat-plan --base-run-command C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\run_command.txt --root C:\glass_runs\phase2_s2_gate_162_repeat_plan --label throughput_v1 --repeats 3 --cache-state dedicated_io_window --out C:\glass_runs\phase2_s2_gate_162_repeat_plan\repeat_plan.json --markdown C:\glass_runs\phase2_s2_gate_162_repeat_plan\repeat_plan.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_162_doctor.json
```

## Test Results

- Focused tests: `3 passed in 0.76s`.
- Full tests: `276 passed, 127 skipped in 16.28s`.
- CUDA test skip reason: GPU externally busy at `100%` utilization with
  approximately `54930/97887 MiB` used.
- Ruff: `All checks passed!`.
- Doctor report: `runs/checkpoints/s2_gate_162_doctor.json`.

## Artifacts

- Repeat plan JSON:
  `C:\glass_runs\phase2_s2_gate_162_repeat_plan\repeat_plan.json`
- Repeat plan Markdown:
  `C:\glass_runs\phase2_s2_gate_162_repeat_plan\repeat_plan.md`

## Planned Repeat Runs

- `throughput_v1_repeat01`
- `throughput_v1_repeat02`
- `throughput_v1_repeat03`

All three runs preserve the Gate160 science/runtime command and replace only
the `--out` directory. The plan also emits a final `glass
resident-runtime-compare` command for the repeat outputs.

## CUDA Status

- CUDA wrapper importable: yes.
- Native CUDA extension loaded: yes.
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Known Limitations

- Planning gate only. It does not execute the three 200-light repeats.
- Full pytest skipped CUDA tests because an unrelated process was saturating
  the GPU.
- The repeat plan labels the intended I/O condition as `dedicated_io_window`,
  but enforcing that condition remains an operator/runtime scheduling step.

## Next Step

Execute the three planned repeats when the GPU and disks are in a controlled
window, then run the generated `resident-runtime-compare` command to quantify
warm-cache/dedicated-I/O variance.

## Clean-Room Compliance

Compliant. This gate reads a GLASS-owned `run_command.txt` and writes GLASS
planning artifacts only. It does not read proprietary source code, execute image
processing, read image pixels, modify input data, or change defaults.
