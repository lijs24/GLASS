# S2-Gate 135 Status: Opt-In Resident Tile-Local Mean

## Gate

S2-Gate 135: Opt-in resident tile-local weighted mean for `tile-local-policy-replay`.

## Completed Content

- Added a native CUDA resident stack primitive:
  - `ResidentCalibratedStack.integrate_tile_local_mean`
  - CUDA launch: `glass_integrate_resident_tile_local_weighted_mean_f32_launch`
- Added Python wrapper support in `glass_cuda.ResidentCalibratedStack`.
- Added resident CLI routing:
  - `--resident-tile-local-policy-mode record`
  - `--resident-tile-local-policy-mode apply_mean`
- Kept the default behavior as `record`, preserving S2-Gate 134 output semantics.
- Implemented opt-in application only for resident stack dispatch with `rejection=none`.
- Added validation for:
  - replay artifact presence when `apply_mean` is requested
  - target frame membership in the active light group
  - positive image-bounded half-open tile extents
  - non-overlapping tile extents
  - finite non-negative multipliers
- Added resident artifact diagnostics for applied mode:
  - requested/effective mode
  - applied status
  - target frame and tile counts
  - multiplier statistics
  - native timing
  - mean-only limitations
- Updated:
  - `docs/phase2_algorithm_hardening.md`
  - `docs/algorithm_sources.md`

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_cuda_resident_stack.py::test_resident_stack_tile_local_mean_matches_cpu_reference tests/test_resident_cuda_run.py::test_tile_local_policy_application_arrays_build_apply_contract tests/test_resident_cuda_run.py::test_cli_resident_cuda_tile_local_policy_apply_mean_changes_target_tile`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_tile_local_policy_replay_loader_validates_contract tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_external_matrix_registration tests/test_cuda_resident_stack.py`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_135_doctor.json --allow-cpu-only`
- `.\.venv\Scripts\glass.exe run --help | Select-String -Pattern "resident-tile-local-policy-mode|resident-tile-local-policy-replay"`
- `.\.venv\Scripts\glass.exe audit --help | Select-String -Pattern "resident-tile-local-policy-mode|resident-tile-local-policy-replay"`
- `.\.venv\Scripts\python.exe -c "import glass_cuda,json; print(json.dumps({'cuda_available': glass_cuda.cuda_available(), 'devices': glass_cuda.list_devices() if glass_cuda.cuda_available() else []}, ensure_ascii=False, indent=2))"`

## Test Results

- Native CUDA build: passed.
- Focused Gate135 pytest: `3 passed in 0.96s`.
- Resident CUDA regression pytest: `33 passed in 0.49s`.
- Ruff: passed.
- Full pytest: `358 passed in 24.13s`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- CUDA toolkit used for this native build: CUDA 13.2.

## Artifacts

- `runs/checkpoints/s2_gate_135_status.md`
- `runs/checkpoints/s2_gate_135_doctor.json`

## Known Limitations

- Tile-local policy application is opt-in only; default remains record-only.
- Tile-local policy application currently supports `rejection=none` weighted mean only.
- Sigma clipping and winsorized sigma rejection still record the replay contract without applying tile-local multipliers.
- This gate does not yet produce tile-local low/high rejection maps or DQ-specific tile-local provenance beyond the normal resident output maps.
- The 200-light real benchmark was not rerun in this gate; this was a native primitive and routing gate with synthetic/smoke validation.

## Next Step

S2-Gate 136 should evaluate a real-data tile-local mean candidate or extend tile-local support into rejection-aware resident integration, with guardrails against frame-accounting and image-agreement regressions.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- The implementation uses GLASS-owned replay artifacts and project-defined weighted-mean CUDA logic.
- Input image directories were not modified.
