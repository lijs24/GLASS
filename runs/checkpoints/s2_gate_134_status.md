# S2-Gate 134 Status: Resident Tile-Local Policy Contract

## Gate

- Gate: S2-Gate 134
- Name: Resident Tile-Local Policy Contract
- Status: green
- Completed at: 2026-06-01

## Completed Content

- Added an opt-in resident-run argument: `--resident-tile-local-policy-replay`.
- Added `_load_tile_local_policy_replay` validation in `src/glass/engine/resident_cuda.py`.
- Resident artifacts now record validated tile-local replay contracts under
  `resident_integration_weighting.tile_local_policy_replay`.
- The contract is explicitly recorded as `validated_not_applied`; it does not change current frame weights or output pixels.
- Updated Phase 2 plan and algorithm-source ledger.
- Added loader and CUDA smoke coverage in `tests/test_resident_cuda_run.py`.

## Real-Artifact Validation

- Input replay: `C:\glass_runs\phase2_s2_gate_133_tile_local_replay\f100_f110_signed_mean_replay.json`.
- Output contract artifact: `C:\glass_runs\phase2_s2_gate_134_tile_local_contract\f100_f110_signed_mean_contract.json`.
- Validation result:
  - enabled: `True`
  - applied: `False`
  - application_status: `validated_not_applied`
  - tile_count: `3`
  - target_frame_count: `11`
  - recommendation: `tile_local_replay_promising`

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_tile_local_policy_replay_loader_validates_contract tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_134_doctor.json --allow-cpu-only
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused ruff: passed.
- Focused loader/help tests: `2 passed in 1.02s`.
- Focused resident CUDA smoke: `1 passed in 0.58s`.
- Full ruff: passed.
- Full pytest: `355 passed in 26.78s`.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_134_doctor.json`.

## Known Limitations

- This gate validates and records the tile-local replay contract only.
- The contract is not applied to integration, rejection, DQ maps, coverage maps, or output FITS files.
- Native tile-local accumulation still needs a dedicated CUDA implementation and numerical comparison.

## Next Step

- Implement an opt-in native resident tile-local weighted-mean primitive for the simplest `rejection=none` path, then extend to sigma/winsorized rejection only after CPU/GPU and artifact parity are green.

## Clean-Room Constraint

- This gate consumed GLASS-generated tile-local replay artifacts only.
- No official PixInsight or WBPP/PJSR source code was read, copied, summarized, or reworked.
- Original image directories were not modified.
