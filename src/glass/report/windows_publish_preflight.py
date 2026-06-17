from __future__ import annotations

from pathlib import Path
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


def _norm_path(value: str | Path | None) -> str | None:
    if value is None:
        return None
    return str(Path(str(value)).resolve(strict=False)).lower()


def _same_path(left: str | Path | None, right: str | Path | None) -> bool:
    left_norm = _norm_path(left)
    right_norm = _norm_path(right)
    return left_norm is not None and right_norm is not None and left_norm == right_norm


def _rows_by_label(rows: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = row.get("label")
        if label:
            result[str(label)] = row
    return result


def _matrix_summary(payload: dict[str, Any]) -> dict[str, Any]:
    machine = payload.get("current_machine") if isinstance(payload.get("current_machine"), dict) else {}
    promotion = (
        payload.get("default_promotion_manifest")
        if isinstance(payload.get("default_promotion_manifest"), dict)
        else {}
    )
    package_labels = [
        str(row.get("label"))
        for row in payload.get("packages") or []
        if isinstance(row, dict) and row.get("label")
    ]
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "primary_package": machine.get("primary_package"),
        "ordered_try_list": [str(item) for item in machine.get("ordered_try_list") or []],
        "package_labels": package_labels,
        "default_promotion_status": promotion.get("status"),
        "default_promotion_passed": promotion.get("passed"),
        "default_promotion_default_change_ready": promotion.get("default_change_ready"),
        "default_route_passed": promotion.get("default_route_passed"),
        "default_route_route_contract_passed": promotion.get(
            "default_route_route_contract_passed"
        ),
        "default_route_route_check_count": promotion.get("default_route_route_check_count"),
        "default_route_speedup_vs_reference": promotion.get(
            "default_route_speedup_vs_reference"
        ),
    }


def _default_promotion_summary(payload: dict[str, Any]) -> dict[str, Any]:
    route = (
        payload.get("default_route_acceptance")
        if isinstance(payload.get("default_route_acceptance"), dict)
        else {}
    )
    return {
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "default_change_ready": payload.get("default_change_ready"),
        "recommendation": payload.get("recommendation"),
        "default_route_status": route.get("status"),
        "default_route_passed": route.get("passed"),
        "default_route_route_contract_passed": route.get("route_contract_passed"),
        "default_route_route_check_count": route.get("route_check_count"),
        "default_route_speedup_vs_reference": route.get("speedup_vs_reference"),
    }


