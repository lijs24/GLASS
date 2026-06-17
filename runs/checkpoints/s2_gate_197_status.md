# S2-Gate 197 Status: Windows GitHub Release Script

## Gate

- Gate: S2-Gate 197
- Scope: generate a reviewable, dry-run PowerShell publish script for the
  strict same-source Windows package release plan.
- Status: green
- Date: 2026-06-18

## Completed

- Extended `glass windows-github-release-plan` with `--script`.
- The generated script verifies GitHub CLI authentication, release asset
  existence, recorded asset byte sizes, SHA256 hashes, and release notes before
  upload.
- The script is dry-run by default and requires the explicit `-Publish` switch
  before invoking `gh release create`.
- The release plan JSON records the generated script path and default script
  mode.
- The release plan Markdown now surfaces the script path and dry-run mode.
- Updated the Windows release checklist and Phase 2 gate document.
- Regenerated the real release handoff artifacts from the strict same-source
  Windows release manifest.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\windows_github_release_plan.py src\glass\cli.py tests\test_windows_github_release_plan.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_github_release_plan.py tests\test_cli_smoke.py
.\.venv\Scripts\ruff.exe check src\glass\report\windows_github_release_plan.py tests\test_windows_github_release_plan.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_github_release_plan.py
$root='C:\glass_runs\phase2_s2_gate_197_windows_release_publish_script'
New-Item -ItemType Directory -Force -Path $root | Out-Null
$gh="$env:ProgramFiles\GitHub CLI\gh.exe"
$common=@(
  'windows-github-release-plan',
  '--manifest','runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json',
  '--tag','v0.1.0-windows-gpu.9',
  '--title','GLASS v0.1.0-windows-gpu.9 Windows CUDA packages',
  '--require-same-source-stamp',
  '--check-gh',
  '--check-gh-auth',
  '--gh-path',$gh,
  '--fail-on-failure'
)
& .\.venv\Scripts\glass.exe @common --out "$root\github_release_plan_publish_script.json" --markdown "$root\github_release_plan_publish_script.md" --notes "$root\github_release_notes.md" --script "$root\publish_github_release.ps1"
& .\.venv\Scripts\glass.exe @common --out runs\checkpoints\s2_gate_197_github_release_plan_publish_script.json --markdown runs\checkpoints\s2_gate_197_github_release_plan_publish_script.md --notes runs\checkpoints\s2_gate_197_github_release_notes.md --script runs\checkpoints\s2_gate_197_publish_github_release.ps1
[System.Management.Automation.Language.Parser]::ParseFile('runs\checkpoints\s2_gate_197_publish_github_release.ps1',[ref]$tokens,[ref]$errors)
powershell -NoProfile -ExecutionPolicy Bypass -File runs\checkpoints\s2_gate_197_publish_github_release.ps1
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor --allow-cpu-only
```

## Test Results

- Focused ruff: passed.
- Focused pytest: `18 passed in 1.94s`.
- Script-template focused pytest after syntax/auth-guard fix:
  `4 passed in 0.22s`.
- PowerShell parser check: passed, `publish script syntax ok`.
- Publish script dry-run without GitHub CLI auth: blocked as expected with exit
  code 1 and message `GitHub CLI authentication check failed`.
- Full ruff: passed.
- Full pytest: `474 passed in 25.30s`.

## CUDA Status

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability
  12.0, VRAM 97886 MiB, driver 596.21.
- Windows package try order reported by `glass doctor`: cuda13, cuda12, cuda11,
  cpu.

## Release Plan Result

- Status: `release_plan_ready`.
- Passed: `true`.
- Publication ready: `false`.
- Recommendation: `authenticate_github_cli_then_run_release_command`.
- Tag: `v0.1.0-windows-gpu.9`.
- Package count: `4`.
- `gh.available`: `true`.
- `gh.auth_ok`: `false`.

## Artifacts

- External root:
  `C:\glass_runs\phase2_s2_gate_197_windows_release_publish_script`
- Checkpoint release plan JSON:
  `runs\checkpoints\s2_gate_197_github_release_plan_publish_script.json`
- Checkpoint release plan Markdown:
  `runs\checkpoints\s2_gate_197_github_release_plan_publish_script.md`
- Checkpoint release notes:
  `runs\checkpoints\s2_gate_197_github_release_notes.md`
- Checkpoint publish script:
  `runs\checkpoints\s2_gate_197_publish_github_release.ps1`

## Known Limitations

- No GitHub release was created.
- No tag was created.
- No package assets were uploaded.
- The generated script cannot publish until GitHub CLI authentication succeeds
  on this machine.
- No new real-data image-processing benchmark was run in this gate because this
  was a release automation gate only.
- A first parser pass caught a PowerShell trailing-comma syntax issue in the
  generated script; the template was fixed and the regenerated script now
  parses successfully.
- A follow-up dry-run check confirmed that failed `gh auth status` now stops
  the script before any release upload path.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS release manifests, GLASS package paths, local GitHub
  CLI status, and local package checksums.
- No input image directory was modified.

## Next Step

- Authenticate GitHub CLI, rerun the release plan with `--check-gh-auth`, then
  run the generated publish script without `-Publish` once for verification and
  with `-Publish` only when the reviewed assets should be uploaded.
