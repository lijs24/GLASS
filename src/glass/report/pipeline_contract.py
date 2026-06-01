from __future__ import annotations

from pathlib import Path
from typing import Any

from glass.io.json_io import read_json, write_json
from glass.models import now_iso


_CORE_INTEGRATION_MAPS = {
    "master": "master_path",
    "weight": "weight_map_path",
    "coverage": "coverage_map_path",
    "dq": "dq_map_path",
}

_REJECTION_MAPS = {
    "low_rejection": "low_rejection_map_path",
    "high_rejection": "high_rejection_map_path",
}


def _load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def _check(name: str, passed: bool, evidence: dict[str, Any], note: str = "") -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "evidence": evidence, "note": note}


def _resolve_path(path_value: Any, run_root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    return path if path.is_absolute() else run_root / path


def _path_exists(path_value: Any, run_root: Path) -> bool:
    path = _resolve_path(path_value, run_root)
    return bool(path and path.exists())


def _policy_items(payload: dict[str, Any], key: str) -> set[str]:
    policy = payload.get("output_map_policy") if isinstance(payload.get("output_map_policy"), dict) else {}
    return {str(item) for item in (policy.get(key) or [])}


def _map_skipped(payload: dict[str, Any], map_name: str) -> bool:
    return map_name in _policy_items(payload, "skipped")


def _map_available_policy(payload: dict[str, Any], map_name: str) -> bool | None:
    policy = payload.get("output_map_policy") if isinstance(payload.get("output_map_policy"), dict) else {}
    available = policy.get("available")
    if not isinstance(available, list):
        return None
    return map_name in {str(item) for item in available}


def _map_row(
    payload: dict[str, Any],
    *,
    run_root: Path,
    surface: str,
    item: str,
    map_name: str,
    path_key: str,
    required: bool,
) -> dict[str, Any]:
    path_value = payload.get(path_key)
    skipped = _map_skipped(payload, map_name)
    exists = _path_exists(path_value, run_root)
    ok = bool(exists or not required or (skipped and map_name != "master"))
    return {
        "surface": surface,
        "item": item,
        "map": map_name,
        "path_key": path_key,
        "path": path_value,
        "exists": exists,
        "required": required,
        "policy_skipped": skipped,
        "ok": ok,
    }


def _integration_rejection_mode(integration: dict[str, Any], output: dict[str, Any]) -> str:
    if isinstance(output.get("integration_rejection"), dict):
        return str((output.get("integration_rejection") or {}).get("mode") or "none")
    return str(output.get("rejection") or integration.get("rejection") or "none")


def _integration_map_rows(integration: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, output in enumerate(integration.get("outputs") or []):
        if not isinstance(output, dict):
            continue
        item = str(output.get("filter") or index)
        for map_name, path_key in _CORE_INTEGRATION_MAPS.items():
            available = _map_available_policy(output, map_name)
            required = map_name == "master" or (available is not False and not _map_skipped(output, map_name))
            rows.append(
                _map_row(
                    output,
                    run_root=run_root,
                    surface="integration",
                    item=item,
                    map_name=map_name,
                    path_key=path_key,
                    required=required,
                )
            )
        rejection = _integration_rejection_mode(integration, output)
        for map_name, path_key in _REJECTION_MAPS.items():
            available = _map_available_policy(output, map_name)
            required = rejection != "none" and available is not False and not _map_skipped(output, map_name)
            rows.append(
                _map_row(
                    output,
                    run_root=run_root,
                    surface="integration",
                    item=item,
                    map_name=map_name,
                    path_key=path_key,
                    required=required,
                )
            )
    return rows


def _integration_rows(integration: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, output in enumerate(integration.get("outputs") or []):
        if not isinstance(output, dict):
            continue
        dq_summary = output.get("dq_summary")
        summary = output.get("dq_provenance_summary")
        item = str(output.get("filter") or index)
        dq_required = not _map_skipped(output, "dq")
        rows.append(
            {
                "item": item,
                "backend": output.get("backend"),
                "rejection": _integration_rejection_mode(integration, output),
                "frame_count": output.get("frame_count"),
                "dq_map_path": output.get("dq_map_path"),
                "dq_map_exists": _path_exists(output.get("dq_map_path"), run_root),
                "dq_summary_present": isinstance(dq_summary, dict),
                "dq_summary_has_valid": isinstance(dq_summary, dict) and "valid" in dq_summary,
                "dq_provenance_summary_present": isinstance(summary, dict),
                "dq_provenance_engine": summary.get("engine") if isinstance(summary, dict) else None,
                "dq_contract_ok": (
                    (not dq_required)
                    or (
                        _path_exists(output.get("dq_map_path"), run_root)
                        and isinstance(dq_summary, dict)
                        and "valid" in dq_summary
                        and isinstance(summary, dict)
                    )
                ),
            }
        )
    return rows


def _local_norm_rows(local_norm: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    enabled = bool(local_norm.get("enabled"))
    for item in local_norm.get("local_norm_results") or []:
        if not isinstance(item, dict):
            continue
        has_crop = "crop_box" in item
        dq_path = item.get("dq_mask_path")
        coefficient_path = item.get("coefficient_grid_path")
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "enabled": enabled,
                "status": item.get("status"),
                "crop_box_recorded": has_crop,
                "crop_box": item.get("crop_box") if has_crop else "missing",
                "normalized_path_exists": _path_exists(item.get("normalized_path"), run_root),
                "coverage_path_exists": _path_exists(item.get("coverage_path"), run_root),
                "dq_mask_path_exists": _path_exists(dq_path, run_root) if dq_path else not enabled,
                "dq_summary_present": isinstance(item.get("dq_summary"), dict),
                "coefficient_grid_exists": _path_exists(coefficient_path, run_root) if enabled else True,
                "model": item.get("coefficient_field_model") or item.get("model"),
                "contract_ok": (
                    has_crop
                    and _path_exists(item.get("normalized_path"), run_root)
                    and _path_exists(item.get("coverage_path"), run_root)
                    and (not enabled or bool(item.get("coefficient_field_model") or item.get("model")))
                    and (not enabled or _path_exists(coefficient_path, run_root))
                    and (not dq_path or _path_exists(dq_path, run_root))
                    and isinstance(item.get("dq_summary"), dict)
                ),
            }
        )
    return rows


def _warp_rows(warp: dict[str, Any], run_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in warp.get("warp_results") or []:
        if not isinstance(item, dict):
            continue
        dq_summary = item.get("dq_summary")
        rows.append(
            {
                "frame_id": item.get("frame_id"),
                "interpolation": item.get("interpolation"),
                "registered_path_exists": _path_exists(item.get("registered_path"), run_root),
                "coverage_path_exists": _path_exists(item.get("coverage_path"), run_root),
                "dq_mask_path_exists": _path_exists(item.get("dq_mask_path"), run_root),
                "dq_summary_present": isinstance(dq_summary, dict),
                "dq_summary_has_valid": isinstance(dq_summary, dict) and "valid" in dq_summary,
                "contract_ok": (
                    _path_exists(item.get("registered_path"), run_root)
                    and _path_exists(item.get("coverage_path"), run_root)
                    and _path_exists(item.get("dq_mask_path"), run_root)
                    and isinstance(dq_summary, dict)
                    and "valid" in dq_summary
                ),
            }
        )
    return rows


def _skipped_warp_rows(warp: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in warp.get("skipped_frames") or []:
        if isinstance(item, dict):
            rows.append(
                {
                    "frame_id": item.get("frame_id"),
                    "status": item.get("status"),
                    "has_reason": bool(item.get("reason")),
                    "contract_ok": bool(item.get("frame_id") and item.get("status") and item.get("reason")),
                }
            )
    return rows


def build_pipeline_contract_audit(run_dir: str | Path) -> dict[str, Any]:
    run_root = Path(run_dir)
    warp_path = run_root / "warp_results.json"
    local_norm_path = run_root / "local_norm_results.json"
    integration_path = run_root / "integration_results.json"
    warp = _load_json_object(warp_path)
    local_norm = _load_json_object(local_norm_path)
    integration = _load_json_object(integration_path)

    warp_rows = _warp_rows(warp, run_root)
    skipped_warp_rows = _skipped_warp_rows(warp)
    local_norm_rows = _local_norm_rows(local_norm, run_root)
    integration_rows = _integration_rows(integration, run_root)
    integration_map_rows = _integration_map_rows(integration, run_root)

    checks = [
        _check("integration_artifact_exists", integration_path.exists(), {"path": str(integration_path)}),
        _check(
            "integration_outputs_present",
            bool(integration_rows),
            {"actual": len(integration_rows), "required_min": 1},
        ),
        _check(
            "integration_output_maps_available",
            bool(integration_map_rows) and all(row["ok"] for row in integration_map_rows),
            {
                "map_count": len(integration_map_rows),
                "failed": [
                    f"{row['item']}:{row['map']}"
                    for row in integration_map_rows
                    if not row["ok"]
                ],
            },
        ),
        _check(
            "integration_dq_contract",
            bool(integration_rows) and all(row["dq_contract_ok"] for row in integration_rows),
            {
                "output_count": len(integration_rows),
                "failed": [row["item"] for row in integration_rows if not row["dq_contract_ok"]],
            },
        ),
    ]
    if warp_path.exists():
        checks.extend(
            [
                _check(
                    "warp_outputs_have_dq_and_coverage",
                    bool(warp_rows) and all(row["contract_ok"] for row in warp_rows),
                    {
                        "warp_output_count": len(warp_rows),
                        "failed": [row["frame_id"] for row in warp_rows if not row["contract_ok"]],
                    },
                ),
                _check(
                    "warp_skipped_frames_are_explained",
                    all(row["contract_ok"] for row in skipped_warp_rows),
                    {
                        "skipped_count": len(skipped_warp_rows),
                        "failed": [row["frame_id"] for row in skipped_warp_rows if not row["contract_ok"]],
                    },
                ),
            ]
        )
    if local_norm_path.exists():
        local_norm_contract_ok = (
            "crop_box" in local_norm
            if not local_norm.get("enabled") and not local_norm_rows
            else bool(local_norm_rows) and all(row["contract_ok"] for row in local_norm_rows)
        )
        checks.append(
            _check(
                "local_normalization_contract",
                local_norm_contract_ok,
                {
                    "enabled": bool(local_norm.get("enabled")),
                    "row_count": len(local_norm_rows),
                    "failed": [row["frame_id"] for row in local_norm_rows if not row["contract_ok"]],
                    "top_level_crop_box_recorded": "crop_box" in local_norm,
                },
                "LN rows must record crop_box and DQ state; enabled LN rows must record coefficient grids.",
            )
        )

    passed = all(check["passed"] for check in checks)
    return {
        "schema_version": 1,
        "audit_type": "pipeline_invariant_contract",
        "created_at": now_iso(),
        "run_dir": str(run_root),
        "status": "passed" if passed else "failed",
        "passed": passed,
        "checks": checks,
        "artifacts": {
            "warp": {"path": str(warp_path), "exists": warp_path.exists()},
            "local_norm": {"path": str(local_norm_path), "exists": local_norm_path.exists()},
            "integration": {"path": str(integration_path), "exists": integration_path.exists()},
        },
        "warp": {"outputs": warp_rows, "skipped_frames": skipped_warp_rows},
        "local_normalization": {
            "enabled": bool(local_norm.get("enabled")) if local_norm else None,
            "reference_frame_id": local_norm.get("reference_frame_id") if local_norm else None,
            "crop_box": local_norm.get("crop_box") if local_norm else None,
            "outputs": local_norm_rows,
        },
        "integration": {"outputs": integration_rows, "maps": integration_map_rows},
    }


def write_pipeline_contract_markdown(path: str | Path, audit: dict[str, Any]) -> None:
    lines = [
        "# GLASS Pipeline Invariant Contract Audit",
        "",
        f"- Status: {audit['status']}",
        f"- Run: `{audit['run_dir']}`",
        "",
        "## Checks",
        "",
    ]
    for item in audit.get("checks") or []:
        marker = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"- {marker}: `{item.get('name')}` - {item.get('evidence')}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pipeline_contract_audit(
    path: str | Path,
    audit: dict[str, Any],
    *,
    markdown: str | Path | None = None,
) -> None:
    write_json(path, audit)
    if markdown is not None:
        write_pipeline_contract_markdown(markdown, audit)
