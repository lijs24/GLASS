# S2-Gate 186 Status: Minimal CUDA Toolkit Installer Plan

## Gate

- Gate: S2-Gate 186
- Scope: add a driver-safe, explicit CUDA12/CUDA11 minimal Toolkit preparation
  path for Windows release builds.
- Status: green
- Date: 2026-06-17

## Completed

- Added `packaging\windows\install_cuda_toolkit_minimal.ps1`.
- The helper defaults to plan-only mode; no download or install happens unless
  `-Download` or `-Install` is supplied.
- The helper records installer URL, expected SHA256, target root, selected
  components, expected `nvcc.exe`, download/install request flags, and
  `driver_component_included=false`.
- The CUDA12 plan uses `cuda_12.4.1_551.78_windows.exe` with components
  `nvcc_12.4` and `cudart_12.4`.
- The CUDA11 plan uses `cuda_11.8.0_522.06_windows.exe` with components
  `nvcc_11.8` and `cudart_11.8`.
- Extended `glass windows-package-build-plan` so missing `cuda12` and `cuda11`
  variants include minimal Toolkit download/install command text.
- Updated Phase 2, algorithm source, and Windows release documentation.

## Commands Run

```powershell
$tokens=$null; $errors=$null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path packaging\windows\install_cuda_toolkit_minimal.ps1), [ref]$tokens, [ref]$errors)
.\.venv\Scripts\ruff.exe check src\glass\report\windows_package_build_plan.py tests\test_windows_package_build_plan.py tests\test_windows_packaging_scripts.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_package_build_plan.py tests\test_windows_packaging_scripts.py
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda12 -OutJson C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\cuda12_minimal_toolkit_plan.json
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda11 -OutJson C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\cuda11_minimal_toolkit_plan.json
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda12 -OutJson runs\checkpoints\s2_gate_186_cuda12_minimal_toolkit_plan.json
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\install_cuda_toolkit_minimal.ps1 -Label cuda11 -OutJson runs\checkpoints\s2_gate_186_cuda11_minimal_toolkit_plan.json
.\.venv\Scripts\glass.exe windows-package-build-plan --out C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\windows_package_build_plan_with_install_commands.json --markdown C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\windows_package_build_plan_with_install_commands.md
.\.venv\Scripts\glass.exe windows-package-build-plan --out runs\checkpoints\s2_gate_186_windows_package_build_plan_with_install_commands.json --markdown runs\checkpoints\s2_gate_186_windows_package_build_plan_with_install_commands.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- PowerShell parser: passed for `build_portable.ps1` and
  `install_cuda_toolkit_minimal.ps1`.
- Focused ruff: passed.
- Focused pytest: `7 passed in 0.21s`.
- Full ruff: passed.
- Full pytest: `464 passed in 25.51s`.

## Real Artifact Results

- `cuda12` helper artifact status: `plan_only`.
- `cuda11` helper artifact status: `plan_only`.
- `install_requested`: `false`.
- `download_requested`: `false`.
- `driver_component_included`: `false`.
- Refreshed package build plan status: `partial_toolkits`.
- Ready variants: `cuda13`, `cpu`.
- Missing CUDA variants: `cuda12`, `cuda11`.

## Artifacts

- External cuda12 plan:
  `C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\cuda12_minimal_toolkit_plan.json`
- External cuda11 plan:
  `C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\cuda11_minimal_toolkit_plan.json`
- External build plan with install commands:
  `C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\windows_package_build_plan_with_install_commands.json`
- External Markdown build plan:
  `C:\glass_runs\phase2_s2_gate_186_cuda_toolkit_minimal_installer\windows_package_build_plan_with_install_commands.md`
- Checkpoint cuda12 plan:
  `runs\checkpoints\s2_gate_186_cuda12_minimal_toolkit_plan.json`
- Checkpoint cuda11 plan:
  `runs\checkpoints\s2_gate_186_cuda11_minimal_toolkit_plan.json`
- Checkpoint build plan:
  `runs\checkpoints\s2_gate_186_windows_package_build_plan_with_install_commands.json`
- Checkpoint Markdown build plan:
  `runs\checkpoints\s2_gate_186_windows_package_build_plan_with_install_commands.md`

## External Metadata Used

- `winget show Nvidia.CUDA --version 12.4 --source winget`
- `winget show Nvidia.CUDA --version 11.8 --source winget`
- NVIDIA CUDA installation guide component-subpackage model for Windows.

## Known Limitations

- This gate does not download or install CUDA Toolkits.
- Component-scoped installer execution still needs to be validated on this
  machine before claiming CUDA12/CUDA11 build readiness.
- The helper currently covers CUDA12 12.4 and CUDA11 11.8 only.
- If NVIDIA installer component names change, the helper should fail loudly at
  install time and the metadata table must be updated.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used public NVIDIA installer metadata and local GLASS artifacts.
- No input image directory was modified.
- No NVIDIA driver install or modification was requested.

## Next Step

- Run the helper with `-Download` and then `-Install` for `cuda12`, verify
  `glass windows-package-build-plan --fail-on-missing`, and build/smoke the
  CUDA12 package if the Toolkit install succeeds.
