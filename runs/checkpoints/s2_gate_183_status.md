# S2-Gate 183 Status - Windows Portable Package Smoke

## Gate

- Gate: S2-Gate 183
- Scope: Add and exercise an auditable smoke test for Windows portable packages.
- Status: green

## Completed

- Added `glass windows-package-smoke`.
- The command validates portable package structure and optional zip artifact.
- The command executes `glass-doctor.cmd --json ...` and `glass.cmd --help` by default.
- The command records execution return codes, output tails, generated portable doctor JSON, CUDA status, source stamp, zip size, checks, failed checks, and limitations.
- Added structure-only fixture tests and CLI tests.
- Built a fresh CPU portable package with the existing Windows packaging script.
- Ran real package smoke against `.release\windows\GLASS` and `.release\windows\GLASS-Portable-win64.zip`.

## Real Build Evidence

- Build command: `powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\build_portable.ps1 -Python .\.venv\Scripts\python.exe`
- Portable root: `.release\windows\GLASS`
- Portable zip: `.release\windows\GLASS-Portable-win64.zip`
- Zip size: `290938309` bytes
- Source stamp: `4b54e77`
- External artifact root: `C:\glass_runs\phase2_s2_gate_183_windows_package_smoke`
- External JSON: `C:\glass_runs\phase2_s2_gate_183_windows_package_smoke\cpu_portable_smoke.json`
- External Markdown: `C:\glass_runs\phase2_s2_gate_183_windows_package_smoke\cpu_portable_smoke.md`
- Checkpoint JSON: `runs/checkpoints/s2_gate_183_cpu_portable_smoke.json`
- Checkpoint Markdown: `runs/checkpoints/s2_gate_183_cpu_portable_smoke.md`
- Help output: `runs/checkpoints/s2_gate_183_windows_package_smoke_help.txt`

## Smoke Result

- Status: `package_smoke_passed`
- Passed: `true`
- Recommendation: `portable_package_ready_for_next_release_step`
- `glass-doctor.cmd` return code: `0`
- `glass.cmd --help` return code: `0`
- Portable doctor product: `GLASS`
- Portable CUDA availability: `false`
- CUDA requirement for this CPU package smoke: `false`
- Failed checks: none

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\windows_package_smoke.py src\glass\cli.py tests\test_windows_package_smoke.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_package_smoke.py tests\test_cli_smoke.py::test_cli_help_commands`
- `powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\build_portable.ps1 -Python .\.venv\Scripts\python.exe`
- `.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64.zip --expected-source 4b54e77 --out C:\glass_runs\phase2_s2_gate_183_windows_package_smoke\cpu_portable_smoke.json --markdown C:\glass_runs\phase2_s2_gate_183_windows_package_smoke\cpu_portable_smoke.md --fail-on-failure`
- `.\.venv\Scripts\glass.exe windows-package-smoke --package-root .release\windows\GLASS --zip .release\windows\GLASS-Portable-win64.zip --expected-source 4b54e77 --out runs\checkpoints\s2_gate_183_cpu_portable_smoke.json --markdown runs\checkpoints\s2_gate_183_cpu_portable_smoke.md --fail-on-failure`
- `.\.venv\Scripts\glass.exe windows-package-smoke --help > runs\checkpoints\s2_gate_183_windows_package_smoke_help.txt`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused package smoke tests: `4 passed`
- Full suite: `457 passed in 23.54 s`
- Ruff: `All checks passed`

## CUDA

- This gate built and smoked the CPU portable package only.
- Portable doctor detects the local RTX PRO 6000 but reports CUDA unavailable because the CPU package does not include the native CUDA module.
- Gate182 remains the matrix guard for CUDA package compatibility; a future gate must smoke actual CUDA portable variants with `--require-cuda`.

## Known Limitations

- The portable source stamp is `4b54e77`, the clean HEAD before the Gate183 commit; this is expected because the smoke command and checkpoint are committed after the package is built. A public release package should be rebuilt after the final release commit.
- This gate does not build CUDA 13/12/11 portable variants.
- This gate does not run on a separate clean Windows user account or produce an installer smoke.
- The package zip is generated under `.release/` and is intentionally not committed.

## Next Step

- S2-Gate 184 should build and smoke a CUDA 13 portable package on this machine with `windows-package-smoke --require-cuda`, then decide whether cuda12/cuda11 package smoke should be true native builds or matrix-backed fallback artifacts.

## Clean-Room

- Compliant. This gate consumes GLASS-built package artifacts and GLASS doctor output only.
- No official PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Original image directories were not touched.
