param(
    [string]$Python = "python",
    [string]$Configuration = "Release",
    [string]$CudaArchitectures = "native",
    [switch]$BuildCuda,
    [switch]$StaticCudaRuntime
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).ProviderPath
$ReleaseRoot = Join-Path $Root ".release\windows"
$AppRoot = Join-Path $ReleaseRoot "GLASS"
$Runtime = Join-Path $AppRoot "runtime"
$SourceStamp = Join-Path $AppRoot "source"

Remove-Item -Recurse -Force $AppRoot -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $AppRoot | Out-Null

& $Python -m venv $Runtime
$Py = Join-Path $Runtime "Scripts\python.exe"
& $Py -m pip install --upgrade pip wheel
$ProjectSpec = "$Root[report,align,zarr]"
& $Py -m pip install $ProjectSpec

if ($BuildCuda) {
    & $Py -m pip install cmake ninja pybind11
    $CMake = Join-Path $Runtime "Scripts\cmake.exe"
    $BuildDir = Join-Path $Root "build\portable-cuda"
    $RuntimeLinkage = if ($StaticCudaRuntime) { "Static" } else { "Shared" }
    & $CMake -S $Root -B $BuildDir -G Ninja `
        -DGLASS_BUILD_PYTHON_CUDA=ON `
        -DGLASS_BUILD_CUDA=OFF `
        -DGLASS_CUDA_RUNTIME_LIBRARY=$RuntimeLinkage `
        -DCMAKE_BUILD_TYPE=$Configuration `
        -DCMAKE_CUDA_ARCHITECTURES=$CudaArchitectures
    & $CMake --build $BuildDir --config $Configuration --target _glass_cuda_native
    $Native = Get-ChildItem -Path (Join-Path $Root "src") -Filter "_glass_cuda_native*.pyd" | Select-Object -First 1
    if (-not $Native) {
        throw "CUDA build completed, but _glass_cuda_native*.pyd was not found in src."
    }
    $SitePackages = & $Py -c "import site; print(site.getsitepackages()[0])"
    Copy-Item $Native.FullName $SitePackages -Force
}

@"
@echo off
setlocal
"%~dp0runtime\Scripts\python.exe" -m glass.cli %*
"@ | Set-Content -Encoding ASCII (Join-Path $AppRoot "glass.cmd")

@"
@echo off
setlocal
"%~dp0runtime\Scripts\python.exe" -m glass.cli doctor --allow-cpu-only %*
"@ | Set-Content -Encoding ASCII (Join-Path $AppRoot "glass-doctor.cmd")

Copy-Item (Join-Path $Root "README.md") $AppRoot -Force
Copy-Item (Join-Path $Root "LICENSE") $AppRoot -Force

$PublicDocs = Join-Path $AppRoot "docs"
New-Item -ItemType Directory -Force $PublicDocs | Out-Null
Copy-Item (Join-Path $Root "docs\project_overview.md") $PublicDocs -Force
Copy-Item (Join-Path $Root "docs\windows_release.md") $PublicDocs -Force

git -C $Root rev-parse --short HEAD | Set-Content -Encoding ASCII $SourceStamp

$Zip = Join-Path $ReleaseRoot "GLASS-Portable-win64.zip"
Remove-Item -Force $Zip -ErrorAction SilentlyContinue
Compress-Archive -Path $AppRoot -DestinationPath $Zip -Force

Write-Host "Portable build written to $AppRoot"
Write-Host "Zip written to $Zip"
