from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso
from glass.utils.checksums import sha256_file


def parse_labeled_zip_paths(specs: list[str] | tuple[str, ...] | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for spec in specs or []:
        if "=" not in spec:
            raise ValueError(f"Expected LABEL=PATH: {spec}")
        label, path = spec.split("=", 1)
        label = label.strip()
        path = path.strip()
        if not label or not path:
            raise ValueError(f"Expected LABEL=PATH: {spec}")
        mapping[label] = path
    return mapping


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _windows_release_matrix_summary(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    payload = _read_json_object(target) if target.exists() else {}
    machine = payload.get("current_machine") if isinstance(payload.get("current_machine"), dict) else {}
    default_promotion = (
        payload.get("default_promotion_manifest")
        if isinstance(payload.get("default_promotion_manifest"), dict)
        else {}
    )
    packages = [row for row in payload.get("packages") or [] if isinstance(row, dict)]
    labels = [str(row.get("label")) for row in packages if row.get("label")]
    return {
        "path": str(target),
        "exists": target.exists(),
        "artifact_type": payload.get("artifact_type"),
        "status": payload.get("status"),
        "passed": payload.get("passed"),
        "recommendation": payload.get("recommendation"),
        "primary_package": machine.get("primary_package"),
        "ordered_try_list": [str(item) for item in machine.get("ordered_try_list") or []],
        "package_labels": labels,
        "package_count": len(labels),
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


def _zip_row(row: dict[str, Any], overrides: dict[str, str]) -> dict[str, Any]:
    label = str(row.get("label") or "")
    zip_path = overrides.get(label) or row.get("zip_path")
    zip_file = Path(str(zip_path)).resolve() if zip_path else None
    exists = zip_file is not None and zip_file.exists() and zip_file.is_file()
    size_bytes = zip_file.stat().st_size if exists and zip_file is not None else None
    digest = sha256_file(zip_file) if exists and zip_file is not None else None
    return {
        "label": label,
        "zip_path": None if zip_file is None else str(zip_file),
        "exists": bool(exists),
        "size_bytes": size_bytes,
        "sha256": digest,
        "smoke_zip_size_bytes": row.get("zip_size_bytes"),
        "source_stamp": row.get("source_stamp"),
        "package_label": row.get("package_label"),
        "suite_row_passed": row.get("passed") is True,
        "smoke_artifact": row.get("path"),
        "cuda_required": row.get("require_cuda"),
        "cuda_available_at_smoke": row.get("cuda_available"),
        "native_extension_loaded_at_smoke": row.get("native_extension_loaded"),
    }


def build_windows_release_manifest(
    *,
    suite_artifact: str | Path,
    zip_overrides: dict[str, str] | None = None,
    require_same_source_stamp: bool = False,
    windows_release_matrix: str | Path | None = None,
    require_windows_release_matrix: bool = True,
) -> dict[str, Any]:
    suite_path = Path(suite_artifact)
    suite = _read_json_object(suite_path)
    rows = suite.get("rows") if isinstance(suite.get("rows"), list) else []
    zip_rows = [_zip_row(row, zip_overrides or {}) for row in rows if isinstance(row, dict)]
    source_stamps = sorted({str(row["source_stamp"]) for row in zip_rows if row.get("source_stamp")})
    matrix_summary = _windows_release_matrix_summary(windows_release_matrix)

    checks: list[dict[str, Any]] = [
        _check(
            "suite_passed",
            suite.get("passed") is True,
            {"suite_status": suite.get("status"), "suite_failed_checks": suite.get("failed_checks")},
        ),
        _check("suite_has_packages", bool(zip_rows), {"package_count": len(zip_rows)}),
    ]
    for row in zip_rows:
        label = str(row["label"])
        checks.extend(
            [
                _check(
                    f"zip_exists:{label}",
                    bool(row["exists"]),
                    {"zip_path": row.get("zip_path")},
                ),
                _check(
                    f"zip_nonempty:{label}",
                    isinstance(row.get("size_bytes"), int) and int(row["size_bytes"]) > 0,
                    {"zip_path": row.get("zip_path"), "size_bytes": row.get("size_bytes")},
                ),
                _check(
                    f"zip_size_matches_smoke:{label}",
                    row.get("smoke_zip_size_bytes") == row.get("size_bytes"),
                    {
                        "smoke_zip_size_bytes": row.get("smoke_zip_size_bytes"),
                        "manifest_size_bytes": row.get("size_bytes"),
                    },
                ),
                _check(
                    f"suite_row_passed:{label}",
                    row.get("suite_row_passed") is True,
                    {"suite_row_passed": row.get("suite_row_passed")},
                ),
                _check(
                    f"sha256_recorded:{label}",
                    isinstance(row.get("sha256"), str) and len(str(row["sha256"])) == 64,
                    {"sha256": row.get("sha256")},
                ),
            ]
        )
    matrix_for_checks = matrix_summary or {}
    if require_windows_release_matrix or matrix_summary is not None:
        manifest_labels = {str(row.get("label")) for row in zip_rows if row.get("label")}
        matrix_labels = [str(label) for label in matrix_for_checks.get("package_labels") or []]
        missing_manifest_assets = [label for label in matrix_labels if label not in manifest_labels]
        checks.extend(
            [
                _check(
                    "windows_release_matrix_present",
                    bool(matrix_summary and matrix_summary.get("exists")),
                    {
                        "path": matrix_for_checks.get("path"),
                        "required": bool(require_windows_release_matrix),
                    },
                ),
                _check(
                    "windows_release_matrix_type",
                    matrix_for_checks.get("artifact_type") == "windows_release_matrix",
                    {
                        "artifact_type": matrix_for_checks.get("artifact_type"),
                        "required": "windows_release_matrix",
                    },
                ),
                _check(
                    "windows_release_matrix_ready",
                    matrix_for_checks.get("status") == "release_matrix_ready"
                    and matrix_for_checks.get("passed") is True,
                    {
                        "status": matrix_for_checks.get("status"),
                        "passed": matrix_for_checks.get("passed"),
                    },
                ),
                _check(
                    "windows_release_matrix_default_promotion_ready",
                    matrix_for_checks.get("default_promotion_status") == "default_promotion_ready"
                    and matrix_for_checks.get("default_promotion_passed") is True
                    and matrix_for_checks.get("default_promotion_default_change_ready") is True,
                    {
                        "status": matrix_for_checks.get("default_promotion_status"),
                        "passed": matrix_for_checks.get("default_promotion_passed"),
                        "default_change_ready": matrix_for_checks.get(
                            "default_promotion_default_change_ready"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_default_route_passed",
                    matrix_for_checks.get("default_route_passed") is True
                    and matrix_for_checks.get("default_route_route_contract_passed") is True
                    and int(matrix_for_checks.get("default_route_route_check_count") or 0) >= 4,
                    {
                        "default_route_passed": matrix_for_checks.get("default_route_passed"),
                        "route_contract_passed": matrix_for_checks.get(
                            "default_route_route_contract_passed"
                        ),
                        "route_check_count": matrix_for_checks.get(
                            "default_route_route_check_count"
                        ),
                    },
                ),
                _check(
                    "windows_release_matrix_assets_present",
                    bool(matrix_labels) and not missing_manifest_assets,
                    {
                        "matrix_labels": matrix_labels,
                        "manifest_labels": sorted(manifest_labels),
                        "missing": missing_manifest_assets,
                    },
                ),
                _check(
                    "windows_release_matrix_try_order_has_cpu_fallback",
                    "cpu" in (matrix_for_checks.get("ordered_try_list") or []),
                    {"ordered_try_list": matrix_for_checks.get("ordered_try_list")},
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

    failed = [item for item in checks if not item.get("passed")]
    return {
        "schema_version": 1,
        "artifact_type": "windows_release_manifest",
        "created_at": now_iso(),
        "status": "release_manifest_ready" if not failed else "blocked",
        "passed": not failed,
        "recommendation": "ready_for_upload" if not failed else "fix_release_manifest_blockers",
        "suite_artifact": str(suite_path),
        "suite_status": suite.get("status"),
        "suite_recommendation": suite.get("recommendation"),
        "requirements": {
            "require_same_source_stamp": bool(require_same_source_stamp),
            "require_windows_release_matrix": bool(require_windows_release_matrix),
        },
        "windows_release_matrix": matrix_summary,
        "source_stamps": source_stamps,
        "packages": zip_rows,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This manifest records release files and SHA256 checksums; it does not rebuild, sign, or upload packages.",
            "ZIP checksums describe the local files at manifest time.",
            "Formal releases should publish the manifest together with signed or otherwise trusted binaries.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    matrix = (
        payload.get("windows_release_matrix")
        if isinstance(payload.get("windows_release_matrix"), dict)
        else {}
    )
    lines = [
        "# GLASS Windows Release Manifest",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Suite artifact: `{payload.get('suite_artifact')}`",
        f"- Source stamps: `{', '.join(payload.get('source_stamps') or [])}`",
        "",
        "## Packages",
        "",
        "| Label | Size bytes | SHA256 | Source | Zip |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in payload.get("packages") or []:
        lines.append(
            "| "
            f"{row.get('label')} | {row.get('size_bytes')} | `{row.get('sha256')}` | "
            f"{row.get('source_stamp')} | `{row.get('zip_path')}` |"
        )
    if matrix:
        lines.extend(
            [
                "",
                "## Windows Release Matrix",
                "",
                f"- Matrix path: `{matrix.get('path')}`",
                f"- Matrix status: `{matrix.get('status')}`",
                f"- Matrix passed: `{matrix.get('passed')}`",
                f"- Primary package: `{matrix.get('primary_package')}`",
                f"- Try order: `{', '.join(matrix.get('ordered_try_list') or [])}`",
                (
                    "- Default promotion: "
                    f"`{matrix.get('default_promotion_status')}` "
                    f"passed `{matrix.get('default_promotion_passed')}`"
                ),
                (
                    "- Default route contract/checks: "
                    f"`{matrix.get('default_route_route_contract_passed')}`/"
                    f"`{matrix.get('default_route_route_check_count')}`"
                ),
            ]
        )
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_release_manifest(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
