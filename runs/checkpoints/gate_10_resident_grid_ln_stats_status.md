# Gate 10 Status: Resident CUDA Grid Local Normalization Stats

## Gate

Gate 10: Local Normalization resident CUDA increment.

## Completed

- Added GPU-side resident pair-grid statistics for local normalization:
  - `ResidentCalibratedStack.frame_pair_grid_stats(reference_index, source_index, tile_height, tile_width)`
  - The CUDA kernel computes per-tile paired source/reference mean, standard deviation, and valid pixel counts while frames remain resident in VRAM.
- Wired resident CLI execution to choose:
  - `--resident-local-normalization-mode global_mean_std`
  - `--resident-local-normalization-mode grid_mean_std`
  - `--resident-local-normalization-tile-size N`
- Resident grid LN now computes coefficient grids, applies them directly to the resident calibrated/registered frame, and records the coefficient grid in `local_norm_results.json`.
- Updated capability flags and CUDA/LN documentation.

## Commands Run

```powershell
& cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "<repo>\.venv\Scripts\cmake.exe" --build "<repo>\build\native-cuda"'
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass_cuda.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py::test_resident_stack_grid_stats_can_drive_in_vram_normalization tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_ncc_subpixel_registration_smoke
.\.venv\Scripts\python.exe -m pytest -q tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_cli_smoke.py
.\.venv\Scripts\python.exe -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py src\glass_cuda.py src\glass\capabilities.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py tests\test_capabilities.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "import glass_cuda; print(glass_cuda.cuda_available()); print(glass_cuda.get_device_info(0) if glass_cuda.cuda_available() else {})"
```

## Test Result

- Native CUDA rebuild: passed.
- Targeted resident grid LN tests: `2 passed`.
- Resident/CLI smoke subset: `32 passed`.
- Full pytest: `171 passed in 7.89s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Native backend: true.

## Known Limitations

- Grid LN is piecewise constant per tile; it is not yet a smoothed/interpolated WBPP-equivalent local model.
- Coefficient audit tables are copied to host for JSON reporting, but full frames remain resident for estimation and application.
- The current real M38 WBPP comparison run did not enable this new grid LN mode; it still needs a dedicated real-data timing/parity run if LN is required in the reference workflow.

## Next Step

- Run a controlled resident CUDA real-data subset with `--resident-local-normalization-mode grid_mean_std` if the PixInsight/WBPP reference enables comparable local normalization.
- Continue refining residual parity at the low-coverage borders and robust rejection behavior.

## Clean-room

- Compliant. No official PixInsight/WBPP/PJSR source was read or copied.
- This change uses only project code, synthetic tests, and clean-room CUDA/Python implementation.
