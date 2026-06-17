from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _quote(value: str) -> str:
    return shlex.quote(value)


def _ps_literal(value: str | None) -> str:
    if value is None:
        return "$null"
    return "'" + str(value).replace("'", "''") + "'"


def _asset_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in manifest.get("packages") or []:
        if not isinstance(row, dict):
            continue
        zip_path = row.get("zip_path")
        zip_file = Path(str(zip_path)).resolve() if zip_path else None
        rows.append(
            {
                "label": row.get("label"),
                "zip_path": None if zip_file is None else str(zip_file),
                "exists": bool(zip_file is not None and zip_file.exists() and zip_file.is_file()),
                "size_bytes": row.get("size_bytes"),
                "sha256": row.get("sha256"),
                "source_stamp": row.get("source_stamp"),
            }
        )
    return rows


def _phase2_artifact_summary(
    path: str | Path | None,
    *,
    expected_artifact_type: str,
) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    payload = _read_json_object(target) if target.exists() else {}
    latest_checkpoint = (
        payload.get("latest_checkpoint")
        if isinstance(payload.get("latest_checkpoint"), dict)
        else {}
    )
    acceptance = payload.get("acceptance_audit") if isinstance(payload.get("acceptance_audit"), dict) else {}
    native_guardrails_bundle = (
        acceptance.get("native_guardrails_bundle")
        if isinstance(acceptance.get("native_guardrails_bundle"), dict)
        else None
    )
    registration_fastpath = (
        acceptance.get("resident_registration_fastpath")
        if isinstance(acceptance.get("resident_registration_fastpath"), dict)
        else None
    )
    baseline = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else {}
    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
    pipeline_contract = (
        payload.get("pipeline_contract")
        if isinstance(payload.get("pipeline_contract"), dict)
        else None
    )
    release_decision = (
        payload.get("release_decision")
        if isinstance(payload.get("release_decision"), dict)
        else None
    )
    return {
        "path": str(target),
        "exists": target.exists(),
        "artifact_type": payload.get("artifact_type"),
        "expected_artifact_type": expected_artifact_type,
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "latest_gate": latest_checkpoint.get("gate"),
        "baseline_gate": baseline.get("latest_gate"),
        "candidate_gate": candidate.get("latest_gate"),
        "acceptance_status": acceptance.get("status"),
        "native_guardrails_bundle": native_guardrails_bundle,
        "native_guardrails_bundle_status": acceptance.get("native_guardrails_bundle_status")
        or (native_guardrails_bundle or {}).get("status"),
        "resident_result_contract_source": acceptance.get("resident_result_contract_source")
        or (native_guardrails_bundle or {}).get("resident_result_contract_source"),
        "resident_result_contract_run_default": acceptance.get("resident_result_contract_run_default")
        if acceptance.get("resident_result_contract_run_default") is not None
        else (native_guardrails_bundle or {}).get("resident_result_contract_run_default"),
        "resident_result_contract_json": acceptance.get("resident_result_contract_json")
        or (native_guardrails_bundle or {}).get("resident_result_contract_json"),
        "resident_native_calibration_artifact": acceptance.get("resident_native_calibration_artifact")
        if acceptance.get("resident_native_calibration_artifact") is not None
        else (native_guardrails_bundle or {}).get("resident_native_calibration_artifact"),
        "resident_calibration_master_count": acceptance.get("resident_calibration_master_count")
        or (native_guardrails_bundle or {}).get("resident_calibration_master_count"),
        "resident_calibrated_light_count": acceptance.get("resident_calibrated_light_count")
        or (native_guardrails_bundle or {}).get("resident_calibrated_light_count"),
        "resident_registration_fastpath": registration_fastpath,
        "resident_registration_fastpath_status": acceptance.get(
            "resident_registration_fastpath_status"
        )
        or (registration_fastpath or {}).get("status"),
        "resident_registration_fastpath_contract_status": acceptance.get(
            "resident_registration_fastpath_contract_status"
        )
        or (registration_fastpath or {}).get("contract_status"),
        "resident_registration_fastpath_mode": acceptance.get("resident_registration_fastpath_mode")
        or (registration_fastpath or {}).get("mode"),
        "triangle_descriptor_fit_batch": acceptance.get("triangle_descriptor_fit_batch")
        if acceptance.get("triangle_descriptor_fit_batch") is not None
        else (registration_fastpath or {}).get("triangle_descriptor_fit_batch"),
        "triangle_descriptor_fit_batch_mode": acceptance.get("triangle_descriptor_fit_batch_mode")
        or (registration_fastpath or {}).get("triangle_descriptor_fit_batch_mode"),
        "triangle_descriptor_fit_device_reuse": acceptance.get(
            "triangle_descriptor_fit_device_reuse"
        )
        or (registration_fastpath or {}).get("triangle_descriptor_fit_device_reuse"),
        "triangle_pixel_refine_batch": acceptance.get("triangle_pixel_refine_batch")
        if acceptance.get("triangle_pixel_refine_batch") is not None
        else (registration_fastpath or {}).get("triangle_pixel_refine_batch"),
        "triangle_pixel_refine_batch_metric_mode": acceptance.get(
            "triangle_pixel_refine_batch_metric_mode"
        )
        or (registration_fastpath or {}).get("triangle_pixel_refine_batch_metric_mode"),
        "triangle_warp_batch": acceptance.get("triangle_warp_batch")
        if acceptance.get("triangle_warp_batch") is not None
        else (registration_fastpath or {}).get("triangle_warp_batch"),
        "triangle_warp_batch_mode": acceptance.get("triangle_warp_batch_mode")
        or (registration_fastpath or {}).get("triangle_warp_batch_mode"),
        "triangle_warp_batch_frame_count": acceptance.get("triangle_warp_batch_frame_count")
        if acceptance.get("triangle_warp_batch_frame_count") is not None
        else (registration_fastpath or {}).get("triangle_warp_batch_frame_count"),
        "resident_warp_copy_mode": acceptance.get("resident_warp_copy_mode")
        or (registration_fastpath or {}).get("resident_warp_copy_mode"),
        "resident_warp_scratch_bytes": acceptance.get("resident_warp_scratch_bytes")
        if acceptance.get("resident_warp_scratch_bytes") is not None
        else (registration_fastpath or {}).get("resident_warp_scratch_bytes"),
        "resident_registration_fastpath_contract_check_count": acceptance.get(
            "resident_registration_fastpath_contract_check_count"
        )
        if acceptance.get("resident_registration_fastpath_contract_check_count") is not None
        else (registration_fastpath or {}).get("contract_check_count"),
        "resident_registration_fastpath_contract_failed_check_count": acceptance.get(
            "resident_registration_fastpath_contract_failed_check_count"
        )
        if acceptance.get("resident_registration_fastpath_contract_failed_check_count") is not None
        else (registration_fastpath or {}).get("contract_failed_check_count"),
        "pipeline_contract": pipeline_contract,
        "pipeline_contract_status": (pipeline_contract or {}).get("status"),
        "pipeline_contract_passed": (pipeline_contract or {}).get("passed"),
        "pipeline_contract_failed_check_count": (pipeline_contract or {}).get("failed_check_count"),
        "pipeline_integration_output_count": (pipeline_contract or {}).get("integration_output_count"),
        "pipeline_integration_map_count": (pipeline_contract or {}).get("integration_map_count"),
        "pipeline_integration_dq_contract": (pipeline_contract or {}).get("integration_dq_contract"),
        "pipeline_integration_stack_result_contract": (pipeline_contract or {}).get(
            "integration_stack_result_contract"
        ),
        "pipeline_integration_resident_result_contract": (pipeline_contract or {}).get(
            "integration_resident_result_contract"
        ),
        "pipeline_pixel_verification_enabled": (pipeline_contract or {}).get(
            "pixel_verification_enabled"
        ),
        "pipeline_integration_dq_map_pixels_match_summary": (pipeline_contract or {}).get(
            "integration_dq_map_pixels_match_summary"
        ),
        "pipeline_integration_coverage_map_pixels_match_dq": (pipeline_contract or {}).get(
            "integration_coverage_map_pixels_match_dq"
        ),
        "pipeline_integration_rejection_map_pixels_match_dq": (pipeline_contract or {}).get(
            "integration_rejection_map_pixels_match_dq"
        ),
        "release_decision": release_decision,
        "release_decision_status": (release_decision or {}).get("status"),
        "release_decision_recommendation": (release_decision or {}).get("recommendation"),
        "release_decision_release_candidate_ready": (release_decision or {}).get(
            "release_candidate_ready"
        ),
        "release_decision_default_change_ready": (release_decision or {}).get(
            "default_change_ready"
        ),
        "release_decision_speedup_actual": (release_decision or {}).get("speedup_actual"),
        "release_runtime_repeat_run_count": (release_decision or {}).get(
            "runtime_repeat_run_count"
        ),
        "release_runtime_repeat_best_label": (release_decision or {}).get(
            "runtime_repeat_best_label"
        ),
        "release_runtime_repeat_best_elapsed_s": (release_decision or {}).get(
            "runtime_repeat_best_elapsed_s"
        ),
        "release_runtime_repeat_elapsed_ratio_vs_best": (release_decision or {}).get(
            "runtime_repeat_elapsed_ratio_vs_best"
        ),
        "release_runtime_repeat_max_elapsed_ratio_vs_best": (release_decision or {}).get(
            "runtime_repeat_max_elapsed_ratio_vs_best"
        ),
    }


