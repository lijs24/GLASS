param(
    [string]$Python = "python",
    [string]$Configuration = "Release",
    [string]$CudaArchitectures = "native",
    [string]$CudaToolkitRoot = "",
    [switch]$BuildCuda,
    [switch]$StaticCudaRuntime
)

$ErrorActionPreference = "Stop"

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath failed with exit code $LASTEXITCODE"
    }
}

function Resolve-CudaRoot {
    param([string]$RequestedRoot)

    if (-not [string]::IsNullOrWhiteSpace($RequestedRoot)) {
        return (Resolve-Path $RequestedRoot).ProviderPath
    }
    if (-not [string]::IsNullOrWhiteSpace($env:CUDA_PATH) -and (Test-Path $env:CUDA_PATH)) {
        return (Resolve-Path $env:CUDA_PATH).ProviderPath
    }

    $DefaultRoot = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    if (Test-Path $DefaultRoot) {
        $Candidates = Get-ChildItem $DefaultRoot -Directory |
            Sort-Object Name -Descending
        if ($Candidates) {
            return $Candidates[0].FullName
        }
    }

    throw "CUDA Toolkit was not found. Pass -CudaToolkitRoot or set CUDA_PATH."
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).ProviderPath
$ReleaseRoot = Join-Path $Root ".release\windows"
$AppRoot = Join-Path $ReleaseRoot "GLASS"
$Runtime = Join-Path $AppRoot "runtime"
$SourceStamp = Join-Path $AppRoot "source"

Remove-Item -Recurse -Force $AppRoot -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $AppRoot | Out-Null

Invoke-Native -FilePath $Python -Arguments @("-m", "venv", $Runtime)
$Py = Join-Path $Runtime "Scripts\python.exe"
Invoke-Native -FilePath $Py -Arguments @("-m", "pip", "install", "--upgrade", "pip", "wheel")
$ProjectSpec = "$Root[report,align,zarr]"
Invoke-Native -FilePath $Py -Arguments @("-m", "pip", "install", $ProjectSpec)

if ($BuildCuda) {
    $ResolvedCudaRoot = Resolve-CudaRoot $CudaToolkitRoot
    $Nvcc = Join-Path $ResolvedCudaRoot "bin\nvcc.exe"
    if (-not (Test-Path $Nvcc)) {
        throw "nvcc was not found at $Nvcc"
    }
    $env:CUDA_PATH = $ResolvedCudaRoot
    $env:PATH = (Join-Path $ResolvedCudaRoot "bin") + ";" + $env:PATH

    Invoke-Native -FilePath $Py -Arguments @("-m", "pip", "install", "cmake", "ninja", "pybind11")
    $CMake = Join-Path $Runtime "Scripts\cmake.exe"
    $Ninja = Join-Path $Runtime "Scripts\ninja.exe"
    $env:PATH = (Join-Path $Runtime "Scripts") + ";" + $env:PATH
    $Pybind11Dir = & $Py -c "import pybind11; print(pybind11.get_cmake_dir())"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Pybind11Dir)) {
        throw "Unable to resolve pybind11 CMake directory from the portable runtime."
    }
    $BuildDir = Join-Path $Root "build\portable-cuda"
    $RuntimeLinkage = if ($StaticCudaRuntime) { "Static" } else { "Shared" }
    Remove-Item -Recurse -Force $BuildDir -ErrorAction SilentlyContinue
    Remove-Item -Force (Join-Path $Root "src\_glass_cuda_native*.pyd") -ErrorAction SilentlyContinue

    Invoke-Native -FilePath $CMake -Arguments @(
        "-S", $Root,
        "-B", $BuildDir,
        "-G", "Ninja",
        "-DGLASS_BUILD_PYTHON_CUDA=ON",
        "-DGLASS_BUILD_CUDA=OFF",
        "-DGLASS_CUDA_RUNTIME_LIBRARY=$RuntimeLinkage",
        "-DGLASS_CUDA_ALLOW_UNSUPPORTED_COMPILER=ON",
        "-DCMAKE_CUDA_FLAGS=--allow-unsupported-compiler -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH",
        "-DCMAKE_BUILD_TYPE=$Configuration",
        "-DCMAKE_CUDA_ARCHITECTURES=$CudaArchitectures",
        "-DCUDAToolkit_ROOT=$ResolvedCudaRoot",
        "-DCMAKE_CUDA_COMPILER=$Nvcc",
        "-DCMAKE_MAKE_PROGRAM=$Ninja",
        "-DPython3_EXECUTABLE=$Py",
        "-Dpybind11_DIR=$Pybind11Dir"
    )
    Invoke-Native -FilePath $CMake -Arguments @(
        "--build", $BuildDir,
        "--config", $Configuration,
        "--target", "_glass_cuda_native"
    )
    $Native = Get-ChildItem -Path (Join-Path $Root "src") -Filter "_glass_cuda_native*.pyd" | Select-Object -First 1
    if (-not $Native) {
        throw "CUDA build completed, but _glass_cuda_native*.pyd was not found in src."
    }
    $SitePackageCandidates = & $Py -c "import site; print('\n'.join(site.getsitepackages()))"
    $SitePackages = $SitePackageCandidates |
        Where-Object { $_ -like "*site-packages" } |
        Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($SitePackages)) {
        $SitePackages = $SitePackageCandidates | Select-Object -First 1
    }
    if ([string]::IsNullOrWhiteSpace($SitePackages)) {
        throw "Unable to resolve Python site-packages for the portable runtime."
    }
    Copy-Item $Native.FullName $SitePackages -Force
    $PackagedNative = Get-ChildItem -Path $SitePackages -Filter "_glass_cuda_native*.pyd" | Select-Object -First 1
    if (-not $PackagedNative) {
        throw "CUDA build completed, but _glass_cuda_native*.pyd was not copied to $SitePackages."
    }
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
