param(
    [string]$Python = "python",
    [string]$Configuration = "Release",
    [string]$CudaArchitectures = "native",
    [string]$CudaToolkitRoot = "",
    [string]$PackageLabel = "",
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

function Invoke-Robocopy {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination,
        [string[]]$ExtraArguments = @()
    )

    robocopy $Source $Destination @ExtraArguments | Out-Host
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}

function Write-Utf8NoBomFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $Encoding)
}

function Resolve-PythonHome {
    param([string]$PythonExecutable)

    $InfoJson = & $PythonExecutable -c "import json, sys; print(json.dumps({'base_prefix': sys.base_prefix, 'executable': sys.executable}))"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($InfoJson)) {
        throw "Unable to resolve Python home from $PythonExecutable"
    }
    $Info = $InfoJson | ConvertFrom-Json
    if ([string]::IsNullOrWhiteSpace($Info.base_prefix) -or -not (Test-Path $Info.base_prefix)) {
        throw "Resolved Python home does not exist: $($Info.base_prefix)"
    }
    return (Resolve-Path $Info.base_prefix).ProviderPath
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

function Import-VisualStudioBuildEnvironment {
    if (Get-Command cl.exe -ErrorAction SilentlyContinue) {
        return
    }

    $VsWhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $VsWhere)) {
        throw "cl.exe was not found on PATH and vswhere.exe was not found. Install Visual Studio Build Tools with the C++ workload."
    }
    $InstallPath = & $VsWhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($InstallPath) -or -not (Test-Path $InstallPath)) {
        throw "Visual Studio C++ Build Tools were not found by vswhere.exe."
    }
    $VcVars = Join-Path $InstallPath "VC\Auxiliary\Build\vcvars64.bat"
    if (-not (Test-Path $VcVars)) {
        throw "vcvars64.bat was not found at $VcVars"
    }

    $EnvLines = & cmd.exe /d /s /c "`"$VcVars`" >nul && set"
    if ($LASTEXITCODE -ne 0 -or -not $EnvLines) {
        throw "Failed to import Visual Studio build environment from $VcVars"
    }
    foreach ($Line in $EnvLines) {
        if ($Line -match "^(.*?)=(.*)$") {
            Set-Item -Path ("Env:\" + $Matches[1]) -Value $Matches[2]
        }
    }
    if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
        throw "Visual Studio build environment was imported, but cl.exe is still unavailable."
    }
}

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).ProviderPath
$ReleaseRoot = Join-Path $Root ".release\windows"
$AppRoot = Join-Path $ReleaseRoot "GLASS"
$Runtime = Join-Path $AppRoot "runtime"
$SourceStamp = Join-Path $AppRoot "source"
$PackageLabelValue = $PackageLabel.Trim()
$ZipName = if ([string]::IsNullOrWhiteSpace($PackageLabelValue)) {
    "GLASS-Portable-win64.zip"
} else {
    "GLASS-Portable-win64-$PackageLabelValue.zip"
}

Remove-Item -Recurse -Force $AppRoot -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $AppRoot | Out-Null

$PythonHome = Resolve-PythonHome $Python
Invoke-Robocopy -Source $PythonHome -Destination $Runtime -ExtraArguments @(
    "/MIR",
    "/NFL",
    "/NDL",
    "/NJH",
    "/NJS",
    "/NP",
    "/XD",
    "__pycache__",
    "/XF",
    "*.pyc"
)
$Py = Join-Path $Runtime "python.exe"
if (-not (Test-Path $Py)) {
    throw "Portable Python executable was not copied to $Py"
}
$env:PYTHONNOUSERSITE = "1"
Invoke-Native -FilePath $Py -Arguments @("-m", "pip", "install", "--upgrade", "pip", "wheel")
$ProjectSpec = "$Root[report,align,zarr]"
Invoke-Native -FilePath $Py -Arguments @("-m", "pip", "install", $ProjectSpec)

if ($BuildCuda) {
    $ResolvedCudaRoot = Resolve-CudaRoot $CudaToolkitRoot
    $Nvcc = Join-Path $ResolvedCudaRoot "bin\nvcc.exe"
    if (-not (Test-Path $Nvcc)) {
        throw "nvcc was not found at $Nvcc"
    }
    Import-VisualStudioBuildEnvironment
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

    $CudaRuntimeDlls = Get-ChildItem -Path (Join-Path $ResolvedCudaRoot "bin") -Filter "cudart64_*.dll" -ErrorAction SilentlyContinue
    foreach ($Dll in $CudaRuntimeDlls) {
        Copy-Item $Dll.FullName $SitePackages -Force
    }
}

@"
@echo off
setlocal
set PYTHONNOUSERSITE=1
"%~dp0runtime\python.exe" -m glass.cli %*
"@ | Set-Content -Encoding ASCII (Join-Path $AppRoot "glass.cmd")

@"
@echo off
setlocal
set PYTHONNOUSERSITE=1
"%~dp0runtime\python.exe" -m glass.cli doctor --allow-cpu-only %*
"@ | Set-Content -Encoding ASCII (Join-Path $AppRoot "glass-doctor.cmd")

Copy-Item (Join-Path $Root "README.md") $AppRoot -Force
Copy-Item (Join-Path $Root "LICENSE") $AppRoot -Force

$PublicDocs = Join-Path $AppRoot "docs"
New-Item -ItemType Directory -Force $PublicDocs | Out-Null
Copy-Item (Join-Path $Root "docs\project_overview.md") $PublicDocs -Force
Copy-Item (Join-Path $Root "docs\windows_release.md") $PublicDocs -Force

git -C $Root rev-parse --short HEAD | Set-Content -Encoding ASCII $SourceStamp
$PackageManifest = [ordered]@{
    schema_version = 1
    product = "GLASS"
    package_label = if ([string]::IsNullOrWhiteSpace($PackageLabelValue)) { $null } else { $PackageLabelValue }
    build_cuda = [bool]$BuildCuda
    cuda_architectures = $CudaArchitectures
    cuda_toolkit_root = if ($BuildCuda) { $ResolvedCudaRoot } else { $null }
    cuda_runtime_library = if ($BuildCuda) { $RuntimeLinkage } else { $null }
    python_home = $PythonHome
    source_stamp = (Get-Content -Raw $SourceStamp).Trim()
}
Write-Utf8NoBomFile -Path (Join-Path $AppRoot "package_manifest.json") -Content ($PackageManifest | ConvertTo-Json -Depth 4)

$Zip = Join-Path $ReleaseRoot $ZipName
Remove-Item -Force $Zip -ErrorAction SilentlyContinue
Compress-Archive -Path $AppRoot -DestinationPath $Zip -Force

Write-Host "Portable build written to $AppRoot"
Write-Host "Zip written to $Zip"
