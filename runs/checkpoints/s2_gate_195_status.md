# S2-Gate 195 Status: GitHub Release Handoff Plan

## Gate

- Gate: S2-Gate 195
- Scope: prepare GitHub release notes and upload command from the strict
  Windows release manifest.
- Status: green
- Date: 2026-06-17

## Completed

- Added `glass windows-github-release-plan`.
- Generated a release plan for tag `v0.1.0-windows-gpu.9`.
- Generated release notes with asset sizes and SHA256 digests.
- Recorded that GitHub CLI is missing from PATH on this checkpoint machine.
- Updated Phase 2, release, and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\windows_github_release_plan.py src\glass\cli.py tests\test_windows_github_release_plan.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_github_release_plan.py tests\test_cli_smoke.py
git ls-remote --tags origin
$root='C:\glass_runs\phase2_s2_gate_195_github_release_plan'
New-Item -ItemType Directory -Force -Path $root | Out-Null
$common=@(
  'windows-github-release-plan',
  '--manifest','runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json',
  '--tag','v0.1.0-windows-gpu.9',
  '--title','GLASS v0.1.0-windows-gpu.9 Windows CUDA packages',
  '--require-same-source-stamp',
  '--check-gh',
  '--fail-on-failure'
)
& .\.venv\Scripts\glass.exe @common --out "$root\github_release_plan.json" --markdown "$root\github_release_plan.md" --notes "$root\github_release_notes.md"
& .\.venv\Scripts\glass.exe @common --out runs\checkpoints\s2_gate_195_github_release_plan.json --markdown runs\checkpoints\s2_gate_195_github_release_plan.md --notes runs\checkpoints\s2_gate_195_github_release_notes.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused ruff: passed.
- Focused pytest: `17 passed in 2.01s`.
- Full ruff: passed.
- Full pytest: `473 passed in 25.64s`.

## Release Plan Result

- Status: `release_plan_ready`.
- Passed: `true`.
- Publication ready: `false`.
- Recommendation: `install_github_cli_then_run_release_command`.
- Tag: `v0.1.0-windows-gpu.9`.
- Title: `GLASS v0.1.0-windows-gpu.9 Windows CUDA packages`.
- Source stamp: `aa63510`.
- Package count: `4`.
- Existing remote tags checked: latest Windows GPU tag found was
  `v0.1.0-windows-gpu.8`; `.9` was not present.

## Planned Assets

- `cuda13`: size `341358345` bytes,
  SHA256 `bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273`.
- `cuda12`: size `341223006` bytes,
  SHA256 `72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31`.
- `cuda11`: size `342200540` bytes,
  SHA256 `2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681`.
- `cpu`: size `296231852` bytes,
  SHA256 `32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d`.

## GitHub Tooling Status

- `gh` CLI: not available on PATH.
- No tag was created.
- No commit was pushed.
- No release was created.
- No asset was uploaded.

## Artifacts

- External root:
  `C:\glass_runs\phase2_s2_gate_195_github_release_plan`
- Checkpoint release plan JSON:
  `runs\checkpoints\s2_gate_195_github_release_plan.json`
- Checkpoint release plan Markdown:
  `runs\checkpoints\s2_gate_195_github_release_plan.md`
- Checkpoint release notes:
  `runs\checkpoints\s2_gate_195_github_release_notes.md`

## Known Limitations

- This gate is a handoff plan only.
- The generated `gh release create` command requires GitHub CLI installed and
  authenticated.
- The repository remains ahead of `origin/main`; push/release is intentionally
  deferred until GitHub tooling is available.
- No new real-data image-processing benchmark was run in this gate.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS manifest metadata and GLASS package paths.
- No input image directory was modified.

## Next Step

- Install and authenticate GitHub CLI, or use an authenticated GitHub connector,
  then push `main` and run the generated release command from
  `runs\checkpoints\s2_gate_195_github_release_plan.md`.
