param(
    [string]$Python = "python",
    [switch]$NoIsolation
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).ProviderPath
Push-Location $Root
try {
    & $Python -m pip install --upgrade build
    if ($NoIsolation) {
        & $Python -m build --wheel --sdist --no-isolation
    } else {
        & $Python -m build --wheel --sdist
    }
    Write-Host "Distribution artifacts written under dist\"
} finally {
    Pop-Location
}
