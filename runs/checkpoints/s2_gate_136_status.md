# S2-Gate 136 Status: Opt-In Resident Tile-Local Rejection

## Gate

S2-Gate 136: opt-in tile-local policy application for resident sigma and winsorized rejection.

## Completed Content

- Added native CUDA rejection-aware tile-local integration:
  - `ResidentCalibratedStack.integrate_tile_local_sigma_clip`
  - CUDA launch: `glass_integrate_resident_tile_local_sigma_clip_f32_launch`
- Added Python wrapper support in `glass_cuda.ResidentCalibratedStack`.
- Added forward CLI mode:
  - `--resident-tile-local-policy-mode apply`
- Preserved Gate135 compatibility:
  - `record` remains the default.
  - `apply_mean` remains available and limited to `rejection=none`.
- Extended resident engine routing:
  - `apply` + `rejection=none` uses `integrate_tile_local_mean`.
  - `apply` + `sigma_clip` uses `integrate_tile_local_sigma_clip`.
  - `apply` + `winsorized_sigma` uses `integrate_tile_local_sigma_clip` with winsorization enabled.
- The rejection-aware path writes the normal resident outputs:
  - master
  - weight map
  - coverage map
  - low rejection map
  - high rejection map
  - DQ map when selected by output policy
- Reused the S2-Gate135 replay validation:
  - target frame membership
  - image-bounded half-open tile extents
  - non-overlapping tile extents
  - finite non-negative multipliers
- Added native timing and applied-mode diagnostics to `resident_artifacts.json`.
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_tile_local_sigma_clip_matches_cpu_reference tests/test_resident_cuda_run.py::test_cli_resident_cuda_tile_local_policy_apply_winsorized_sigma_records_rejection_maps tests/test_resident_cuda_run.py::test_cli_resident_cuda_tile_local_policy_apply_mean_changes_target_tile`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py tests/test_resident_cuda_run.py::test_tile_local_policy_application_arrays_build_apply_contract tests/test_resident_cuda_run.py::test_tile_local_policy_replay_loader_validates_contract tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_136_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\glass.exe run --help | Select-String -Pattern "resident-tile-local-policy-mode|apply_mean|apply enables"`
- `.\.venv\Scripts\glass.exe audit --help | Select-String -Pattern "resident-tile-local-policy-mode|apply_mean|apply enables"`
- `.\.venv\Scripts\python.exe -c "import glass_cuda,json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices() if glass_cuda.cuda_available() else []}, ensure_ascii=False, indent=2))"`

## Test Results

- Native CUDA build: passed.
- Gate136 focused pytest: `3 passed in 1.17s`.
- Resident CUDA regression pytest: `35 passed in 0.43s`.
- Ruff: passed.
- Full pytest: `360 passed in 20.51s`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA toolkit used for this native build: CUDA 13.2.

## Artifacts

- `runs/checkpoints/s2_gate_136_status.md`
- `runs/checkpoints/s2_gate_136_doctor.json`

## Known Limitations

- Tile-local policy application remains opt-in; default mode remains `record`.
- Fused-matrix resident integration does not support tile-local policy application.
- The rejection primitive follows the current GLASS resident two-pass sigma/winsorized approximation; it is not claimed to be a PixInsight-equivalent rejection implementation.
- The 200-light real benchmark was not rerun in this gate. Promotion of a tile-local policy still requires benchmark-contract, frame-accounting, and image-agreement validation on the real dataset.

## Next Step

S2-Gate 137 should run a bounded real-data `apply` experiment against the 200-light benchmark contract, comparing frame accounting, runtime, output drift, and localized residual changes before any default behavior is considered.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- The implementation uses GLASS-owned replay artifacts and project-defined CUDA rejection logic.
- Input image directories were not modified.