def build_windows_publish_preflight(
    *,
    release_manifest: str | Path,
    github_release_plan: str | Path,
    windows_release_matrix: str | Path,
    default_promotion_manifest: str | Path,
    require_publication_ready: bool = True,
) -> dict[str, Any]:
    manifest_path = Path(release_manifest)
    plan_path = Path(github_release_plan)
    matrix_path = Path(windows_release_matrix)
    promotion_path = Path(default_promotion_manifest)

    manifest = _read_json_object(manifest_path)
    plan = _read_json_object(plan_path)
    matrix = _read_json_object(matrix_path)
    promotion = _read_json_object(promotion_path)

    manifest_packages = _rows_by_label(manifest.get("packages") or [])
    plan_assets = _rows_by_label(plan.get("assets") or [])
    matrix_info = _matrix_summary(matrix)
    promotion_info = _default_promotion_summary(promotion)
    manifest_matrix = (
        manifest.get("windows_release_matrix")
        if isinstance(manifest.get("windows_release_matrix"), dict)
        else {}
    )
    plan_matrix = (
        plan.get("release_matrix") if isinstance(plan.get("release_matrix"), dict) else {}
    )

    manifest_labels = sorted(manifest_packages)
    asset_labels = sorted(plan_assets)
    matrix_labels = sorted(matrix_info["package_labels"])
    missing_assets = [label for label in manifest_labels if label not in plan_assets]
    missing_manifest_rows = [label for label in matrix_labels if label not in manifest_packages]
    mismatched_assets: list[str] = []
    for label, row in manifest_packages.items():
        asset = plan_assets.get(label) or {}
        if (
            asset
            and (
                row.get("sha256") != asset.get("sha256")
                or row.get("size_bytes") != asset.get("size_bytes")
                or not _same_path(row.get("zip_path"), asset.get("zip_path"))
            )
        ):
            mismatched_assets.append(label)

    checks = [
        _check(
            "release_manifest_ready",
            manifest.get("artifact_type") == "windows_release_manifest"
            and manifest.get("status") == "release_manifest_ready"
            and manifest.get("passed") is True,
            {
                "artifact_type": manifest.get("artifact_type"),
                "status": manifest.get("status"),
                "passed": manifest.get("passed"),
            },
        ),
        _check(
            "github_release_plan_ready",
            plan.get("artifact_type") == "windows_github_release_plan"
            and plan.get("status") == "release_plan_ready"
            and plan.get("passed") is True,
            {
                "artifact_type": plan.get("artifact_type"),
                "status": plan.get("status"),
                "passed": plan.get("passed"),
            },
        ),
        _check(
            "github_release_plan_publication_ready",
            plan.get("publication_ready") is True if require_publication_ready else True,
            {
                "publication_ready": plan.get("publication_ready"),
                "required": bool(require_publication_ready),
            },
        ),
        _check(
            "windows_release_matrix_ready",
            matrix_info["artifact_type"] == "windows_release_matrix"
            and matrix_info["status"] == "release_matrix_ready"
            and matrix_info["passed"] is True,
            matrix_info,
        ),
        _check(
            "default_promotion_ready",
            promotion_info["artifact_type"] == "default_promotion_manifest"
            and promotion_info["status"] == "default_promotion_ready"
            and promotion_info["passed"] is True
            and promotion_info["default_change_ready"] is True,
            promotion_info,
        ),
        _check(
            "default_route_contract_passed",
            promotion_info["default_route_passed"] is True
            and promotion_info["default_route_route_contract_passed"] is True
            and int(promotion_info["default_route_route_check_count"] or 0) >= 4,
            {
                "default_route_passed": promotion_info["default_route_passed"],
                "route_contract_passed": promotion_info["default_route_route_contract_passed"],
                "route_check_count": promotion_info["default_route_route_check_count"],
            },
        ),
        _check(
            "manifest_references_matrix",
            _same_path(manifest_matrix.get("path"), matrix_path),
            {"manifest_matrix_path": manifest_matrix.get("path"), "matrix_path": str(matrix_path)},
        ),
        _check(
            "github_plan_references_manifest",
            _same_path(plan.get("manifest_artifact"), manifest_path),
            {
                "plan_manifest_artifact": plan.get("manifest_artifact"),
                "manifest_path": str(manifest_path),
            },
        ),
        _check(
            "github_plan_references_matrix",
            _same_path(plan_matrix.get("path"), matrix_path),
            {"plan_matrix_path": plan_matrix.get("path"), "matrix_path": str(matrix_path)},
        ),
        _check(
            "matrix_default_promotion_matches_manifest",
            matrix_info["default_promotion_status"] == promotion_info["status"]
            and matrix_info["default_promotion_passed"] == promotion_info["passed"]
            and matrix_info["default_promotion_default_change_ready"]
            == promotion_info["default_change_ready"],
            {"matrix": matrix_info, "default_promotion": promotion_info},
        ),
        _check(
            "matrix_default_route_matches_manifest",
            matrix_info["default_route_passed"] == promotion_info["default_route_passed"]
            and matrix_info["default_route_route_contract_passed"]
            == promotion_info["default_route_route_contract_passed"]
            and matrix_info["default_route_route_check_count"]
            == promotion_info["default_route_route_check_count"],
            {"matrix": matrix_info, "default_promotion": promotion_info},
        ),
        _check(
            "manifest_assets_match_github_plan",
            not missing_assets and not mismatched_assets,
            {
                "manifest_labels": manifest_labels,
                "asset_labels": asset_labels,
                "missing_assets": missing_assets,
                "mismatched_assets": mismatched_assets,
            },
        ),
        _check(
            "matrix_packages_match_manifest",
            matrix_labels == manifest_labels and not missing_manifest_rows,
            {
                "matrix_labels": matrix_labels,
                "manifest_labels": manifest_labels,
                "missing_manifest_rows": missing_manifest_rows,
            },
        ),
        _check(
            "cpu_fallback_preserved",
            "cpu" in matrix_info["ordered_try_list"]
            and "cpu" in manifest_packages
            and "cpu" in plan_assets,
            {
                "ordered_try_list": matrix_info["ordered_try_list"],
                "manifest_labels": manifest_labels,
                "asset_labels": asset_labels,
            },
        ),
    ]
    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "windows_publish_preflight",
        "created_at": now_iso(),
        "status": "publish_preflight_ready" if not failed else "blocked",
        "passed": not failed,
        "recommendation": "publish_release_bundle" if not failed else "fix_publish_preflight_blockers",
        "inputs": {
            "release_manifest": str(manifest_path),
            "github_release_plan": str(plan_path),
            "windows_release_matrix": str(matrix_path),
            "default_promotion_manifest": str(promotion_path),
        },
        "requirements": {
            "require_publication_ready": bool(require_publication_ready),
        },
        "summary": {
            "release_tag": (plan.get("release") or {}).get("tag")
            if isinstance(plan.get("release"), dict)
            else None,
            "asset_count": len(plan_assets),
            "package_count": len(manifest_packages),
            "primary_package": matrix_info["primary_package"],
            "ordered_try_list": matrix_info["ordered_try_list"],
            "source_stamps": manifest.get("source_stamps") or [],
            "default_promotion_status": promotion_info["status"],
            "default_route_check_count": promotion_info["default_route_route_check_count"],
            "default_route_speedup_vs_reference": promotion_info[
                "default_route_speedup_vs_reference"
            ],
        },
        "release_manifest": {
            "status": manifest.get("status"),
            "passed": manifest.get("passed"),
            "package_labels": manifest_labels,
        },
        "github_release_plan": {
            "status": plan.get("status"),
            "passed": plan.get("passed"),
            "publication_ready": plan.get("publication_ready"),
            "asset_labels": asset_labels,
        },
        "windows_release_matrix": matrix_info,
        "default_promotion_manifest": promotion_info,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This artifact verifies local release handoff evidence; it does not upload assets or create a GitHub release.",
            "ZIP checksums are trusted from the supplied release manifest and GitHub handoff artifacts.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# GLASS Windows Publish Preflight",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Release tag: `{summary.get('release_tag')}`",
        f"- Assets/packages: `{summary.get('asset_count')}`/`{summary.get('package_count')}`",
        f"- Primary package: `{summary.get('primary_package')}`",
        f"- Try order: `{', '.join(summary.get('ordered_try_list') or [])}`",
        f"- Source stamps: `{', '.join(summary.get('source_stamps') or [])}`",
        f"- Default promotion: `{summary.get('default_promotion_status')}`",
        (
            "- Default route checks/speedup: "
            f"`{summary.get('default_route_check_count')}`/"
            f"`{summary.get('default_route_speedup_vs_reference')}`"
        ),
        "",
        "## Inputs",
        "",
    ]
    for key, value in (payload.get("inputs") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_publish_preflight(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
