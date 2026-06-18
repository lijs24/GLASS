param(
    [string]$GhPath = 'gh',
    [switch]$Publish
)

$ErrorActionPreference = 'Stop'
$ExpectedTag = 'v0.1.0-gate332'
$ReleaseTitle = 'GLASS Gate332 Windows Fixture'
$NotesFile = 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_332_release_notes.md'
$WindowsReleaseMatrixFile = 'runs\checkpoints\s2_gate_332_fixture\windows_release_matrix.json'
$Phase2StatusFile = $null
$Phase2StatusCompareFile = $null
$Assets = @(
    @{ Label = 'cuda13'; Path = 'C:\Users\ljs\WORK\astro\gpuwbpp\runs\checkpoints\s2_gate_332_fixture\GLASS-Portable-win64-cuda13.zip'; Sha256 = '0000000000000000000000000000000000000000000000000000000000000001'; SizeBytes = 27 }
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
if ($WindowsReleaseMatrixFile) {
    if (-not (Test-Path -LiteralPath $WindowsReleaseMatrixFile -PathType Leaf)) {
        throw "Missing Windows release matrix artifact: $WindowsReleaseMatrixFile"
    }
    $matrix = Get-Content -LiteralPath $WindowsReleaseMatrixFile -Raw | ConvertFrom-Json
    if ($matrix.artifact_type -ne 'windows_release_matrix' -or $matrix.status -ne 'release_matrix_ready' -or $matrix.passed -ne $true) {
        throw "Windows release matrix check failed: $WindowsReleaseMatrixFile"
    }
    if (-not $matrix.default_promotion_manifest -or $matrix.default_promotion_manifest.status -ne 'default_promotion_ready' -or $matrix.default_promotion_manifest.passed -ne $true -or $matrix.default_promotion_manifest.default_route_passed -ne $true) {
        throw "Windows release matrix default-promotion evidence failed: $WindowsReleaseMatrixFile"
    }
    if ($matrix.default_promotion_manifest.integration_rejection_sample_counts_match_maps -ne $true -or $matrix.default_promotion_manifest.rejection_sample_accounting_status -ne 'passed' -or [int]$matrix.default_promotion_manifest.rejection_sample_accounting_failed_count -ne 0) {
        throw "Windows release matrix rejection sample accounting failed: $WindowsReleaseMatrixFile"
    }
    if ($matrix.default_promotion_manifest.integration_sample_accounting_closure -ne $true -or $matrix.default_promotion_manifest.sample_accounting_closure_status -ne 'passed' -or [int]$matrix.default_promotion_manifest.sample_accounting_closure_failed_count -ne 0) {
        throw "Windows release matrix sample accounting closure failed: $WindowsReleaseMatrixFile"
    }
    if ($matrix.default_promotion_manifest.stack_engine_contract_present -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_ready -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_phase2_check_passed -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_status -ne 'passed' -or $matrix.default_promotion_manifest.stack_engine_contract_passed -ne $true -or $matrix.default_promotion_manifest.stack_engine_contract_scope -ne 'all' -or $matrix.default_promotion_manifest.stack_engine_contract_adoption_recommendation -ne 'stack_engine_default_ready' -or [int]$matrix.default_promotion_manifest.stack_engine_contract_default_gap_count -ne 0 -or [int]$matrix.default_promotion_manifest.stack_engine_contract_blocker_count -ne 0) {
        throw "Windows release matrix StackEngine default contract failed: $WindowsReleaseMatrixFile"
    }
    $residentFastpathHandoff = $matrix.default_promotion_manifest.resident_registration_fastpath_release_handoff
    if (-not $residentFastpathHandoff -or $residentFastpathHandoff.present -ne $true -or $residentFastpathHandoff.ready -ne $true -or $residentFastpathHandoff.raw_ready -ne $true -or $residentFastpathHandoff.phase2_ready -ne $true -or $residentFastpathHandoff.agreement -ne $true -or $residentFastpathHandoff.decision_check_passed -ne $true -or $residentFastpathHandoff.phase2_check_passed -ne $true -or $residentFastpathHandoff.raw_status -ne 'passed' -or $residentFastpathHandoff.phase2_status -ne 'passed' -or $residentFastpathHandoff.raw_required -ne $true -or $residentFastpathHandoff.phase2_required -ne $true -or [int]$residentFastpathHandoff.raw_passed_check_count -le 0 -or [int]$residentFastpathHandoff.phase2_passed_check_count -le 0 -or [int]$residentFastpathHandoff.raw_failed_check_count -ne 0 -or [int]$residentFastpathHandoff.phase2_failed_check_count -ne 0) {
        throw "Windows release matrix resident fastpath release handoff failed: $WindowsReleaseMatrixFile"
    }
    $releaseGuard = $matrix.release_decision_direct_runtime_publication_guard
    if (-not $releaseGuard -or $releaseGuard.present -ne $true -or $releaseGuard.ready -ne $true -or $releaseGuard.decision_check_passed -ne $true -or $releaseGuard.source_ready -ne $true -or $releaseGuard.count_ready -ne $true -or $releaseGuard.raw_leaf_checks_ready -ne $true -or $releaseGuard.phase2_leaf_checks_ready -ne $true -or $releaseGuard.raw_acceptance_source -ne 'explicit_resident_artifacts_json' -or $releaseGuard.raw_calibration_source -ne 'resident_artifacts_json_fallback' -or [int]$releaseGuard.raw_resident_lights -lt 200) {
        throw "Windows release matrix release-decision direct publication guard failed: $WindowsReleaseMatrixFile"
    }
    $defaultPromotionReleaseGuard = $matrix.default_promotion_manifest.release_decision_direct_runtime_publication_guard
    if (-not $defaultPromotionReleaseGuard -or $defaultPromotionReleaseGuard.present -ne $true -or $defaultPromotionReleaseGuard.ready -ne $true -or $defaultPromotionReleaseGuard.decision_check_passed -ne $true -or $defaultPromotionReleaseGuard.source_ready -ne $true -or $defaultPromotionReleaseGuard.count_ready -ne $true -or $defaultPromotionReleaseGuard.leaf_checks_ready -ne $true -or $defaultPromotionReleaseGuard.raw_matrix_acceptance_source -ne 'explicit_resident_artifacts_json' -or $defaultPromotionReleaseGuard.raw_matrix_pipeline_calibration_source -ne 'resident_artifacts_json_fallback' -or [int]$defaultPromotionReleaseGuard.raw_matrix_pipeline_resident_lights -lt 200) {
        throw "Windows release matrix default-promotion direct publication guard failed: $WindowsReleaseMatrixFile"
    }
}
if ($Phase2StatusFile) {
    if (-not (Test-Path -LiteralPath $Phase2StatusFile -PathType Leaf)) {
        throw "Missing Phase 2 status artifact: $Phase2StatusFile"
    }
    $phase2Status = Get-Content -LiteralPath $Phase2StatusFile -Raw | ConvertFrom-Json
    if ($phase2Status.artifact_type -ne 'glass_phase2_status' -or $phase2Status.status -ne 'green' -or $phase2Status.passed -ne $true) {
        throw "Phase 2 status check failed: $Phase2StatusFile"
    }
    if (-not $phase2Status.pipeline_contract -or $phase2Status.pipeline_contract.integration_sample_accounting_closure -ne $true -or $phase2Status.pipeline_contract.sample_accounting_closure_status -ne 'passed' -or [int]$phase2Status.pipeline_contract.sample_accounting_closure_failed_count -ne 0) {
        throw "Phase 2 sample accounting closure failed: $Phase2StatusFile"
    }
    $phase2StackCheck = $phase2Status.checks | Where-Object { $_.name -eq 'stack_engine_default_contract_ready' } | Select-Object -First 1
    if (-not $phase2StackCheck -or $phase2StackCheck.passed -ne $true -or -not $phase2Status.stack_engine_contract -or $phase2Status.stack_engine_contract.audit_type -ne 'stack_engine_default_contract' -or $phase2Status.stack_engine_contract.status -ne 'passed' -or $phase2Status.stack_engine_contract.passed -ne $true -or $phase2Status.stack_engine_contract.default_promotion_ready -ne $true -or $phase2Status.stack_engine_contract.default_promotion_status -ne 'ready' -or $phase2Status.stack_engine_contract.adoption_recommendation -ne 'stack_engine_default_ready' -or $phase2Status.stack_engine_contract.default_promotion_recommendation -ne 'stack_engine_default_ready' -or [int]$phase2Status.stack_engine_contract.default_promotion_phase2_stack_engine_default_gap_count -ne 0 -or [int]$phase2Status.stack_engine_contract.default_promotion_blocker_count -ne 0) {
        throw "Phase 2 StackEngine default contract failed: $Phase2StatusFile"
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