def _windows_release_matrix_summary(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    payload = _read_json_object(target) if target.exists() else {}
    current_machine = (
        payload.get("current_machine") if isinstance(payload.get("current_machine"), dict) else {}
    )
    default_promotion = (
        payload.get("default_promotion_manifest")
        if isinstance(payload.get("default_promotion_manifest"), dict)
        else {}
    )
    package_rows = [row for row in payload.get("packages") or [] if isinstance(row, dict)]
    package_labels = [str(row.get("label")) for row in package_rows if row.get("label")]
    return {
        "path": str(target),
        "exists": target.exists(),
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "primary_package": current_machine.get("primary_package"),
        "ordered_try_list": [str(item) for item in current_machine.get("ordered_try_list") or []],
        "cuda_available": current_machine.get("cuda_available"),
        "native_extension_loaded": current_machine.get("native_extension_loaded"),
        "package_labels": package_labels,
        "package_count": len(package_labels),
        "default_promotion_status": default_promotion.get("status"),
        "default_promotion_passed": default_promotion.get("passed"),
        "default_promotion_default_change_ready": default_promotion.get("default_change_ready"),
        "default_route_passed": default_promotion.get("default_route_passed"),
        "default_route_route_contract_passed": default_promotion.get(
            "default_route_route_contract_passed"
        ),
        "default_route_route_check_count": default_promotion.get("default_route_route_check_count"),
        "default_route_speedup_vs_reference": default_promotion.get(
            "default_route_speedup_vs_reference"
        ),
    }


def _run_gh(command: list[str], *, timeout_s: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_s,
        )
    except Exception as exc:  # pragma: no cover - environment-specific diagnostics
        return {
            "command": command,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "exception": type(exc).__name__,
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "exception": None,
    }


def _has_native_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "native_guardrails_bundle_status",
            "resident_result_contract_source",
            "resident_result_contract_run_default",
            "resident_result_contract_json",
            "resident_native_calibration_artifact",
            "resident_calibration_master_count",
            "resident_calibrated_light_count",
        )
    )


