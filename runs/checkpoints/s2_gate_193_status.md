# S2-Gate 193 Status: Windows Release Manifest

## Gate

- Gate: S2-Gate 193
- Scope: record Windows release zip sizes and SHA256 checksums from the package
  suite artifact.
- Status: green
- Date: 2026-06-17

## Completed

- Added `glass windows-release-manifest`.
- Added release manifest checks for suite status, zip presence, zip size,
  smoke-size agreement, suite-row status, and SHA256 digest recording.
- Generated external and checkpoint JSON/Markdown release manifest artifacts.
- Updated Phase 2, release, and algorithm-source documentation.

## Commands Run

```powershell
.\.venv\Scripts\ruff.exe check src\glass\report\windows_release_manifest.py src\glass\cli.py tests\test_windows_release_manifest.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_windows_release_manifest.py tests\test_cli_smoke.py
$root='C:\glass_runs\phase2_s2_gate_193_windows_release_manifest'
New-Item -ItemType Directory -Force -Path $root | Out-Null
$common=@(
  'windows-release-manifest',
  '--suite','runs\checkpoints\s2_gate_192_windows_package_suite.json',
  '--fail-on-failure'
)
& .\.venv\Scripts\glass.exe @common --out "$root\windows_release_manifest.json" --markdown "$root\windows_release_manifest.md"
& .\.venv\Scripts\glass.exe @common --out runs\checkpoints\s2_gate_193_windows_release_manifest.json --markdown runs\checkpoints\s2_gate_193_windows_release_manifest.md
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused ruff: passed.
- Focused pytest: `17 passed in 1.93s`.
- Full ruff: passed.
- Full pytest: `470 passed in 25.35s`.

## Manifest Result

- Status: `release_manifest_ready`.
- Passed: `true`.
- Recommendation: `ready_for_upload`.
- Package count: `4`.
- Failed checks: none.

## Package Checksums

- `cuda13`: size `339732356` bytes,
  SHA256 `87023bac87deaec4298cb4351b250f40d4a53b8c55165b59d4cdb83dba7f5a54`.
- `cuda12`: size `341206870` bytes,
  SHA256 `5fd272b0525ddb1222115f2dfc2ae67fcdab80eadcdd522b6c89cd4d03d87242`.
- `cuda11`: size `342183616` bytes,
  SHA256 `d1d5a23a46e4e00cb95ce87c3a732f02863861ec934e6ad7d171166ce5f8f5a5`.
- `cpu`: size `296215418` bytes,
  SHA256 `71ace05d2abde81acf2122b4d1891e1bff290b63f71f859bb2d1e60a71eb38a6`.

## CUDA Status

- CUDA available on the checkpoint machine: `true`.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- External manifest JSON:
  `C:\glass_runs\phase2_s2_gate_193_windows_release_manifest\windows_release_manifest.json`
- External manifest Markdown:
  `C:\glass_runs\phase2_s2_gate_193_windows_release_manifest\windows_release_manifest.md`
- Checkpoint manifest JSON:
  `runs\checkpoints\s2_gate_193_windows_release_manifest.json`
- Checkpoint manifest Markdown:
  `runs\checkpoints\s2_gate_193_windows_release_manifest.md`

## Known Limitations

- This gate does not rebuild, sign, upload, or publish packages.
- The manifest describes local zip files at manifest time.
- The package set still has mixed source stamps inherited from earlier gates.
  Formal release artifacts should be rebuilt from one final tag or commit and
  checked with `--require-same-source-stamp`.
- No new real-data image-processing benchmark was run in this gate.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read, copied, summarized, or reworked.
- The gate used only GLASS package-suite metadata and GLASS zip files.
- No input image directory was modified.

## Next Step

- Rebuild the complete Windows package set from one final source tag for a
  strict public release, or return to algorithm-hardening gates now that the
  Windows package audit chain is complete.
