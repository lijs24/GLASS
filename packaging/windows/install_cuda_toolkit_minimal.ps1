param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("cuda12", "cuda11")]
    [string]$Label,
    [string]$DownloadDir = "$env:LOCALAPPDATA\GLASS\cuda-installers",
    [string]$OutJson = "",
    [switch]$Download,
    [switch]$Install,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

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

$Packages = @{
    cuda12 = @{
        Toolkit = "12.4"
        InstallerName = "cuda_12.4.1_551.78_windows.exe"
        InstallerUrl = "https://developer.download.nvidia.com/compute/cuda/12.4.1/local_installers/cuda_12.4.1_551.78_windows.exe"
        Sha256 = "7d20c5eb186e4d3c64680fe5096bed05926aea89754192102323c956c26244de"
        Components = @("nvcc_12.4", "cudart_12.4")
        ExpectedRoot = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"
    }
    cuda11 = @{
        Toolkit = "11.8"
        InstallerName = "cuda_11.8.0_522.06_windows.exe"
        InstallerUrl = "https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_522.06_windows.exe"
        Sha256 = "b70f38f27321c0a53993438a91970a2e3c426f46da4c42eceff1eeea031a6555"
        Components = @("nvcc_11.8", "cudart_11.8")
        ExpectedRoot = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
    }
}

$Spec = $Packages[$Label]
$InstallerPath = Join-Path $DownloadDir $Spec.InstallerName
$DownloadRequested = [bool]$Download -or [bool]$Install
$Status = "plan_only"
$InstallerPresent = Test-Path $InstallerPath
$InstallerSha256 = $null
$InstallExitCode = $null

if ($DownloadRequested) {
    New-Item -ItemType Directory -Force $DownloadDir | Out-Null
    if ($Force -or -not (Test-Path $InstallerPath)) {
        Invoke-WebRequest -Uri $Spec.InstallerUrl -OutFile $InstallerPath
    }
    $InstallerPresent = Test-Path $InstallerPath
    if (-not $InstallerPresent) {
        throw "Installer was not downloaded: $InstallerPath"
    }
    $InstallerSha256 = (Get-FileHash -Algorithm SHA256 $InstallerPath).Hash.ToLowerInvariant()
    if ($InstallerSha256 -ne $Spec.Sha256) {
        throw "SHA256 mismatch for $InstallerPath. Expected $($Spec.Sha256), got $InstallerSha256"
    }
    $Status = "downloaded"
}

if ($Install) {
    $Arguments = @("-s") + $Spec.Components + @("-n")
    $Process = Start-Process -FilePath $InstallerPath -ArgumentList $Arguments -Wait -PassThru
    $InstallExitCode = $Process.ExitCode
    if ($InstallExitCode -ne 0) {
        throw "CUDA installer failed with exit code $InstallExitCode"
    }
    $Status = "installed"
}

$Payload = [ordered]@{
    schema_version = 1
    artifact_type = "cuda_toolkit_minimal_install"
    label = $Label
    status = $Status
    toolkit = $Spec.Toolkit
    installer_url = $Spec.InstallerUrl
    installer_path = $InstallerPath
    installer_present = $InstallerPresent
    installer_sha256 = $InstallerSha256
    expected_sha256 = $Spec.Sha256
    components = $Spec.Components
    driver_component_included = $false
    install_requested = [bool]$Install
    download_requested = $DownloadRequested
    install_exit_code = $InstallExitCode
    expected_root = $Spec.ExpectedRoot
    nvcc_expected = Join-Path $Spec.ExpectedRoot "bin\nvcc.exe"
    notes = @(
        "This script intentionally installs only nvcc and cudart components.",
        "Display driver components are not requested.",
        "Run glass windows-package-build-plan after install to verify nvcc discovery."
    )
}

if (-not [string]::IsNullOrWhiteSpace($OutJson)) {
    $OutPath = [System.IO.Path]::GetFullPath($OutJson)
    New-Item -ItemType Directory -Force ([System.IO.Path]::GetDirectoryName($OutPath)) | Out-Null
    Write-Utf8NoBomFile -Path $OutPath -Content ($Payload | ConvertTo-Json -Depth 6)
}

$Payload | ConvertTo-Json -Depth 6
