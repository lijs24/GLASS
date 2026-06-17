param(
    [string]$GhPath = 'C:\Program Files\GitHub CLI\gh.exe',
    [switch]$Publish
)

$ErrorActionPreference = 'Stop'
$ExpectedTag = 'v0.1.0-windows-gpu.9'
$ReleaseTitle = 'GLASS v0.1.0-windows-gpu.9 Windows CUDA packages'
$NotesFile = 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_197_github_release_notes.md'
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
