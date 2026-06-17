from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso

DEFAULT_REQUIRED_LABELS = ("cuda13", "cuda12", "cuda11", "cpu")


def parse_labeled_paths(specs: list[str] | tuple[str, ...] | None) -> dict[str, str]:
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


def _read_json_object(path: str | Path) -> dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON artifact must be an object: {path}")
    return payload


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _row(label: str, path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "label": label,
            "path": None,
            "present": False,
            "passed": False,
            "status": "missing",
            "failed_checks": ["missing_smoke_artifact"],
            "package_label": None,
            "source_stamp": None,
            "zip_path": None,
            "zip_size_bytes": None,
            "require_cuda": None,
            "cuda_available": None,
            "native_extension_loaded": None,
        }
    payload = _read_json_object(path)
    package = payload.get("package") if isinstance(payload.get("package"), dict) else {}
    requirements = payload.get("requirements") if isinstance(payload.get("requirements"), dict) else {}
    execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
    doctor_json = execution.get("doctor_json") if isinstance(execution.get("doctor_json"), dict) else {}
    cuda = doctor_json.get("cuda") if isinstance(doctor_json.get("cuda"), dict) else {}
    manifest = package.get("manifest") if isinstance(package.get("manifest"), dict) else {}
    return {
        "label": label,
        "path": str(path),
        "present": True,
        "passed": payload.get("passed") is True,
        "status": payload.get("status"),
        "failed_checks": list(payload.get("failed_checks") or []),
        "package_label": manifest.get("package_label"),
        "source_stamp": package.get("source_stamp"),
        "zip_path": package.get("zip_path"),
        "zip_size_bytes": package.get("zip_size_bytes"),
        "require_cuda": requirements.get("require_cuda"),
        "cuda_available": cuda.get("cuda_available"),
        "native_extension_loaded": cuda.get("native_extension_loaded"),
    }


def build_windows_package_suite(
    *,
    smoke_artifacts: dict[str, str],
    required_labels: tuple[str, ...] = DEFAULT_REQUIRED_LABELS,
    require_same_source_stamp: bool = False,
) -> dict[str, Any]:
    rows = [_row(label, smoke_artifacts.get(label)) for label in required_labels]
    source_stamps = sorted({str(row["source_stamp"]) for row in rows if row.get("source_stamp")})
    checks: list[dict[str, Any]] = []
    for row in rows:
        label = str(row["label"])
        checks.extend(
            [
                _check(f"smoke_present:{label}", bool(row["present"]), {"path": row.get("path")}),
                _check(
                    f"smoke_passed:{label}",
                    bool(row["passed"]),
                    {"status": row.get("status"), "failed_checks": row.get("failed_checks")},
                ),
                _check(
                    f"package_label_matches:{label}",
                    row.get("package_label") == label,
                    {"actual": row.get("package_label"), "required": label},
                ),
                _check(
                    f"zip_nonempty:{label}",
                    isinstance(row.get("zip_size_bytes"), int) and int(row["zip_size_bytes"]) > 0,
                    {"zip_path": row.get("zip_path"), "zip_size_bytes": row.get("zip_size_bytes")},
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
        "artifact_type": "windows_package_suite",
        "created_at": now_iso(),
        "status": "package_suite_ready" if not failed else "blocked",
        "passed": not failed,
        "recommendation": "publish_package_suite" if not failed else "fix_package_suite_blockers",
        "requirements": {
            "required_labels": list(required_labels),
            "require_same_source_stamp": bool(require_same_source_stamp),
        },
        "source_stamps": source_stamps,
        "rows": rows,
        "checks": checks,
        "failed_checks": [str(item.get("name")) for item in failed],
        "limitations": [
            "This suite aggregates package smoke artifacts; it does not rebuild, sign, or upload packages.",
            "Mixed source stamps are allowed unless require_same_source_stamp is enabled.",
            "Formal release artifacts should normally be rebuilt from one final tag or commit.",
        ],
    }


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# GLASS Windows Package Suite",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Passed: `{payload.get('passed')}`",
        f"- Recommendation: `{payload.get('recommendation')}`",
        f"- Source stamps: `{', '.join(payload.get('source_stamps') or [])}`",
        "",
        "## Packages",
        "",
        "| Label | Passed | Source | Zip size | CUDA required | CUDA available |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            "| "
            f"{row.get('label')} | {row.get('passed')} | {row.get('source_stamp')} | "
            f"{row.get('zip_size_bytes')} | {row.get('require_cuda')} | {row.get('cuda_available')} |"
        )
    lines.extend(["", "## Checks", ""])
    for item in payload.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    lines.append("")
    return "\n".join(lines)


def write_windows_package_suite(
    out: str | Path,
    payload: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(out, payload)
    if markdown is not None:
        Path(markdown).parent.mkdir(parents=True, exist_ok=True)
        Path(markdown).write_text(_markdown(payload), encoding="utf-8")
