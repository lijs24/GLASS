# S2-Gate 196 Status: GitHub CLI Auth Preflight

## Gate

- Gate: S2-Gate 196
- Scope: distinguish GitHub CLI installation readiness from authenticated
  publication readiness for the Windows package release plan.
- Status: green
- Date: 2026-06-18

## Completed

- Merged the remote README-only update into local `main`.
- Pushed local `main` to `origin/main`; remote is now updated through merge
  commit `cf154b7`.
- Installed GitHub CLI 2.94.0 with winget.
- Attempted `gh auth login --web`; the GitHub device-code endpoint timed out on
  the local network.
- Extended `glass windows-github-release-plan` with `--gh-path` and
  `--check-gh-auth`.
- Regenerated the release handoff plan against the strict same-source Windows
  manifest with explicit `gh` path and auth check.

## Commands Run

```powershell
git fetch origin
git show --patch 94a2147 -- README.md
git merge origin/main
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
git push origin main
winget install --id GitHub.cli --source winget --accept-source-agreements --accept-package-agreements
& "$env:ProgramFiles\GitHub CLI\gh.exe" --version
& "$env:ProgramFiles\GitHub CLI\gh.exe" auth status
& "$env:ProgramFiles\GitHub CLI\gh.exe" auth login --hostname github.com --git-protocol ssh --web --scopes repo
.\.venv\Scripts\ruff.exe check src\glass\report\windows_github_release_plan.py src\glass\cli.py tests\test_windows_github_release_plan.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_github_release_plan.py tests\test_cli_smoke.py
$root='C:\glass_runs\phase2_s2_gate_196_github_cli_auth_preflight'
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
& .\.venv\Scripts\glass.exe @common --out "$root\github_release_plan_auth_preflight.json" --markdown "$root\github_release_plan_auth_preflight.md" --notes "$root\github_release_notes.md"
& .\.venv\Scripts\glass.exe @common --out runs\checkpoints\s2_gate_196_github_release_plan_auth_preflight.json --markdown runs\checkpoints\s2_gate_196_github_release_plan_auth_preflight.md --notes runs\checkpoints\s2_gate_196_github_release_notes.md
```

## Test Results

- Pre-push ruff: passed.
- Pre-push full pytest: `473 passed in 25.53s`.
- Focused ruff after auth-preflight changes: passed.
- Focused pytest after auth-preflight changes: `18 passed in 2.05s`.

## GitHub Status

- Code push: succeeded, `main -> origin/main`.
- Remote README update merged: `94a2147 Update README.md`.
- Local merge commit: `cf154b7`.
- GitHub CLI installed: `gh version 2.94.0`.
- GitHub CLI auth: not authenticated.
- `gh auth login --web`: failed to reach
  `https://github.com/login/device/code` due to local network timeout.
- VPN settings were not inspected or changed.

## Release Plan Result

- Status: `release_plan_ready`.
- Passed: `true`.
- Publication ready: `false`.
- Recommendation: `authenticate_github_cli_then_run_release_command`.
- Tag: `v0.1.0-windows-gpu.9`.
- Source stamp: `aa63510`.
- Package count: `4`.
- `gh.available`: `true`.
- `gh.auth_ok`: `false`.

## Artifacts

- External root:
  `C:\glass_runs\phase2_s2_gate_196_github_cli_auth_preflight`
- Checkpoint release plan JSON:
  `runs\checkpoints\s2_gate_196_github_release_plan_auth_preflight.json`
- Checkpoint release plan Markdown:
  `runs\checkpoints\s2_gate_196_github_release_plan_auth_preflight.md`
- Checkpoint release notes:
  `runs\checkpoints\s2_gate_196_github_release_notes.md`

## Known Limitations

- No GitHub release was created.
- No tag was created.
- No package assets were uploaded.
- Publication now requires successful `gh auth login` or another authenticated
  GitHub release-upload path.
- No new real-data image-processing benchmark was run in this gate.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS manifest metadata, GLASS package paths, local Git
  metadata, and GitHub CLI status output.
- No input image directory was modified.

## Next Step

- Authenticate GitHub CLI when network access to the device-code endpoint is
  available, rerun the auth preflight, then create the GitHub release using the
  generated command in the release-plan Markdown.