def _has_registration_fastpath_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "resident_registration_fastpath_status",
            "resident_registration_fastpath_contract_status",
            "resident_registration_fastpath_mode",
            "triangle_descriptor_fit_batch",
            "triangle_descriptor_fit_batch_mode",
            "triangle_descriptor_fit_device_reuse",
            "triangle_pixel_refine_batch",
            "triangle_pixel_refine_batch_metric_mode",
            "triangle_warp_batch",
            "triangle_warp_batch_mode",
            "triangle_warp_batch_frame_count",
            "resident_warp_copy_mode",
            "resident_warp_scratch_bytes",
            "resident_registration_fastpath_contract_check_count",
            "resident_registration_fastpath_contract_failed_check_count",
        )
    )


def _has_pipeline_contract_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "pipeline_contract_status",
            "pipeline_contract_passed",
            "pipeline_integration_dq_contract",
            "pipeline_integration_stack_result_contract",
            "pipeline_integration_resident_result_contract",
            "pipeline_pixel_verification_enabled",
            "pipeline_integration_dq_map_pixels_match_summary",
            "pipeline_integration_coverage_map_pixels_match_dq",
            "pipeline_integration_rejection_map_pixels_match_dq",
        )
    )


def _has_release_decision_phase2_provenance(phase2_status: dict[str, Any]) -> bool:
    return any(
        phase2_status.get(key) is not None
        for key in (
            "release_decision_status",
            "release_decision_recommendation",
            "release_decision_default_change_ready",
            "release_runtime_repeat_run_count",
            "release_runtime_repeat_elapsed_ratio_vs_best",
        )
    )


