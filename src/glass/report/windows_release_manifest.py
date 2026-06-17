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
) -> dict[str, Any]:
    suite_path = Path(suite_artifact)
    suite = _read_json_object(suite_path)
    rows = suite.get("rows") if isinstance(suite.get("rows"), list) else []
    zip_rows = [_zip_row(row, zip_overrides or {}) for row in rows if isinstance(row, dict)]
    source_stamps = sorted({str(row["source_stamp"]) for row in zip_rows if row.get("source_stamp")})

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
        },
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
