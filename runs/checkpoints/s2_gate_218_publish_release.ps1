param(
    [string]$GhPath = 'gh',
    [switch]$Publish
)

$ErrorActionPreference = 'Stop'
$ExpectedTag = 'v0.1.0-phase2-gate218'
$ReleaseTitle = 'GLASS Phase 2 Gate 218 Windows packages'
$NotesFile = 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_218_release_notes.md'
$Phase2StatusFile = 'runs\checkpoints\s2_gate_218_phase2_status.json'
$Phase2StatusCompareFile = 'runs\checkpoints\s2_gate_218_phase2_status_compare.json'
$Assets = @(
    @{ Label = 'cuda13'; Path = 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda13.zip'; Sha256 = 'bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273'; SizeBytes = 341358345 },
    @{ Label = 'cuda12'; Path = 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda12.zip'; Sha256 = '72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31'; SizeBytes = 341223006 },
    @{ Label = 'cuda11'; Path = 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cuda11.zip'; Sha256 = '2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681'; SizeBytes = 342200540 },
    @{ Label = 'cpu'; Path = 'C:\Users\ljs\WORK\astro\gpuwbpp\.release\windows\GLASS-Portable-win64-cpu.zip'; Sha256 = '32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d'; SizeBytes = 296231852 }
)

if (-not (Get-Command $GhPath -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $GhPath -PathType Leaf)) {
    throw "GitHub CLI not found: $GhPath"
}
& $GhPath auth status | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI authentication check failed. Run gh auth login, then retry.'
}

foreach ($asset in $Assets) {
    if (-not (Test-Path -LiteralPath $asset.Path -PathType Leaf)) {
        throw "Missing release asset: $($asset.Path)"
    }
    $actualSize = (Get-Item -LiteralPath $asset.Path).Length
    if ($actualSize -ne [int64]$asset.SizeBytes) {
        throw "Asset size mismatch for $($asset.Label): expected $($asset.SizeBytes), got $actualSize"
    }
    $actualSha = (Get-FileHash -LiteralPath $asset.Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSha -ne $asset.Sha256.ToLowerInvariant()) {
        throw "Asset SHA256 mismatch for $($asset.Label): expected $($asset.Sha256), got $actualSha"
    }
}
if ($NotesFile -and -not (Test-Path -LiteralPath $NotesFile -PathType Leaf)) {
    throw "Missing release notes file: $NotesFile"
}
if ($Phase2StatusFile) {
    if (-not (Test-Path -LiteralPath $Phase2StatusFile -PathType Leaf)) {
        throw "Missing Phase 2 status artifact: $Phase2StatusFile"
    }
    $phase2Status = Get-Content -LiteralPath $Phase2StatusFile -Raw | ConvertFrom-Json
    if ($phase2Status.artifact_type -ne 'glass_phase2_status' -or $phase2Status.status -ne 'green' -or $phase2Status.passed -ne $true) {
        throw "Phase 2 status check failed: $Phase2StatusFile"
    }
}
if ($Phase2StatusCompareFile) {
    if (-not (Test-Path -LiteralPath $Phase2StatusCompareFile -PathType Leaf)) {
        throw "Missing Phase 2 status compare artifact: $Phase2StatusCompareFile"
    }
    $phase2Compare = Get-Content -LiteralPath $Phase2StatusCompareFile -Raw | ConvertFrom-Json
    if ($phase2Compare.artifact_type -ne 'glass_phase2_status_compare' -or $phase2Compare.status -ne 'passed' -or $phase2Compare.passed -ne $true) {
        throw "Phase 2 status compare check failed: $Phase2StatusCompareFile"
    }
}

$releaseArgs = @('release', 'create', $ExpectedTag)
$releaseArgs += @($Assets | ForEach-Object { $_.Path })
$releaseArgs += @('--title', $ReleaseTitle)
if ($NotesFile) {
    $releaseArgs += @('--notes-file', $NotesFile)
}
$releaseArgs += '--draft'

Write-Host 'GLASS release assets verified.'
Write-Host 'Dry-run complete. Re-run this script with -Publish to create the GitHub release.'
if (-not $Publish) {
    exit 0
}
& $GhPath @releaseArgs
if ($LASTEXITCODE -ne 0) {
    throw "GitHub release creation failed with exit code $LASTEXITCODE"
}