def _release_notes(payload: dict[str, Any]) -> str:
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    phase2_compare = phase2.get("status_compare") if isinstance(phase2.get("status_compare"), dict) else {}
    release_matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    install_order = release_matrix.get("ordered_try_list") or ["cuda13", "cuda12", "cuda11", "cpu"]
    lines = [
        f"# {payload['release']['title']}",
        "",
        "Windows portable packages for GLASS.",
        "",
        f"- Source stamp: `{', '.join(payload.get('source_stamps') or [])}`",
        f"- Package count: `{len(payload.get('assets') or [])}`",
        "",
        "## Assets",
        "",
        "| Label | Size bytes | SHA256 |",
        "| --- | ---: | --- |",
    ]
    for asset in payload.get("assets") or []:
        lines.append(
            f"| {asset.get('label')} | {asset.get('size_bytes')} | `{asset.get('sha256')}` |"
        )
    lines.extend(
        [
            "",
            "## Recommended Install Order",
            "",
            "Try " + ", then ".join(f"`{item}`" for item in install_order) + ".",
            "",
        ]
    )
    if release_matrix:
        lines.extend(
            [
                "## Windows Release Matrix Evidence",
                "",
                (
                    "- Windows release matrix: "
                    f"`{release_matrix.get('status')}` passed `{release_matrix.get('passed')}`"
                ),
                (
                    "- Primary package: "
                    f"`{release_matrix.get('primary_package')}` "
                    f"packages `{', '.join(release_matrix.get('package_labels') or [])}`"
                ),
                (
                    "- Default promotion: "
                    f"`{release_matrix.get('default_promotion_status')}` "
                    f"passed `{release_matrix.get('default_promotion_passed')}`"
                ),
                (
                    "- Default route contract: "
                    f"`{release_matrix.get('default_route_route_contract_passed')}` "
                    f"checks `{release_matrix.get('default_route_route_check_count')}` "
                    f"speedup `{release_matrix.get('default_route_speedup_vs_reference')}`"
                ),
                "",
            ]
        )
    if phase2_status or phase2_compare:
        lines.extend(
            [
                "## Phase 2 Handoff Evidence",
                "",
                f"- Phase 2 status: `{phase2_status.get('status')}` gate `{phase2_status.get('latest_gate')}`",
            ]
        )
        if _has_native_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Native resident contract source: "
                        f"`{phase2_status.get('resident_result_contract_source')}` "
                        f"run-default `{phase2_status.get('resident_result_contract_run_default')}`"
                    ),
                    (
                        "- Native calibration artifact: "
                        f"`{phase2_status.get('resident_native_calibration_artifact')}` "
                        f"masters `{phase2_status.get('resident_calibration_master_count')}` "
                        f"calibrated lights `{phase2_status.get('resident_calibrated_light_count')}`"
                    ),
                ]
            )
        if _has_registration_fastpath_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Resident registration fast path: "
                        f"`{phase2_status.get('resident_registration_fastpath_status')}` "
                        "contract "
                        f"`{phase2_status.get('resident_registration_fastpath_contract_status')}` "
                        f"mode `{phase2_status.get('resident_registration_fastpath_mode')}`"
                    ),
                    (
                        "- Fast path details: descriptor batch "
                        f"`{phase2_status.get('triangle_descriptor_fit_batch')}`, "
                        f"pixel refine batch `{phase2_status.get('triangle_pixel_refine_batch')}`, "
                        f"warp batch `{phase2_status.get('triangle_warp_batch')}` "
                        f"frames `{phase2_status.get('triangle_warp_batch_frame_count')}`, "
                        f"copy `{phase2_status.get('resident_warp_copy_mode')}`"
                    ),
                ]
            )
        if _has_pipeline_contract_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Pipeline DQ contract: "
                        f"`{phase2_status.get('pipeline_contract_status')}` "
                        f"passed `{phase2_status.get('pipeline_contract_passed')}` "
                        f"DQ `{phase2_status.get('pipeline_integration_dq_contract')}`"
                    ),
                    (
                        "- Pipeline pixel verification: "
                        f"`{phase2_status.get('pipeline_pixel_verification_enabled')}` "
                        "DQ pixels "
                        f"`{phase2_status.get('pipeline_integration_dq_map_pixels_match_summary')}` "
                        "coverage "
                        f"`{phase2_status.get('pipeline_integration_coverage_map_pixels_match_dq')}` "
                        "rejection "
                        f"`{phase2_status.get('pipeline_integration_rejection_map_pixels_match_dq')}`"
                    ),
                ]
            )
        if _has_release_decision_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Default-change decision: "
                        f"`{phase2_status.get('release_decision_status')}` "
                        f"ready `{phase2_status.get('release_decision_default_change_ready')}` "
                        f"recommendation `{phase2_status.get('release_decision_recommendation')}`"
                    ),
                    (
                        "- Runtime repeat evidence: runs "
                        f"`{phase2_status.get('release_runtime_repeat_run_count')}`, "
                        f"best `{phase2_status.get('release_runtime_repeat_best_label')}` "
                        f"`{phase2_status.get('release_runtime_repeat_best_elapsed_s')}` s, "
                        "ratio "
                        f"`{phase2_status.get('release_runtime_repeat_elapsed_ratio_vs_best')}`"
                    ),
                ]
            )
        lines.extend(
            [
                (
                    "- Phase 2 status compare: "
                    f"`{phase2_compare.get('status')}` "
                    f"baseline `{phase2_compare.get('baseline_gate')}` "
                    f"candidate `{phase2_compare.get('candidate_gate')}`"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _powershell_release_script(payload: dict[str, Any]) -> str:
    release = payload.get("release") if isinstance(payload.get("release"), dict) else {}
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    phase2_compare = phase2.get("status_compare") if isinstance(phase2.get("status_compare"), dict) else {}
    release_matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    gh_path = gh.get("path") or "gh"
    notes_file = release.get("notes_file")
    assets = payload.get("assets") if isinstance(payload.get("assets"), list) else []

    lines = [
        "param(",
        f"    [string]$GhPath = {_ps_literal(str(gh_path))},",
        "    [switch]$Publish",
        ")",
        "",
        "$ErrorActionPreference = 'Stop'",
        f"$ExpectedTag = {_ps_literal(str(release.get('tag') or ''))}",
        f"$ReleaseTitle = {_ps_literal(str(release.get('title') or ''))}",
        f"$NotesFile = {_ps_literal(str(notes_file) if notes_file else None)}",
        f"$WindowsReleaseMatrixFile = {_ps_literal(release_matrix.get('path'))}",
        f"$Phase2StatusFile = {_ps_literal(phase2_status.get('path'))}",
        f"$Phase2StatusCompareFile = {_ps_literal(phase2_compare.get('path'))}",
        "$Assets = @(",
    ]
    for index, asset in enumerate(assets):
        suffix = "," if index + 1 < len(assets) else ""
        lines.append(
            "    @{"
            f" Label = {_ps_literal(str(asset.get('label') or ''))};"
            f" Path = {_ps_literal(str(asset.get('zip_path') or ''))};"
            f" Sha256 = {_ps_literal(str(asset.get('sha256') or ''))};"
            f" SizeBytes = {int(asset.get('size_bytes') or 0)}"
            f" }}{suffix}"
        )
    lines.extend(
        [
            ")",
            "",
            "if (-not (Get-Command $GhPath -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $GhPath -PathType Leaf)) {",
            "    throw \"GitHub CLI not found: $GhPath\"",
            "}",
            "& $GhPath auth status | Out-Host",
            "if ($LASTEXITCODE -ne 0) {",
            "    throw 'GitHub CLI authentication check failed. Run gh auth login, then retry.'",
            "}",
            "",
            "foreach ($asset in $Assets) {",
            "    if (-not (Test-Path -LiteralPath $asset.Path -PathType Leaf)) {",
            "        throw \"Missing release asset: $($asset.Path)\"",
            "    }",
            "    $actualSize = (Get-Item -LiteralPath $asset.Path).Length",
            "    if ($actualSize -ne [int64]$asset.SizeBytes) {",
            "        throw \"Asset size mismatch for $($asset.Label): expected $($asset.SizeBytes), got $actualSize\"",
            "    }",
            "    $actualSha = (Get-FileHash -LiteralPath $asset.Path -Algorithm SHA256).Hash.ToLowerInvariant()",
            "    if ($actualSha -ne $asset.Sha256.ToLowerInvariant()) {",
            "        throw \"Asset SHA256 mismatch for $($asset.Label): expected $($asset.Sha256), got $actualSha\"",
            "    }",
            "}",
            "if ($NotesFile -and -not (Test-Path -LiteralPath $NotesFile -PathType Leaf)) {",
            "    throw \"Missing release notes file: $NotesFile\"",
            "}",
            "if ($WindowsReleaseMatrixFile) {",
            "    if (-not (Test-Path -LiteralPath $WindowsReleaseMatrixFile -PathType Leaf)) {",
            "        throw \"Missing Windows release matrix artifact: $WindowsReleaseMatrixFile\"",
            "    }",
            "    $matrix = Get-Content -LiteralPath $WindowsReleaseMatrixFile -Raw | ConvertFrom-Json",
            "    if ($matrix.artifact_type -ne 'windows_release_matrix' -or $matrix.status -ne 'release_matrix_ready' -or $matrix.passed -ne $true) {",
            "        throw \"Windows release matrix check failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "    if (-not $matrix.default_promotion_manifest -or $matrix.default_promotion_manifest.status -ne 'default_promotion_ready' -or $matrix.default_promotion_manifest.passed -ne $true -or $matrix.default_promotion_manifest.default_route_passed -ne $true) {",
            "        throw \"Windows release matrix default-promotion evidence failed: $WindowsReleaseMatrixFile\"",
            "    }",
            "}",
            "if ($Phase2StatusFile) {",
            "    if (-not (Test-Path -LiteralPath $Phase2StatusFile -PathType Leaf)) {",
            "        throw \"Missing Phase 2 status artifact: $Phase2StatusFile\"",
            "    }",
            "    $phase2Status = Get-Content -LiteralPath $Phase2StatusFile -Raw | ConvertFrom-Json",
            "    if ($phase2Status.artifact_type -ne 'glass_phase2_status' -or $phase2Status.status -ne 'green' -or $phase2Status.passed -ne $true) {",
            "        throw \"Phase 2 status check failed: $Phase2StatusFile\"",
            "    }",
            "}",
            "if ($Phase2StatusCompareFile) {",
            "    if (-not (Test-Path -LiteralPath $Phase2StatusCompareFile -PathType Leaf)) {",
            "        throw \"Missing Phase 2 status compare artifact: $Phase2StatusCompareFile\"",
            "    }",
            "    $phase2Compare = Get-Content -LiteralPath $Phase2StatusCompareFile -Raw | ConvertFrom-Json",
            "    if ($phase2Compare.artifact_type -ne 'glass_phase2_status_compare' -or $phase2Compare.status -ne 'passed' -or $phase2Compare.passed -ne $true) {",
            "        throw \"Phase 2 status compare check failed: $Phase2StatusCompareFile\"",
            "    }",
            "}",
            "",
            "$releaseArgs = @('release', 'create', $ExpectedTag)",
            "$releaseArgs += @($Assets | ForEach-Object { $_.Path })",
            "$releaseArgs += @('--title', $ReleaseTitle)",
            "if ($NotesFile) {",
            "    $releaseArgs += @('--notes-file', $NotesFile)",
            "}",
        ]
    )
    if release.get("draft") is True:
        lines.append("$releaseArgs += '--draft'")
    if release.get("prerelease") is True:
        lines.append("$releaseArgs += '--prerelease'")
    lines.extend(
        [
            "",
            "Write-Host 'GLASS release assets verified.'",
            "Write-Host 'Dry-run complete. Re-run this script with -Publish to create the GitHub release.'",
            "if (-not $Publish) {",
            "    exit 0",
            "}",
            "& $GhPath @releaseArgs",
            "if ($LASTEXITCODE -ne 0) {",
            "    throw \"GitHub release creation failed with exit code $LASTEXITCODE\"",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def build_windows_github_release_plan(
    *,
    manifest_artifact: str | Path,
    tag: str,
    title: str | None = None,
    notes_file: str | Path | None = None,
    draft: bool = True,
    prerelease: bool = False,
    require_same_source_stamp: bool = False,
    check_gh: bool = False,
    check_gh_auth: bool = False,
    gh_path: str | Path | None = None,
    phase2_status: str | Path | None = None,
    phase2_status_compare: str | Path | None = None,
    windows_release_matrix: str | Path | None = None,
    require_windows_release_matrix: bool = True,
) -> dict[str, Any]:
    manifest_path = Path(manifest_artifact)
    manifest = _read_json_object(manifest_path)
    assets = _asset_rows(manifest)
    phase2_status_summary = _phase2_artifact_summary(
        phase2_status,
        expected_artifact_type="glass_phase2_status",
    )
    phase2_compare_summary = _phase2_artifact_summary(
        phase2_status_compare,
        expected_artifact_type="glass_phase2_status_compare",
    )
    release_matrix_summary = _windows_release_matrix_summary(windows_release_matrix)
    source_stamps = sorted({str(row["source_stamp"]) for row in assets if row.get("source_stamp")})
    release_title = title or f"GLASS {tag} Windows packages"
    notes_path = str(Path(notes_file).resolve()) if notes_file is not None else None
    gh_exe = str(gh_path) if gh_path is not None else shutil.which("gh")
    if gh_exe is not None and not Path(gh_exe).exists() and Path(gh_exe).is_absolute():
        gh_exe = None
    gh_version = _run_gh([gh_exe, "--version"]) if check_gh and gh_exe else None
    gh_auth = _run_gh([gh_exe, "auth", "status"]) if check_gh_auth and gh_exe else None
    gh_auth_ok = gh_auth is not None and gh_auth.get("returncode") == 0

    checks: list[dict[str, Any]] = [
        _check(
            "manifest_passed",
            manifest.get("passed") is True,
            {"manifest_status": manifest.get("status"), "failed_checks": manifest.get("failed_checks")},
        ),
        _check("assets_present", bool(assets), {"asset_count": len(assets)}),
    ]
    for asset in assets:
        label = str(asset.get("label"))
        checks.extend(
            [
                _check(f"asset_exists:{label}", bool(asset.get("exists")), {"path": asset.get("zip_path")}),
                _check(
                    f"asset_has_sha256:{label}",
                    isinstance(asset.get("sha256"), str) and len(str(asset["sha256"])) == 64,
                    {"sha256": asset.get("sha256")},
                ),
                _check(
                    f"asset_nonempty:{label}",
                    isinstance(asset.get("size_bytes"), int) and int(asset["size_bytes"]) > 0,
                    {"size_bytes": asset.get("size_bytes")},
                ),
            ]
        )
    if require_same_source_stamp:
        checks.append(
            _check(
                "same_source_stamp",
                len(source_stamps) == 1,
                {"source_stamps": source_stamps},
            )
        )
    if phase2_status_summary is not None:
        checks.extend(
            [
                _check(
                    "phase2_status_present",
                    bool(phase2_status_summary.get("exists")),
                    {"path": phase2_status_summary.get("path")},
                ),
                _check(
                    "phase2_status_type",
                    phase2_status_summary.get("artifact_type") == "glass_phase2_status",
                    {
                        "artifact_type": phase2_status_summary.get("artifact_type"),
                        "required": "glass_phase2_status",
                    },
                ),
                _check(
                    "phase2_status_green",
                    phase2_status_summary.get("status") == "green"
                    and phase2_status_summary.get("passed") is True,
                    {
                        "status": phase2_status_summary.get("status"),
                        "passed": phase2_status_summary.get("passed"),
                        "latest_gate": phase2_status_summary.get("latest_gate"),
                    },
                ),
            ]
        )
    if phase2_compare_summary is not None:
        checks.extend(
            [
                _check(
                    "phase2_status_compare_present",
                    bool(phase2_compare_summary.get("exists")),
                    {"path": phase2_compare_summary.get("path")},
                ),
                _check(
                    "phase2_status_compare_type",
                    phase2_compare_summary.get("artifact_type") == "glass_phase2_status_compare",
                    {
                        "artifact_type": phase2_compare_summary.get("artifact_type"),
                        "required": "glass_phase2_status_compare",
                    },
                ),
                _check(
                    "phase2_status_compare_passed",
                    phase2_compare_summary.get("status") == "passed"
                    and phase2_compare_summary.get("passed") is True,
                    {
                        "status": phase2_compare_summary.get("status"),
                        "passed": phase2_compare_summary.get("passed"),
                        "baseline_gate": phase2_compare_summary.get("baseline_gate"),
                        "candidate_gate": phase2_compare_summary.get("candidate_gate"),
                    },
                ),
            ]
        )
    release_matrix_for_checks = release_matrix_summary or {}
    if require_windows_release_matrix or release_matrix_summary is not None:
        asset_labels = {str(asset.get("label")) for asset in assets if asset.get("label")}
        matrix_labels = [
            str(label) for label in release_matrix_for_checks.get("package_labels") or []
        ]
        missing_matrix_assets = [label for label in matrix_labels if label not in asset_labels]
        checks.extend(
            [
                _check(
                    "windows_release_matrix_present",
                    bool(release_matrix_summary and release_matrix_summary.get("exists")),
                    {
                        "path": release_matrix_for_checks.get("path"),
                        "required": bool(require_windows_release_matrix),
                    },
                ),
                _check(
                    "windows_release_matrix_type",
                    release_matrix_for_checks.get("artifact_type") == "windows_release_matrix",
                    {
                        "artifact_type": release_matrix_for_checks.get("artifact_type"),
                        "required": "windows_release_matrix",
                    },
                ),
                _check(
                    "windows_release_matrix_ready",
                    release_matrix_for_checks.get("status") == "release_matrix_ready"
                    and release_matrix_for_checks.get("passed") is True,
                    {
                        "status": release_matrix_for_checks.get("status"),
                        "passed": release_matrix_for_checks.get("passed"),
                    },
                ),
                _check(
                    "windows_release_matrix_default_promotion_ready",
                    release_matrix_for_checks.get("default_promotion_status")
                    == "default_promotion_ready"
                    and release_matrix_for_checks.get("default_promotion_passed") is True
                    and release_matrix_for_checks.get("default_promotion_default_change_ready")
                    is True,
                    {
                        "status": release_matrix_for_checks.get("default_promotion_status"),
                        "passed": release_matrix_for_checks.get("default_promotion_passed"),
                        "default_change_ready": release_matrix_for_checks.get(
                            "default_promotion_default_change_ready"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_default_route_passed",
                    release_matrix_for_checks.get("default_route_passed") is True
                    and release_matrix_for_checks.get("default_route_route_contract_passed") is True
                    and int(release_matrix_for_checks.get("default_route_route_check_count") or 0)
                    >= 4,
                    {
                        "default_route_passed": release_matrix_for_checks.get(
                            "default_route_passed"
                        ),
                        "route_contract_passed": release_matrix_for_checks.get(
                            "default_route_route_contract_passed"
                        ),
                        "route_check_count": release_matrix_for_checks.get(
                            "default_route_route_check_count"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_assets_present",
                    bool(matrix_labels) and not missing_matrix_assets,
                    {
                        "matrix_labels": matrix_labels,
                        "asset_labels": sorted(asset_labels),
                        "missing": missing_matrix_assets,
                    },
                ),
                _check(
                    "windows_release_matrix_try_order_has_cpu_fallback",
                    "cpu" in (release_matrix_for_checks.get("ordered_try_list") or []),
                    {"ordered_try_list": release_matrix_for_checks.get("ordered_try_list")},
                ),
            ]
        )

    failed = [item for item in checks if not item.get("passed")]
    command_parts = [
        "gh",
        "release",
        "create",
        _quote(tag),
    ]
    command_parts.extend(_quote(str(asset["zip_path"])) for asset in assets if asset.get("zip_path"))
    command_parts.extend(
        [
            "--title",
            _quote(release_title),
        ]
    )
    if notes_path is not None:
        command_parts.extend(["--notes-file", _quote(notes_path)])
    if draft:
        command_parts.append("--draft")
    if prerelease:
        command_parts.append("--prerelease")
    release_command = " ".join(str(part) for part in command_parts if str(part).strip())
    gh_cli_ready = not check_gh or gh_exe is not None
    gh_auth_ready = not check_gh_auth or gh_auth_ok
    publication_ready = not failed and gh_cli_ready and gh_auth_ready
    recommendation = "run_release_command"
    if failed:
        recommendation = "fix_release_plan_blockers"
    elif check_gh and gh_exe is None:
        recommendation = "install_github_cli_then_run_release_command"
    elif check_gh_auth and not gh_auth_ok:
        recommendation = "authenticate_github_cli_then_run_release_command"

    return {
        "schema_version": 1,
        "artifact_type": "windows_github_release_plan",
        "created_at": now_iso(),
        "status": "release_plan_ready" if not failed else "blocked",
        "passed": not failed,
        "publication_ready": publication_ready,
        "recommendation": recommendation,
        "manifest_artifact": str(manifest_path),
        "release": {
            "tag": tag,
            "title": release_title,
            "draft": bool(draft),
            "prerelease": bool(prerelease),
            "notes_file": notes_path,
            "command": release_command,
        },
        "gh": {
            "checked": bool(check_gh),
            "auth_checked": bool(check_gh_auth),
            "available": gh_exe is not None,
            "path": gh_exe,
            "version": gh_version,
            "auth_status": gh_auth,
            "auth_ok": gh_auth_ok,
        },
        "phase2": {
            "status": phase2_status_summary,
            "status_compare": phase2_compare_summary,
        },
        "release_matrix": release_matrix_summary,
        "requirements": {
            "require_windows_release_matrix": bool(require_windows_release_matrix),
        },
        "source_stamps": source_stamps,
        "assets": assets,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This is a release handoff plan; it does not create a GitHub release or upload assets.",
            "Install and authenticate GitHub CLI before running the generated command.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    release = payload.get("release") if isinstance(payload.get("release"), dict) else {}
    gh = payload.get("gh") if isinstance(payload.get("gh"), dict) else {}
    phase2 = payload.get("phase2") if isinstance(payload.get("phase2"), dict) else {}
    phase2_status = phase2.get("status") if isinstance(phase2.get("status"), dict) else {}
    phase2_compare = phase2.get("status_compare") if isinstance(phase2.get("status_compare"), dict) else {}
    release_matrix = (
        payload.get("release_matrix") if isinstance(payload.get("release_matrix"), dict) else {}
    )
    lines = [
        "# GLASS Windows GitHub Release Plan",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Publication ready: `{payload.get('publication_ready')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Tag: `{release.get('tag')}`",
        f"- Title: `{release.get('title')}`",
        f"- Source stamps: `{', '.join(payload.get('source_stamps') or [])}`",
        f"- GitHub CLI available: `{gh.get('available')}`",
        f"- GitHub CLI auth OK: `{gh.get('auth_ok')}`",
            f"- Publish script: `{release.get('script_file')}`",
            f"- Publish script mode: `{release.get('script_default_mode')}`",
            f"- Windows release matrix: `{release_matrix.get('status')}`",
            "",
        "## Assets",
        "",
        "| Label | Size bytes | SHA256 | Path |",
        "| --- | ---: | --- | --- |",
    ]
    for asset in payload.get("assets") or []:
        lines.append(
            "| "
            f"{asset.get('label')} | {asset.get('size_bytes')} | `{asset.get('sha256')}` | "
            f"`{asset.get('zip_path')}` |"
        )
    if release_matrix:
        lines.extend(
            [
                "",
                "## Windows Release Matrix Handoff",
                "",
                f"- Matrix path: `{release_matrix.get('path')}`",
                f"- Matrix status: `{release_matrix.get('status')}`",
                f"- Matrix passed: `{release_matrix.get('passed')}`",
                f"- Primary package: `{release_matrix.get('primary_package')}`",
                f"- Try order: `{', '.join(release_matrix.get('ordered_try_list') or [])}`",
                (
                    "- Default promotion: "
                    f"`{release_matrix.get('default_promotion_status')}` "
                    f"passed `{release_matrix.get('default_promotion_passed')}`"
                ),
                (
                    "- Default route contract/checks: "
                    f"`{release_matrix.get('default_route_route_contract_passed')}`/"
                    f"`{release_matrix.get('default_route_route_check_count')}`"
                ),
            ]
        )
    if phase2_status or phase2_compare:
        lines.extend(
            [
                "",
                "## Phase 2 Handoff Preflight",
                "",
                f"- Phase 2 status path: `{phase2_status.get('path')}`",
                f"- Phase 2 status: `{phase2_status.get('status')}`",
                f"- Phase 2 latest gate: `{phase2_status.get('latest_gate')}`",
            ]
        )
        if _has_native_phase2_provenance(phase2_status):
            lines.extend(
                [
                    f"- Native guardrails bundle: `{phase2_status.get('native_guardrails_bundle_status')}`",
                    f"- Native resident contract source: `{phase2_status.get('resident_result_contract_source')}`",
                    (
                        "- Native resident result run default: "
                        f"`{phase2_status.get('resident_result_contract_run_default')}`"
                    ),
                    f"- Native resident result contract: `{phase2_status.get('resident_result_contract_json')}`",
                    (
                        "- Native calibration artifact: "
                        f"`{phase2_status.get('resident_native_calibration_artifact')}`"
                    ),
                    f"- Native calibration masters: `{phase2_status.get('resident_calibration_master_count')}`",
                    f"- Native calibrated lights: `{phase2_status.get('resident_calibrated_light_count')}`",
                ]
            )
        if _has_registration_fastpath_phase2_provenance(phase2_status):
            lines.extend(
                [
                    (
                        "- Resident registration fast path: "
                        f"`{phase2_status.get('resident_registration_fastpath_status')}`"
                    ),
                    (
                        "- Resident registration fast path contract: "
                        f"`{phase2_status.get('resident_registration_fastpath_contract_status')}` "
                        f"checks `{phase2_status.get('resident_registration_fastpath_contract_check_count')}` "
                        "failed "
                        f"`{phase2_status.get('resident_registration_fastpath_contract_failed_check_count')}`"
                    ),
                    (
                        "- Resident registration fast path mode: "
                        f"`{phase2_status.get('resident_registration_fastpath_mode')}`"
                    ),
                    (
                        "- Descriptor fit batch: "
                        f"`{phase2_status.get('triangle_descriptor_fit_batch')}` "
                        f"mode `{phase2_status.get('triangle_descriptor_fit_batch_mode')}`"
                    ),
                    (
                        "- Descriptor device reuse: "
                        f"`{phase2_status.get('triangle_descriptor_fit_device_reuse')}`"
                    ),
                    (
                        "- Pixel refine batch: "
                        f"`{phase2_status.get('triangle_pixel_refine_batch')}` "
                        f"metric `{phase2_status.get('triangle_pixel_refine_batch_metric_mode')}`"
                    ),
                    (
                        "- Triangle warp batch: "
                        f"`{phase2_status.get('triangle_warp_batch')}` "
                        f"mode `{phase2_status.get('triangle_warp_batch_mode')}` "
                        f"frames `{phase2_status.get('triangle_warp_batch_frame_count')}`"
                    ),
                    f"- Resident warp copy mode: `{phase2_status.get('resident_warp_copy_mode')}`",
                    f"- Resident warp scratch bytes: `{phase2_status.get('resident_warp_scratch_bytes')}`",
                ]
            )
        if _has_pipeline_contract_phase2_provenance(phase2_status):
            lines.extend(
                [
                    f"- Pipeline contract: `{phase2_status.get('pipeline_contract_status')}`",
                    f"- Pipeline contract passed: `{phase2_status.get('pipeline_contract_passed')}`",
                    (
                        "- Pipeline contract failed checks: "
                        f"`{phase2_status.get('pipeline_contract_failed_check_count')}`"
                    ),
                    (
                        "- Pipeline integration outputs/maps: "
                        f"`{phase2_status.get('pipeline_integration_output_count')}`/"
                        f"`{phase2_status.get('pipeline_integration_map_count')}`"
                    ),
                    (
                        "- Pipeline integration DQ contract: "
                        f"`{phase2_status.get('pipeline_integration_dq_contract')}`"
                    ),
                    (
                        "- Pipeline StackEngine result contract: "
                        f"`{phase2_status.get('pipeline_integration_stack_result_contract')}`"
                    ),
                    (
                        "- Pipeline resident result contract: "
                        f"`{phase2_status.get('pipeline_integration_resident_result_contract')}`"
                    ),
                    (
                        "- Pipeline pixel verification: "
                        f"`{phase2_status.get('pipeline_pixel_verification_enabled')}`"
                    ),
                    (
                        "- Pipeline DQ pixels match summary: "
                        f"`{phase2_status.get('pipeline_integration_dq_map_pixels_match_summary')}`"
                    ),
                    (
                        "- Pipeline coverage pixels match DQ: "
                        f"`{phase2_status.get('pipeline_integration_coverage_map_pixels_match_dq')}`"
                    ),
                    (
                        "- Pipeline rejection pixels match DQ: "
                        f"`{phase2_status.get('pipeline_integration_rejection_map_pixels_match_dq')}`"
                    ),
                ]
            )
        if _has_release_decision_phase2_provenance(phase2_status):
            lines.extend(
                [
                    f"- Release decision: `{phase2_status.get('release_decision_status')}`",
                    (
                        "- Release recommendation: "
                        f"`{phase2_status.get('release_decision_recommendation')}`"
                    ),
                    (
                        "- Default change ready: "
                        f"`{phase2_status.get('release_decision_default_change_ready')}`"
                    ),
                    (
                        "- Runtime repeat runs: "
                        f"`{phase2_status.get('release_runtime_repeat_run_count')}`"
                    ),
                    (
                        "- Runtime repeat best: "
                        f"`{phase2_status.get('release_runtime_repeat_best_label')}` "
                        f"`{phase2_status.get('release_runtime_repeat_best_elapsed_s')}` s"
                    ),
                    (
                        "- Runtime repeat ratio vs best: "
                        f"`{phase2_status.get('release_runtime_repeat_elapsed_ratio_vs_best')}`"
                    ),
                ]
            )
        lines.extend(
            [
                f"- Phase 2 status compare path: `{phase2_compare.get('path')}`",
                f"- Phase 2 status compare: `{phase2_compare.get('status')}`",
                f"- Phase 2 compare baseline gate: `{phase2_compare.get('baseline_gate')}`",
                f"- Phase 2 compare candidate gate: `{phase2_compare.get('candidate_gate')}`",
            ]
        )
    lines.extend(["", "## Command", "", "```powershell", str(release.get("command") or ""), "```", ""])
    lines.extend(["## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_github_release_plan(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
    notes: str | Path | None = None,
    script: str | Path | None = None,
) -> None:
    if script is not None:
        release = payload.get("release")
        if isinstance(release, dict):
            release["script_file"] = str(Path(script).resolve())
            release["script_default_mode"] = "dry_run_requires_publish_switch"
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
    if notes is not None:
        Path(notes).parent.mkdir(parents=True, exist_ok=True)
        Path(notes).write_text(_release_notes(payload), encoding="utf-8")
    if script is not None:
        Path(script).parent.mkdir(parents=True, exist_ok=True)
        Path(script).write_text(_powershell_release_script(payload), encoding="utf-8")
